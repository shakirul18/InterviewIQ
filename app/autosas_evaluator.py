"""
InterviewIQ evaluator using the locally trained AutoSAS-inspired model.
Numeric values stay internal; the UI receives only Weak/Average/Strong.
"""
from pathlib import Path
from difflib import SequenceMatcher
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "autosas_lite.pkl"
_package = joblib.load(MODEL_PATH)
_model = _package["model"]
_vectorizer = _package["vectorizer"]

def normalize_text(text):
    return " ".join(str(text).strip().lower().split())

def basic_features(text):
    words = text.split()
    unique_words = set(words)
    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    return np.asarray([[
        len(text), len(words), len(unique_words),
        len(unique_words) / max(1, len(words)),
        sum(len(w) for w in words) / max(1, len(words)),
        sentences, len(text) / max(1, sentences),
        sum(c.isdigit() for c in text), sum(c.isupper() for c in text)
    ]], dtype=float)

def model_prediction(answer):
    text = normalize_text(answer)
    features = np.hstack([basic_features(text), _vectorizer.transform([text]).toarray()])
    return float(np.clip(_model.predict(features)[0], 0, 3))

def _similarity(a, b):
    if not b:
        return 0.0
    v = TfidfVectorizer(ngram_range=(1, 2))
    m = v.fit_transform([normalize_text(a), normalize_text(b)])
    return float((m[0] @ m[1].T).toarray()[0, 0]) if m.shape[1] else 0.0

def keyword_coverage(answer, keywords):
    if not keywords:
        return 0.0
    text = normalize_text(answer)
    tokens = text.split()
    covered = 0
    for keyword in keywords:
        key = normalize_text(keyword)
        if not key:
            continue
        if key in text or any(SequenceMatcher(None, key, t).ratio() >= 0.82 for t in tokens):
            covered += 1
    return covered / len(keywords)

def determine_label(model_score, reference_score, question_score, keyword_score, words):
    if words < 8:
        return "Weak"
    if model_score >= 2.0:
        return "Strong"
    if reference_score >= 0.38 and words >= 30:
        return "Strong"
    if keyword_score >= 0.60 and words >= 25 and (reference_score >= 0.20 or question_score >= 0.15):
        return "Strong"
    if keyword_score >= 0.40 and reference_score >= 0.30 and words >= 25:
        return "Strong"
    if model_score >= 1.0:
        return "Average"
    if reference_score >= 0.18 and words >= 15:
        return "Average"
    if keyword_score >= 0.35 and words >= 15:
        return "Average"
    if question_score >= 0.20 and words >= 15:
        return "Average"
    return "Weak"

def feedback_for(label):
    if label == "Strong":
        return "Good answer. Your response is relevant and covers the main idea clearly."
    if label == "Average":
        return "Your answer covers part of the topic. Add a few more relevant details, concepts, or examples to make it stronger."
    return "The answer is too brief or misses important concepts. Explain the main idea more clearly and include relevant details or examples."

def evaluate_answer(answer, question, reference, keywords):
    clean = normalize_text(answer)
    words = len(clean.split())
    model_score = model_prediction(clean)
    reference_score = _similarity(clean, reference)
    question_score = _similarity(clean, question)
    keyword_score = keyword_coverage(clean, keywords)
    label = determine_label(model_score, reference_score, question_score, keyword_score, words)
    return {
        "score": {"Weak": 0.30, "Average": 0.65, "Strong": 0.90}[label],
        "label": label,
        "feedback": feedback_for(label),
    }
