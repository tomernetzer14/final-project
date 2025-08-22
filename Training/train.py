import torch
import json
import random
from transformers import T5Tokenizer, T5Config
from custom_model import CustomT5  
import wandb
from utils import build_importance_mask
from rouge_score import rouge_scorer
from tqdm import tqdm
DEBUG = False

# === Config ===
MODEL_NAME = "Falconsai/text_summarization"
DATA_PATH = "train_dataset_prepared.jsonl"
BEST_VAL_LOSS = float('inf')
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 2  
EPOCHS = 1
N_EXAMPLES = 3000
MAX_INPUT = 512
MAX_OUTPUT = 256


all_examples = []
with open(DATA_PATH, encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i >= N_EXAMPLES:
            break
        ex = json.loads(line)
        if DEBUG and i < 3:
            print(f"[DEBUG][LOAD] Example {i}: prompt={ex.get('prompt', '')[:50]}... target={ex.get('target_summary', '')[:50]}... keywords={ex.get('keywords', [])}")
        all_examples.append(ex)


random.shuffle(all_examples)
split = int(0.9 * len(all_examples))
train_examples = all_examples[:split]
val_examples = all_examples[split:]
print(f"Train: {len(train_examples)}, Val: {len(val_examples)}")

# ========== WANDB ==========
wandb.init(project="custom-t5-train", name="train_data_3000", config={"model": MODEL_NAME})


tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)
config = T5Config.from_pretrained(MODEL_NAME)
model = CustomT5(config)
pretrained_model = CustomT5.from_pretrained(MODEL_NAME)
model.load_state_dict(pretrained_model.state_dict(), strict=False)
model.to(DEVICE)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5)

save_dir = "trained_custom_t5"

def get_batches(examples, batch_size):
    for i in range(0, len(examples), batch_size):
        yield examples[i:i+batch_size]

def calc_rouge(preds, targets):
    scorer = rouge_scorer.RougeScorer(['rouge2', 'rougeL'], use_stemmer=True)
    scores2, scoresL = [], []
    for p, t in zip(preds, targets):
        res = scorer.score(t, p)
        scores2.append(res['rouge2'].fmeasure)
        scoresL.append(res['rougeL'].fmeasure)
    return sum(scores2)/len(scores2), sum(scoresL)/len(scoresL)

