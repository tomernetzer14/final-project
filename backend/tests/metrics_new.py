# improved_metrics_new.py
import csv
import spacy
import textstat
import re

from collections import Counter
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine

# Load spaCy NLP pipeline once globally
nlp = spacy.load("en_core_web_sm")
sbert_model = SentenceTransformer("all-MiniLM-L6-v2")


def load_common_words(path="google-10000-english.txt"):
    with open(path, "r", encoding="utf-8") as file:
        return set(line.strip().lower() for line in file)


def load_frequency_data(file_path):
    frequency_data = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t') 
        for row in reader:
            word = row['word'].strip().lower()
            freq = int(row['freq'])
            frequency_data[word] = freq

    max_freq = max(frequency_data.values())
    for word in frequency_data:
        frequency_data[word] /= max_freq 
    return frequency_data


def calculate_word_freq_score(text, frequency_data):
    words = text.lower().split()
    score, count = 0, 0
    for word in words:
        word = word.strip(".,!?\"'")
        if word in frequency_data:
            score += frequency_data[word]
            count += 1
    return (score / count) if count else 0


def avg_sentence_length(text):
    doc = nlp(text)
    sentences = list(doc.sents)
    return len(text.split()) / len(sentences) if sentences else 0


def avg_syllables_per_word(text):
    words = text.split()
    if not words:
        return 0
    return sum(textstat.syllable_count(word) for word in words) / len(words)




def calculate_complexity(text):
    words = text.split()
    if not words:
        return 0
    total_words = len(words)
    avg_syllables = avg_syllables_per_word(text)
    avg_word_length = sum(len(w) for w in words) / total_words
    complex_word_ratio = sum(
        1 for w in words if textstat.syllable_count(w) >= 3
    ) / total_words

    s_score = normalize(avg_syllables, 1, 3)
    c_score = normalize(complex_word_ratio, 0, 0.6)
    l_score = normalize(avg_word_length, 3, 8)
    return 0.4 * s_score + 0.4 * c_score + 0.2 * l_score


def flesch_reading_ease_fixed(text):
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    total_sentences = len(sentences)
    words = text.split()
    total_words = len(words)
    total_syllables = sum(textstat.syllable_count(word) for word in words)
    if total_sentences == 0 or total_words == 0:
        return 0
    score = 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)
    return max(0, min(score, 100))


def calculate_readability(text, common_words_set):
    if not text.strip():
        return 0
    words = text.split()
    total_words = len(words)
    if total_words == 0:
        return 0
    flesch_score = flesch_reading_ease_fixed(text)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    avg_sentence_len = total_words / max(1, len(sentences))
    common_count = sum(1 for word in words if word.lower().strip(".,!?\"'") in common_words_set)
    common_ratio = common_count / total_words
    score = (
        flesch_score * 0.7 +
        (1 - avg_sentence_len / 25) * 0.15 +
        common_ratio * 0.15
    )
    return max(0, min(score, 100))


def normalize(value, min_val, max_val):
    normalized = (max_val - value) / (max_val - min_val)
    return max(0, min(100, normalized * 100))


def ngrams(text, n):
    tokens = text.lower().strip().split()
    return set(zip(*[tokens[i:] for i in range(n)]))

def safe_div(x, y):
    return x / y if y else 0.0

def f1(p, r):
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def calculate_embedding_similarity(generated_text, reference_text):

    gen_emb = sbert_model.encode(generated_text, convert_to_tensor=False)
    ref_emb = sbert_model.encode(reference_text, convert_to_tensor=False)

    similarity = 1 - cosine(gen_emb, ref_emb)
    return similarity * 100
