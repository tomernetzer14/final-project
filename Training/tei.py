from lxml import etree
from utils import clean_text

import re

def clean_text_v2(text):
    """
    Clean scientific text thoroughly:
    - Remove arXiv/LaTeX markers
    - Remove citations in formats like:
      (Author et al., 2019), Author et al. (2019), by Author et al. (2019)
    - Remove clarifying parentheses (i.e., ...), (e.g., ...)
    - Remove copyright and everything after
    - Remove links and emails
    - Remove bracketed citations like [13], [f7]
    - Remove notes/funding and what follows
    - Remove figures mentions
    - Normalize whitespace
    """

    # Remove LaTeX-style markers
    text = re.sub(r'@xmath\d+', '', text)
    text = re.sub(r'@xcite', '', text)
    text = re.sub(r'\$.*?\$', '', text)
    text = re.sub(r'\\(cite|ref|label)\{[^}]*\}', '', text)
    text = re.sub(r'~', ' ', text)

    # Remove (Author et al., 2019) or (Author, 2019)
    text = re.sub(r'\(([A-Z][a-zA-Z]+(?: et al\.)?(?:,)? \d{4})\)', '', text)

    # Remove i.e., e.g., see ... inside parentheses
    text = re.sub(r'\((i\.e\.|e\.g\.|see|cf\.|vs\.|respectively)[^)]*\)', '', text, flags=re.IGNORECASE)

    # Remove parenthesized dates (April 2022), (2020)
    text = re.sub(r'\(\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\s*\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(\s*\d{4}\s*\)', '', text)

    # Remove Author et al. (2020), by Author et al. (2020)
    text = re.sub(r'\bby\s+[A-Z][a-zA-Z]+(?: et al\.)?\s*\(\d{4}\)', '', text)
    text = re.sub(r'\b[A-Z][a-zA-Z]+(?: et al\.)?\s*\(\d{4}\)', '', text)
    text = re.sub(r'\b[A-Z][a-zA-Z]+(?: and [A-Z][a-zA-Z]+)?\s*\(\d{4}\)', '', text)

    # Remove URLs and emails
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'\b\S+@\S+\.\S+\b', '', text)

    # Remove [13], [f7], [5,13]
    text = re.sub(r'\[\s*[\w\d, ]+\]', '', text)

    # Remove figure mentions
    text = re.sub(r'(see,?\s+)?figures?(\s*\w+(\-\w+)?(,?|\s*-\s*\w+)*)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'figure\s*\[[^\]]*\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'figure\s+\w+', '', text, flags=re.IGNORECASE)

    # Remove copyright and everything after
    text = re.split(r'(?i)\b(copyright|©)\b', text)[0]

    # Remove 'Funding', 'Notes', etc., and anything after them
    text = re.split(r'(?i)\b(funding|notes?)\b', text)[0]

    # Remove empty brackets and excessive whitespace
    text = re.sub(r'\{\}', '', text)
    text = re.sub(r'\[\]', '', text)
    text = re.sub(r'\(\)', '', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def clean_text_v3(text):
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



def extract_text_from_tei(tei_path, output_txt_path="output.txt"):
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}

    tree = etree.parse(tei_path)
    root = tree.getroot()

    body = root.find('.//tei:body', namespaces=ns)
    if body is None:
        raise ValueError("No <body> found in TEI")

    cleaned_sections = []

    for div in body.findall(".//tei:div", namespaces=ns):
        div_type = div.attrib.get('type', '').lower()
        if div_type in ('references', 'bibliography', 'figure', 'table'):
            continue

        head = div.find('tei:head', namespaces=ns)
        title = head.text.strip() if head is not None and head.text else None

        paragraphs = []
        for p in div.findall('tei:p', namespaces=ns):
            raw_text = ''.join(p.itertext()).strip()
            cleaned_text = clean_text_v3(raw_text)
            if cleaned_text:
                paragraphs.append(cleaned_text)

        if paragraphs:
            section = ""
            if title:
                section += title + "\n"
            section += "\n".join(paragraphs)
            cleaned_sections.append(section.strip())

    with open(output_txt_path, "w", encoding="utf-8") as out:
        out.write("\n\n".join(cleaned_sections))

    print(f"✅ Extracted {len(cleaned_sections)} cleaned sections into {output_txt_path}")



#extract_text_from_tei("IRINA.tei.xml", "IRINA_orig.txt") 