for epoch in range(EPOCHS):
    model.train()
    train_loss = 0
    train_batches = list(get_batches(train_examples, BATCH_SIZE))
    for b_idx, batch in enumerate(tqdm(train_batches, desc=f"Epoch {epoch+1} [Train]")):
        batch_inputs = [ex['prompt'] for ex in batch]
        batch_labels = [ex['target_summary'] for ex in batch]
        batch_keywords = [ex['keywords'] for ex in batch]

        if DEBUG and b_idx < 2:
            print(f"[DEBUG][BATCH {b_idx}] batch_inputs[0]: {batch_inputs[0][:100]}")
            print(f"[DEBUG][BATCH {b_idx}] batch_labels[0]: {batch_labels[0][:100]}")
            print(f"[DEBUG][BATCH {b_idx}] batch_keywords[0]: {batch_keywords[0]}")

        inputs = tokenizer(batch_inputs, return_tensors="pt", padding=True, truncation=True, max_length=MAX_INPUT)
        labels = tokenizer(batch_labels, return_tensors="pt", padding=True, truncation=True, max_length=MAX_OUTPUT)

        if DEBUG and b_idx < 2:
            print(f"[DEBUG][BATCH {b_idx}] input_ids[0]: {inputs['input_ids'][0][:30]}")
            print(f"[DEBUG][BATCH {b_idx}] labels[0]: {labels['input_ids'][0][:30]}")
            print(f"[DEBUG][BATCH {b_idx}] decoded input[0]: {tokenizer.decode(inputs['input_ids'][0])[:100]}")
            print(f"[DEBUG][BATCH {b_idx}] decoded label[0]: {tokenizer.decode(labels['input_ids'][0])[:100]}")

        imp_masks = []
        for idx in range(len(batch)):
            imp_mask = build_importance_mask(inputs['input_ids'][idx:idx+1], batch_keywords[idx], tokenizer)
            imp_masks.append(imp_mask)
        importance_mask = torch.cat(imp_masks, dim=0)
        if DEBUG and b_idx < 2:
            print(f"[DEBUG][BATCH {b_idx}] importance_mask[0][:30]: {importance_mask[0][:30]}")

        inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
        labels = {k: v.to(DEVICE) for k, v in labels.items()}
        importance_mask = importance_mask.to(DEVICE)

        optimizer.zero_grad()
        outputs = model(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            labels=labels["input_ids"],
            importance_mask=importance_mask
        )
        if DEBUG and b_idx < 2:
            print(f"[DEBUG][BATCH {b_idx}] Loss: {outputs.loss.item()}")
        loss = outputs.loss
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        train_loss += loss.item()
        
        if (b_idx + 1) % 100 == 0:
            avg_loss = train_loss / (b_idx + 1)
            print(f"[Epoch {epoch+1} | Batch {b_idx+1}] Avg train loss: {avg_loss:.4f}")
            wandb.log({
                "batch": b_idx+1,
                "epoch": epoch+1,
                "train/batch_loss": loss.item(),
                "train/avg_loss": avg_loss
            })
    avg_train_loss = train_loss / (len(train_examples)//BATCH_SIZE+1)

    # ----------- VALIDATION -----------
    model.eval()
    val_loss = 0
    val_preds = []
    val_targets = []
    val_batches = list(get_batches(val_examples, BATCH_SIZE))

    with torch.no_grad():
        for b_idx, batch in enumerate(tqdm(val_batches, desc=f"Epoch {epoch+1} [Val]")):
            batch_inputs = [ex['prompt'] for ex in batch]
            batch_labels = [ex['target_summary'] for ex in batch]
            batch_keywords = [ex['keywords'] for ex in batch]
            inputs = tokenizer(batch_inputs, return_tensors="pt", padding=True, truncation=True, max_length=MAX_INPUT)
            labels = tokenizer(batch_labels, return_tensors="pt", padding=True, truncation=True, max_length=MAX_OUTPUT)
            imp_masks = []
            for idx in range(len(batch)):
                imp_mask = build_importance_mask(inputs['input_ids'][idx:idx+1], batch_keywords[idx], tokenizer)
                imp_masks.append(imp_mask)
            importance_mask = torch.cat(imp_masks, dim=0)
            if DEBUG and b_idx < 2:
                print(f"[DEBUG][VAL {b_idx}] batch_inputs[0]: {batch_inputs[0][:100]}")
                print(f"[DEBUG][VAL {b_idx}] batch_labels[0]: {batch_labels[0][:100]}")
                print(f"[DEBUG][VAL {b_idx}] input_ids[0]: {inputs['input_ids'][0][:30]}")
                print(f"[DEBUG][VAL {b_idx}] labels[0]: {labels['input_ids'][0][:30]}")
                print(f"[DEBUG][VAL {b_idx}] importance_mask[0][:30]: {importance_mask[0][:30]}")
            inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
            labels = {k: v.to(DEVICE) for k, v in labels.items()}
            importance_mask = importance_mask.to(DEVICE)

            outputs = model(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                labels=labels["input_ids"],
                importance_mask=importance_mask
            )
            if DEBUG and b_idx < 2:
                print(f"[DEBUG][VAL {b_idx}] Loss: {outputs.loss.item()}")
            batch_loss = outputs.loss.item()
            val_loss += outputs.loss.item()
            
            if (b_idx + 1) % 20 == 0:
                avg_val_loss = val_loss / (b_idx + 1)
                print(f"[Epoch {epoch+1} | Val Batch {b_idx+1}] Avg val loss: {avg_val_loss:.4f}")
                wandb.log({
                    "val/batch": b_idx+1,
                    "epoch": epoch+1,
                    "val/batch_loss": batch_loss,
                    "val/avg_loss": avg_val_loss
                })
            
            out_ids = model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                importance_mask=importance_mask,
                max_length=MAX_OUTPUT,
                min_length=5,
                num_beams=2
            )
            for idx in range(len(out_ids)):
                pred = tokenizer.decode(out_ids[idx], skip_special_tokens=True)
                gold = batch_labels[idx]
                if DEBUG and b_idx < 2 and idx < 2:
                    print(f"[DEBUG][VAL {b_idx}] Pred: {pred[:100]}")
                    print(f"[DEBUG][VAL {b_idx}] Gold: {gold[:100]}")
                val_preds.append(pred)
                val_targets.append(gold)

    avg_val_loss = val_loss / (len(val_examples)//BATCH_SIZE+1)
    rouge2, rougel = calc_rouge(val_preds, val_targets)

    print(f"Epoch {epoch+1}: train_loss={avg_train_loss:.4f} | val_loss={avg_val_loss:.4f} | rouge2={rouge2:.4f} | rougel={rougel:.4f}")
    wandb.log({
        "epoch": epoch+1,
        "train/loss": avg_train_loss,
        "val/loss": avg_val_loss,
        "val/rouge2": rouge2,
        "val/rougel": rougel
    })

    if avg_val_loss < BEST_VAL_LOSS:
        print("Best model so far, saving...")
        model.save_pretrained(save_dir)
        tokenizer.save_pretrained(save_dir)
        BEST_VAL_LOSS = avg_val_loss

wandb.finish()
print(f"Model and tokenizer saved to {save_dir}")
