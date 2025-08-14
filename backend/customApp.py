from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import torch
from transformers import T5ForConditionalGeneration
from transformers import T5Tokenizer
from custom_model import CustomT5
from bert_score import score
import logging
logging.basicConfig(level=logging.INFO)

from metrics_new import (
    load_frequency_data,
    load_common_words,
    calculate_complexity,
    calculate_readability,
    calculate_word_freq_score,
    calculate_embedding_similarity
)

from utils import (
    clean_text as preprocess_text,
    split_sections,
    extract_keywords,
    split_into_chunks,
    build_importance_mask,
    build_prompt as prepare_prompt,
    postprocess_summary

)

# === Init App === #
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# === Load Resources === #
common_words_file = "google-10000-english.txt"
freq_file = "words_219k.txt"
common_words = [line.strip() for line in open(common_words_file, encoding="utf-8")]
frequency_data = load_frequency_data(freq_file)

# === Load Model === #
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[⚙️ Device] Using device: {device}")

MODEL_PATH = "./MODEL/t5-custom"  
tokenizer = T5Tokenizer.from_pretrained(MODEL_PATH)
model = CustomT5.from_pretrained(MODEL_PATH).to(device).eval()

# === Load baseline model === #
default_tokenizer = T5Tokenizer.from_pretrained("t5-small")
default_model = T5ForConditionalGeneration.from_pretrained("t5-small").to(device).eval()

# === Simplification with custom model === #
def simplify_text(text):
    raw_text = text
    trace = {}
    sections_raw = split_sections(raw_text)
    trace["sections"] = (
        f"The text was identified as containing {len(sections_raw)} sections."
        if len(sections_raw) > 1
        else "The text was not split into sections."
    )

    sections = {name: preprocess_text(text) for name, text in sections_raw.items()}
    trace["cleaned"] = "Text cleaning was applied to the text."


    keywords_dict = {}
    for section_name, section_text in sections.items():
        keywords = extract_keywords(section_text)
        keywords_dict[section_name] = keywords
    trace["keywords"] = keywords_dict

    full_output = []
    debug_lines = []
    chunks_counter = 0
    for section_name, section_text in sections.items():
        print(f"\n[📌 SECTION: {section_name}]")
        logging.info(f"\n[📌 SECTION: {section_name}]")

        full_output.append(f"[SECTION: {section_name}]\n")
        debug_lines.append(f"\n================ SECTION: {section_name} ================\n")

        chunks = split_into_chunks(section_text)
        chunks_counter = chunks_counter+len(chunks)
        for i, chunk in enumerate(chunks):
            print(f"\n--- [🔹 Chunk {i + 1}/{len(chunks)}] ---")
            logging.info(f"\n--- [🔹 Chunk {i + 1}/{len(chunks)}] ---")

            keywords = extract_keywords(chunk)
            prompt = prepare_prompt(chunk, keywords)

            inputs = tokenizer(
                prompt,
                return_tensors="pt",
                padding="max_length",
                truncation=True,
                max_length=512
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}
            importance_mask = build_importance_mask(inputs["input_ids"], keywords, tokenizer).to(device)
            debug_lines.append(f"\n--- Chunk {i + 1}/{len(chunks)} ---\n")
            debug_lines.append("[🔤 Prompt]:\n" + prompt + "\n")
            debug_lines.append("[🔑 Keywords]: " + ", ".join(keywords) + "\n")
            debug_lines.append("[📟 input_ids (first 20)]:\n" + str(inputs["input_ids"][0][:20].tolist()) + "\n")
            debug_lines.append("[🟩 Importance mask (first 20)]:\n" + str(importance_mask[0][:20].tolist()) + "\n")

            with torch.no_grad():
                output_ids = model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    max_length=256,
                    min_length=5,
                )
                output_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
                print("[🟡 Output (no importance_mask)]:", output_text)
                debug_lines.append("[🟡 Output (no importance_mask)]:\n" + output_text + "\n")

                output_ids_masked = model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    importance_mask=importance_mask,
                    max_length=256,
                    min_length=5,
                )
                output_text_masked = tokenizer.decode(output_ids_masked[0], skip_special_tokens=True)
                print("[🟢 Output (with importance_mask)]:", output_text_masked)

                debug_lines.append("[🟢 Output (with importance_mask)]:\n" + output_text_masked + "\n")

                if output_text_masked.strip():
                    full_output.append(output_text_masked.strip() + "\n\n")
                    logging.info("[🟢 Output (with importance_mask)]")
                elif output_text.strip():
                    full_output.append(output_text.strip() + "\n")
                    logging.info("[🟡 Output (no importance_mask)]")


        trace["chunks"] = f"The text was split into {chunks_counter} chunks."

    return " ".join(full_output), keywords_dict, trace , "\n".join(full_output)


# === Simplification with baseline === #
def simplify_with_base_model(text):
    text_clean = preprocess_text(text)
    chunks = split_into_chunks(text_clean)
    summaries = []

    for chunk in chunks:
        inputs = default_tokenizer(chunk, return_tensors="pt", truncation=True, padding="max_length", max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            output = default_model.generate(
                input_ids=inputs["input_ids"],
                max_length=256,
                do_sample=True,
                top_k=50,
                top_p=0.9,
                temperature=0.8,
                repetition_penalty=2.0,
                no_repeat_ngram_size=3,
                num_return_sequences=1
            )
            summary = default_tokenizer.decode(output[0], skip_special_tokens=True)
            summaries.append(summary)

    full_summary = " ".join(summaries)
    return postprocess_summary(full_summary)


# === Route === #
@app.route("/simplify", methods=["POST"])
def simplify():
    data = request.json
    if "text" not in data:
        return jsonify({"error": "Missing 'text' in request"}), 400

    original_text = data["text"]
    simplified, keywords, trace , full_out  = simplify_text(original_text)
    baseline = simplify_with_base_model(original_text)

    _, _, bert_f1 = score([full_out], [baseline], lang="en", verbose=False)
    bert_score = bert_f1[0].item() * 100

    complexity_model = calculate_complexity(full_out)
    readability_model = calculate_readability(full_out, common_words)
    wordfreq_model = calculate_word_freq_score(full_out, frequency_data) * 100
    bertsim = calculate_embedding_similarity(full_out , baseline)
    return jsonify({
        "original": original_text,
        "simplified": simplified,
        "baseline": baseline,
        "keywords": keywords,
        "trace": trace,
        "metrics": {
            "readability": readability_model,
            "complexity": complexity_model,
            "frequencyScore": wordfreq_model,
            "bert": bert_score,
            "berts": bertsim
        }
    })


@app.route('/extract-pdf', methods=['POST'])
def extract_pdf():
    try:
        if 'input' not in request.files:
            return jsonify({'error': "Missing 'input' file"}), 400

        pdf_file = request.files['input']
        files = {
            'input': (pdf_file.filename, pdf_file.stream, pdf_file.mimetype)
        }

        grobid_response = requests.post(
            'http://grobid:8070/api/processFulltextDocument',
            files=files
        )

        if grobid_response.status_code != 200:
            print("[❌ GROBID ERROR]", grobid_response.status_code, grobid_response.text)
            return jsonify({'error': 'GROBID failed', 'details': grobid_response.text}), 500

        return grobid_response.text, 200, {'Content-Type': 'application/xml'}

    except Exception as e:
        import traceback
        print("[ EXCEPTION OCCURRED ]")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# === Run App === #
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, use_reloader=False)