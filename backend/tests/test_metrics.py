
from metrics_new import (
    calculate_word_freq_score,
    calculate_complexity,
    calculate_readability,
    calculate_embedding_similarity,
    load_common_words,

)

def test_load_common_words_loads_words():
    words = load_common_words("google-10000-english.txt")
    assert isinstance(words, set)
    assert "the" in words

def test_calculate_word_freq_score_returns_number():
    freq_data = {"science": 1.0, "is": 0.5}
    score = calculate_word_freq_score("science is fun", freq_data)
    assert 0 <= score <= 1

def test_calculate_complexity_output():
    score = calculate_complexity("Science is evolving rapidly.")
    assert isinstance(score, float)

def test_calculate_readability_bounds():
    words = {"science", "is", "great"}
    score = calculate_readability("Science is great!", words)
    assert 0 <= score <= 100

def test_embedding_similarity_between_similar_sentences():
    sim = calculate_embedding_similarity("AI is powerful.", "AI is strong.")
    assert 0 <= sim <= 100
