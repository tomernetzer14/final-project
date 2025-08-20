import os
import json
import re
from tqdm import tqdm
from transformers import pipeline
import subprocess

DEVICE = 0 
summarizer = pipeline("summarization", model="facebook/bart-large-cnn", tokenizer="facebook/bart-large-cnn", device=DEVICE)

def clean_scientific_text(text):
    text = re.sub(r'@xmath\d+|@xcite|\$.*?\$', '', text)
    text = re.sub(r'\\(cite|ref|label)\{[^}]*\}', '', text)
    text = re.sub(r'~|\\\[.*?\\\]|\{\}|\[\s*[fF]?\d+(,\s*[fF]?\d+)*\s*\]', '', text)
    text = re.sub(r'(figure|fig\.?|see)\s*\S+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\( ?see(,)? ?figures? [^)]+\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+\.', '.', text)
    text = re.sub(r'\s+,', ',', text)
    return text.strip()
def clean_text(text):
    """
    Clean scientific text thoroughly.
    """
    # Remove LaTeX-style markers
    text = re.sub(r'@xmath\d+', '', text)
    text = re.sub(r'@xcite', '', text)
    text = re.sub(r'\$.*?\$', '', text)
    text = re.sub(r'\\(cite|ref|label)\{[^}]*\}', '', text)
    text = re.sub(r'~', ' ', text)

    # Remove (Author et al., 2019) and similar
    text = re.sub(r'\(\s*[A-Z][a-zA-Z\-]+(?:\s+(et al\.|and\s+[A-Z][a-zA-Z\-]+))?,?\s*\d{4}\s*\)', '', text)

    # Remove by Author et al.
    text = re.sub(r'\bby\s+[A-Z][a-zA-Z\-]+(?:\s+et al\.)?', '', text)

    # Remove Author et al. (2019) and variations
    text = re.sub(r'\b[A-Z][a-zA-Z\-]+(?:\s+(et al\.|and\s+[A-Z][a-zA-Z\-]+))?\s*\(\s*\d{4}\s*\)', '', text)

    # Remove (i.e., ...), (e.g., ...), etc.
    text = re.sub(r'\((i\.e\.|e\.g\.|see|cf\.|vs\.|respectively)[^)]*\)', '', text, flags=re.IGNORECASE)

    # Remove parenthesized dates and content (e.g., (April 2022), (2020))
    text = re.sub(r'\(\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\s*\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(\s*\d{4}\s*\)', '', text)

    # Remove figure/table mentions like (Table 3), (Fig. 2)
    text = re.sub(r'\((Table|Tab\.?|Figure|Fig\.?)\s*\d+[a-zA-Z]?\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(Table|Tab\.?|Figure|Fig\.?)\s*\d+[a-zA-Z]?', '', text, flags=re.IGNORECASE)

    # Remove emails and URLs
    text = re.sub(r'\b\S+@\S+\.\S+\b', '', text)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)

    # Remove citations like [12], [f7], [1, 2, 3]
    text = re.sub(r'\[\s*[\w\d, ]+\]', '', text)

    # Remove copyright and everything after
    text = re.split(r'(?i)\b(copyright|©)\b', text)[0]

    # Remove funding and notes sections
    text = re.split(r'(?i)\b(funding|notes?)\b', text)[0]

    # Remove empty brackets and normalize spaces
    text = re.sub(r'\{\}|\[\]|\(\)', '', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()
def normalize_section_name(name):
    name = re.sub(r'[^A-Za-z ]', '', name)
    return name.strip().upper()

def is_english(text):
    letters = re.sub(r'[^A-Za-z]', '', text)
    return len(letters) > 0 and len(letters) / max(1, len(text.replace(' ', ''))) > 0.7

def generate_dataset(input_path, output_dir, max_examples=None):
    os.makedirs(output_dir, exist_ok=True)

    with open(input_path, encoding="utf8") as f:
        lines = f.readlines()

    count = 0

    for line in tqdm(lines, desc="Processing articles"):
        try:
            article = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"❌ Skipping bad JSON line: {e}")
            continue

        article_id = article.get("article_id")
        section_names = article.get("section_names", [])
        sections = article.get("sections", [])

        if len(section_names) != len(sections):
            print(f"⚠️ Skipping article {article_id} due to section mismatch")
            continue

        original_lines = []
        ref_lines = []

        for section_name, section_sents in zip(section_names, sections):
            norm_section = normalize_section_name(section_name)
            section_text = clean_text(" ".join(section_sents).strip())

            if not is_english(norm_section + section_text) or len(section_text) < 20:
                continue

            try:
                summary = summarizer(section_text[:3000], max_length=512, min_length=50, do_sample=False)[0]['summary_text']
            except Exception as e:
                print(f"[!] Failed to summarize: {e}")
                continue

            original_lines.append(f"{norm_section}\n{section_text.strip()}\n")
            ref_lines.append(f"{norm_section}\n{summary.strip()}\n")

        if original_lines and ref_lines:
            base_path = os.path.join(output_dir, f"{count + 1}")
            original_txt = base_path + "_original.txt"

            with open(base_path + "_original.txt", "w", encoding="utf8") as f_orig:
                f_orig.write("\n".join(original_lines))
            #with open(base_path + ".txt", "w", encoding="utf8") as f_txt:
            #    f_txt.write("\n".join(original_lines))
            with open(base_path + "_ref.txt", "w", encoding="utf8") as f_ref:
                f_ref.write("\n".join(ref_lines))
            
            
            
            try:
                print(f"🔁 Running inference on {original_txt}")
                subprocess.run(["python", "inference.py", original_txt], check=True)
            except subprocess.CalledProcessError as e:
                print(f"❌ Inference failed on {original_txt}: {e}")
                
                
            count += 1
        if max_examples and count >= max_examples:
            break

    print(f"\n✅ Saved {count} examples into {output_dir}")


generate_dataset("test.txt", "output_samples", max_examples=50)
