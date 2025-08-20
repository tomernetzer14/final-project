import torch
import torch.nn as nn
from transformers import T5ForConditionalGeneration
from transformers.models.t5.modeling_t5 import T5Attention,T5Block, T5LayerNorm, T5DenseActDense, T5Stack,T5Config
import torch.nn.functional as F

DEBUG = -2


# === 1. Custom Attention that supports importance_mask ===
class CustomT5Attention(T5Attention):
    def __init__(self, config, has_relative_attention_bias=False, is_bidirectional=False):
        super().__init__(config, has_relative_attention_bias, is_bidirectional)


    def forward(
        self,
        input,
        mask=None,
        kv=None,
        position_bias=None,
        past_key_value=None,
        head_mask=None,
        layer_head_mask=None,    
        query_length=None,
        use_cache=False,
        output_attentions=False,
        **kwargs               
    ):
        bs, qlen, dim = input.size()

        if past_key_value is not None:
            assert self.is_decoder is True, "Encoder cannot cache past key value states"
            assert (
                len(past_key_value) == 2
            ), "past_key_value should have 2 past states: keys and values. Got {} past states".format(
                len(past_key_value)
            )
            real_qlen = qlen + past_key_value[0].shape[2] if query_length is None else query_length
        else:
            real_qlen = qlen

        if kv is None:
            klen = real_qlen
        else:
            klen = kv.size(1)

        def shape(x):
            return x.view(bs, -1, self.n_heads, self.key_value_proj_dim).transpose(1, 2)

        def unshape(x):
            return x.transpose(1, 2).contiguous().view(bs, -1, self.inner_dim)

        q = shape(self.q(input))  # (bs, n_heads, qlen, dim_per_head)

        if kv is None:
            k = shape(self.k(input))  # (bs, n_heads, qlen, dim_per_head)
            v = shape(self.v(input))  # (bs, n_heads, qlen, dim_per_head)
        elif past_key_value is None:
            k = v = kv
            k = shape(self.k(k))  # (bs, n_heads, qlen, dim_per_head)
            v = shape(self.v(v))  # (bs, n_heads, qlen, dim_per_head)

        if past_key_value is not None:
            if kv is None:
                k_, v_ = past_key_value
                k = torch.cat([k_, k], dim=2)  # (bs, n_heads, klen, dim_per_head)
                v = torch.cat([v_, v], dim=2)  # (bs, n_heads, klen, dim_per_head)
            else:
                k, v = past_key_value

        if self.is_decoder and use_cache is True:
            present_key_value_state = ((k, v),)
        else:
            present_key_value_state = (None,)

        # (bs, n_heads, qlen, klen)
        scores = torch.matmul(
            q, k.transpose(3, 2)
        )

        if position_bias is None:
            if not self.has_relative_attention_bias:
                raise ValueError("No position_bias provided and no weights to compute position_bias")
            position_bias = self.compute_bias(real_qlen, klen)

            if past_key_value is not None:
                position_bias = position_bias[:, :, -qlen:, :]

            if mask is not None:
                position_bias = position_bias + mask  # (bs, n_heads, qlen, klen)

        
        importance_mask = getattr(self, "importance_mask", None)
        if importance_mask is not None and not self.is_decoder:
            if DEBUG > 0:
                print(f"[CustomT5Attention] Adding importance_mask: {importance_mask.shape}")
            if importance_mask.ndim == 2:
                bias = importance_mask.unsqueeze(1).unsqueeze(2)  # [bs,1,1,klen]
                if bias.size(-1) == scores.size(-1):
                    scores = scores + bias
                    if DEBUG > 0:
                        print(f"[CustomT5Attention] importance_mask injected as bias: {bias.shape}")
                else:
                    if DEBUG > 0:
                        print(f"[CustomT5Attention] importance_mask shape mismatch! bias={bias.shape}, scores={scores.shape}")
            else:
                if DEBUG > 0:
                    print(f"[CustomT5Attention] importance_mask must be [bs, seq_len], got {importance_mask.shape}")

        scores += position_bias

        weights = F.softmax(scores.float(), dim=-1).type_as(scores)  # (bs, n_heads, qlen, klen)
        weights = F.dropout(weights, p=self.dropout, training=self.training)  # (bs, n_heads, qlen, klen)

        if head_mask is not None:
            weights = weights * head_mask

        context = torch.matmul(weights, v)  # (bs, n_heads, qlen, dim_per_head)
        context = unshape(context)  # (bs, qlen, dim)

        context = self.o(context)

        outputs = (context,) + present_key_value_state + (position_bias,)
        if output_attentions:
            outputs = outputs + (weights,)
        return outputs


