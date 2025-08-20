import os
import json
import re
from tqdm import tqdm

SKIP_SECTION_NAMES = [
    "references", "bibliography", "acknowledgements", "thanks", "funding", "notes",
    "appendix", "supplementary", "supporting", "formula", "notation"
]

MIN_PARAGRAPH_LENGTH = 50  

def clean_text_v3(text):
    text = re.sub(r'@xmath\d+|@xcite|\$.*?\$|\\(cite|ref|label)\{[^}]*\}|~', '', text)
    text = re.sub(r'\(\s*[A-Z][a-zA-Z\-]+(?:\s+(et al\.|and\s+[A-Z][a-zA-Z\-]+))?,?\s*\d{4}\s*\)', '', text)
    text = re.sub(r'\bby\s+[A-Z][a-zA-Z\-]+(?:\s+et al\.)?', '', text)
    text = re.sub(r'\b[A-Z][a-zA-Z\-]+(?:\s+(et al\.|and\s+[A-Z][a-zA-Z\-]+))?\s*\(\s*\d{4}\s*\)', '', text)
    text = re.sub(r'\((i\.e\.|e\.g\.|see|cf\.|vs\.|respectively)[^)]*\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\s*\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(\s*\d{4}\s*\)', '', text)
    text = re.sub(r'\((Table|Tab\.?|Figure|Fig\.?)\s*\d+[a-zA-Z]?\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(Table|Tab\.?|Figure|Fig\.?)\s*\d+[a-zA-Z]?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\S+@\S+\.\S+\b|https?://\S+|www\.\S+', '', text)
    text = re.sub(r'\[\s*[\w\d, ]+\]', '', text)
    text = re.split(r'(?i)\b(copyright|©|funding|notes?)\b', text)[0]
    text = re.sub(r'\{\}|\[\]|\(\)', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def process_dataset(input_path, output_dir, start_index=1, num_examples=5):
    os.makedirs(output_dir, exist_ok=True)

    with open(input_path, encoding="utf-8") as f:
        lines = f.readlines()

    for i in tqdm(range(start_index - 1, min(start_index - 1 + num_examples, len(lines)))):
        entry = json.loads(lines[i])
        article_id = i + 1

        original_path = os.path.join(output_dir, f"{article_id}_original.txt")
        with open(original_path, "w", encoding="utf-8") as fout:
            fout.write("ABSTRACT\n")
            fout.write(clean_text_v3(entry["sc-abstract"].strip()) + "\n\n")
            for section_name, section_text in zip(entry["sc-section_names"], entry["sc-sections"]):
                if any(skip in section_name.lower() for skip in SKIP_SECTION_NAMES):
                    continue
                section_text = clean_text_v3(section_text.strip())
                if len(section_text) < MIN_PARAGRAPH_LENGTH:
                    continue
                fout.write(section_name.strip() + "\n")
                fout.write(section_text + "\n\n")

        ref_path = os.path.join(output_dir, f"{article_id}_ref.txt")
        with open(ref_path, "w", encoding="utf-8") as fref:
            fref.write(entry["pr-article"].strip())

    print(f"✅ Processed {num_examples} entries into '{output_dir}'")


if __name__ == "__main__":
    #process_dataset("valid_raw.json", "output_cleane_2000", start_index=1, num_examples=1000)
    process_dataset("valid_raw.json", "output_cleane_2000", start_index=201, num_examples=1800)
