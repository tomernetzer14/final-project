import re
from keybert import KeyBERT
from transformers import T5Tokenizer
import torch

# === INITIALIZE ONCE ===
kw_model = KeyBERT()
tokenizer = T5Tokenizer.from_pretrained("Falconsai/text_summarization")

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

def split_sections(text):
    """
    Split article into sections by common scientific headers (titles, all-caps, or short lines).
    Returns: dict {section_title: section_text}
    """
    lines = text.splitlines()
    section_positions = {}
    current_pos = 0

    for line in lines:
        line_clean = line.strip()
 
        if (len(line_clean.split()) <= 5 and 
            (re.match(r'^([0-9]+(\.[0-9]+)?\s)?[A-Za-z ]+$', line_clean) or line_clean.isupper())):
            section_positions[line_clean] = current_pos
        current_pos += len(line) + 1

    if not section_positions:
        return {"Full Text": text}

    sorted_sections = sorted(section_positions.items(), key=lambda x: x[1])
    sections = {}
    for i, (section, start_idx) in enumerate(sorted_sections):
        end_idx = sorted_sections[i + 1][1] if i + 1 < len(sorted_sections) else len(text)
        content = text[start_idx:end_idx].strip()
        lines_in_section = content.splitlines()
        content = "\n".join(lines_in_section[1:]).strip() 
        sections[section] = content

    return sections

def extract_keywords(text, n=10):
    """
    Extract top-N keywords/phrases using KeyBERT.
    Returns: list of keywords
    """
    keywords = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 2),
        stop_words='english',
        use_mmr=True,
        diversity=0.7,
        #top_n=n
    )
    return [kw[0] for kw in keywords]

def split_into_chunks(text, chunk_size=512, overlap=50):
    """
    Split text into overlapping chunks for the model input (by token length).
    Returns: list of chunks (strings)
    """
    tokens = tokenizer.encode(text, truncation=False)
    chunks = []
    for i in range(0, len(tokens), chunk_size - overlap):
        chunk = tokens[i:i + chunk_size]
        chunks.append(tokenizer.decode(chunk))
    return chunks

def build_importance_mask(input_ids, keywords, tokenizer):
    """
    Build importance mask for specific input_ids (after tokenization, padding, truncation).
    5.0 for any token matching a keyword (phrase split to words), else 0.0.
    input_ids: torch.Tensor of shape [batch, seq]
    keywords: list of strings
    tokenizer: the tokenizer used
    Returns: torch.Tensor [batch, seq]
    """
    flat_keywords = set(word.lower() for phrase in keywords for word in phrase.split())
    masks = []
    for sequence in input_ids:
        tokens = tokenizer.convert_ids_to_tokens(sequence)
        mask = []
        for tok in tokens:
            tok_clean = tok.lower().replace('▁', '').strip()
            is_important = tok_clean in flat_keywords
            mask.append(2.6 if is_important else 0.0)
        masks.append(mask)
    return torch.tensor(masks, dtype=torch.float32)


def build_prompt(section_text, keywords):
    """
    Build the model's input prompt in the same way for training and inference.
    """
    keyword_str = ", ".join(keywords)
    prompt = f"Simplify and summarize: {section_text}\nFocus on: {keyword_str}"
    return prompt


def postprocess_summary(text):
    text = re.sub(r'\s+', ' ', text)

    text = re.sub(r'\. (?=[A-Z])', '.\n\n', text)

    text = re.sub(r',(?=[^\s])', ', ', text)

    text = re.sub(r'[^\x00-\x7F\u0590-\u05FF]+', '', text) 

    text = re.sub(r' +', ' ', text)

    return text.strip()