import json
from tqdm import tqdm
from utils import clean_text, extract_keywords, build_importance_mask, build_prompt
from transformers import T5Tokenizer

INPUT_PATH = "train_dataset_arx_full.json"#"val_dataset_arx_full.json"
OUTPUT_PATH = "train_dataset_prepared.jsonl"

tokenizer = T5Tokenizer.from_pretrained("Falconsai/text_summarization")

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    raw_dataset = json.load(f)

new_records = []
for record in tqdm(raw_dataset):
    clean_section = clean_text(record["input_text"])
    
    keywords = extract_keywords(clean_section)
    
    encoding = tokenizer(
        clean_section, max_length=1024, truncation=True, padding="max_length", return_tensors="pt"
    )
    input_ids = encoding["input_ids"][0].tolist()
    
    # importance mask
    importance_mask =[]# build_importance_mask(input_ids, keywords)
    
    # בניית פרומפט אחיד
    prompt = build_prompt(clean_section, keywords)
    
    new_rec = {
        "id": record["id"],
        "article_id": record["article_id"],
        "section_name": record["section_name"],
        "input_text": clean_section,
        "keywords": keywords,
        "importance_mask": importance_mask,
        "prompt": prompt,
        "target_summary": record["target_summary"],
    }
    new_records.append(new_rec)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for rec in new_records:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"✅ Done! Saved {len(new_records)} records to {OUTPUT_PATH}")
