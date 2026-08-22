import re
from functools import lru_cache
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@lru_cache(maxsize=1)
def _semantic_model():
    """Load MiniLM only when needed; returning None activates the offline fallback."""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None


def evaluate_answer(answer: str, reference: str, keywords: list[str]):
    normalized = answer.strip()
    if len(normalized.split()) < 5:
        return {"score": 0, "similarity": 0, "feedback": "Your answer is too short. Explain your idea in at least 2–3 clear sentences.", "method": "Basic local check"}

    model = _semantic_model()
    if model:
        embeddings = model.encode([normalized, reference])
        similarity = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
        method = "MiniLM semantic similarity"
    else:
        matrix = TfidfVectorizer(stop_words="english").fit_transform([normalized, reference])
        similarity = float(cosine_similarity(matrix[0], matrix[1])[0][0])
        method = "TF-IDF local fallback"

    answer_words = normalized.lower()
    matches = sum(1 for word in keywords if word.lower() in answer_words)
    keyword_bonus = min(matches / max(len(keywords), 1), 1) * 15
    length_bonus = min(len(normalized.split()) / 45, 1) * 8
    score = round(max(0, min(100, similarity * 77 + keyword_bonus + length_bonus)))

    if score >= 75:
        feedback = "Strong answer. Your explanation is relevant and includes useful points. In a real interview, add one short example to make it even stronger."
    elif score >= 50:
        missing = [word for word in keywords if word.lower() not in answer_words]
        tip = f" Consider mentioning: {', '.join(missing[:3])}." if missing else " Add a practical example for more impact."
        feedback = "Good start, but make the answer more specific and better structured." + tip
    else:
        feedback = "Your answer needs more relevant detail. Define the main idea, explain why it matters, and use a simple example."

    return {"score": score, "similarity": round(similarity * 100, 1), "feedback": feedback, "method": method}