# === 2. Patch the original T5Block to override only the SelfAttention ===
class PatchedT5Block(T5Block):
    def __init__(self, config, has_relative_attention_bias=False):
        super().__init__(config, has_relative_attention_bias)
        self.layer[0].SelfAttention = CustomT5Attention(
            config,
            has_relative_attention_bias=has_relative_attention_bias,
            is_bidirectional=False,
        )

    def forward(self, hidden_states, attention_mask=None, position_bias=None, **kwargs):
        if DEBUG > 0:
            print(f"[📦 PatchedT5Block] Forward called on block")

        

        return super().forward(
            hidden_states,
            attention_mask=attention_mask,
            position_bias=position_bias,
            **kwargs
        )



# === 3. Patch only the encoder stack to use our custom blocks ===
class CustomT5Stack(T5Stack):
    def __init__(self, config, embed_tokens):
        super().__init__(config, embed_tokens)

        new_blocks = []
        for i, block in enumerate(self.block):
            orig_has_relative_attention_bias = getattr(block.layer[0].SelfAttention, "has_relative_attention_bias", False)
            patched_block = PatchedT5Block(config, has_relative_attention_bias=orig_has_relative_attention_bias)
            patched_block.load_state_dict(block.state_dict())
            new_blocks.append(patched_block)
        self.block = nn.ModuleList(new_blocks)
        self._importance_mask = None
        if DEBUG > 0:
            print("[✅ CustomT5Stack] Initialized")

    def forward(self, input_ids=None, attention_mask=None, importance_mask=None, **kwargs):

        if importance_mask is None:
            importance_mask = getattr(self, "_importance_mask", None)
            if DEBUG > 0:
                print("[🧱 CustomT5Stack] Pulled importance_mask from self._importance_mask" if importance_mask is not None else "[🧱 CustomT5Stack] No importance_mask provided or stored")
        else:
            self._importance_mask = importance_mask
            if DEBUG > 0:
                print(f"[🧱 CustomT5Stack] Received importance_mask in forward, shape: {importance_mask.shape}")


        for i, block in enumerate(self.block):
            attention = block.layer[0].SelfAttention
            if isinstance(attention, CustomT5Attention):
                attention.importance_mask = importance_mask
                #block.importance_mask = importance_mask

                if DEBUG > 1:
                    print(f"[🔗 CustomT5Stack] Set importance_mask for block {i}")
            else:
                if DEBUG > 0:
                    print(f"[⚠️ CustomT5Stack] block {i} is not CustomT5Attention (type={type(attention)})")
        
        kwargs["use_cache"] = False


        return super().forward(
            input_ids=input_ids,
            attention_mask=attention_mask,
            **kwargs
        )



# === 4. Final CustomT5 Model ===
class CustomT5(T5ForConditionalGeneration):
    def __init__(self, config: T5Config):
        super().__init__(config)

        # ✅ Replace encoder with our custom version that uses PatchedT5Block
        self.encoder = CustomT5Stack(config, self.shared)
        if DEBUG > 0:
            print("[✅ CustomT5] Initialized with Custom Encoder Stack")
    
    def prepare_inputs_for_generation(
        self, input_ids, past=None, attention_mask=None, use_cache=None, encoder_outputs=None, **kwargs
    ):
        importance_mask = kwargs.get("importance_mask", None)

        # cut decoder_input_ids if past is used
        if past is not None:
            input_ids = input_ids[:, -1:]
            
            
        if DEBUG > 0:
            print("[🛠️ prepare_inputs_for_generation] called from generate()")
            if importance_mask is not None:
                print(f"[🛠️ prepare_inputs_for_generation] Got importance_mask with shape {importance_mask.shape}")
            else:
                print("[🛠️ prepare_inputs_for_generation] No importance_mask received")
                
        if importance_mask is not None:
            self.encoder._importance_mask = importance_mask
            if DEBUG > 0:
                print("[🛠️ prepare_inputs_for_generation] Stored importance_mask on encoder")

        return {
            "decoder_input_ids": input_ids,
            "past_key_values": past,
            "encoder_outputs": encoder_outputs,
            "attention_mask": attention_mask,
            "use_cache": use_cache,
            "importance_mask": importance_mask, 

        }    
   
    
    def forward(self, input_ids=None, attention_mask=None, importance_mask=None, **kwargs):
        if DEBUG > 0:
            print("🧾 CustomT5.forward() called")
            if importance_mask is not None:
                print(f"[🧾 forward] importance_mask shape: {importance_mask.shape}")
            else:
                print("[🧾 forward] importance_mask is None")

        if importance_mask is None:
            importance_mask = getattr(self.encoder, "_importance_mask", None)
            if DEBUG > 0:
                print("[🧾 forward] Pulled importance_mask from encoder._importance_mask" if importance_mask is not None else "[🧾 forward] No importance_mask on encoder")
        else:
            self.encoder._importance_mask = importance_mask  
            if DEBUG > 0:
                print("[🧾 forward] Stored importance_mask on encoder")

        return super().forward(
            input_ids=input_ids,
            attention_mask=attention_mask,
         
            **kwargs
        )

