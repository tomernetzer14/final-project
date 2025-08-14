
import pytest
from utils import clean_text, split_sections, split_into_chunks, build_prompt, postprocess_summary, build_importance_mask
from transformers import T5Tokenizer
import torch

def test_clean_text_removes_latex_and_urls():
    text = "Here is a formula: $x^2$ and a URL: https://example.com"
    cleaned = clean_text(text)
    assert "$" not in cleaned and "http" not in cleaned

def test_split_sections_basic():
    text = "Intro\nThis is intro.\nMethods\nThis is methods."
    result = split_sections(text)
    assert "Intro" in result and "Methods" in result

def test_split_into_chunks_output_type():
    text = " ".join(["token"] * 600)
    chunks = split_into_chunks(text, chunk_size=100, overlap=10)
    assert isinstance(chunks, list)
    assert all(isinstance(c, str) for c in chunks)

def test_build_prompt_contains_keywords():
    text = "Sample section text"
    keywords = ["AI", "robotics"]
    prompt = build_prompt(text, keywords)
    assert all(word in prompt for word in keywords)

def test_postprocess_summary_formatting():
    text = "Sentence one. Sentence two. Sentence three."
    result = postprocess_summary(text)
    assert "\n" in result or ". " in result

def test_build_importance_mask_shape():
    tokenizer = T5Tokenizer.from_pretrained("t5-small")
    text = "Simplify and summarize: AI is revolutionizing science.\nFocus on: AI, science"
    input_ids = tokenizer(text, return_tensors="pt").input_ids
    mask = build_importance_mask(input_ids, ["AI", "science"], tokenizer)
    assert mask.shape == input_ids.shape
