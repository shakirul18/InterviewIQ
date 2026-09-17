from functools import lru_cache
from pathlib import Path
import difflib
import pickle
import re

import numpy as np


# ============================================================
# MODEL PATH
# ============================================================

MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "models"
    / "best_model.pkl"
)


# ============================================================
# INTERNAL LABEL → DATABASE SCORE
#
# These scores are ONLY used internally because the existing
# database structure stores a numeric value.
#
# They are NOT returned to the frontend.
# ============================================================

LABEL_TO_SCORE = {
    "Weak": 0.0,
    "Average": 50.0,
    "Strong": 100.0,
}


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def _normalize(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        str(text).strip().lower()
    )


def _tokens(text: str):
    return re.findall(
        r"[A-Za-z]+(?:'[A-Za-z]+)?",
        str(text).lower()
    )


# ============================================================
# QUESTION COPY DETECTION
#
# Prevents a user from simply submitting the question itself
# as the answer.
# ============================================================

def _copy_of_question(
    answer: str,
    question: str
) -> bool:

    answer_text = _normalize(answer)
    question_text = _normalize(question)

    if not answer_text or not question_text:
        return False


    # Exact copy
    if answer_text == question_text:
        return True


    # Very high character similarity
    similarity = difflib.SequenceMatcher(
        None,
        answer_text,
        question_text
    ).ratio()

    if similarity >= 0.90:
        return True


    # Token overlap
    answer_tokens = _tokens(answer_text)
    question_tokens = set(
        _tokens(question_text)
    )

    if len(answer_tokens) >= 5:

        overlap = sum(
            token in question_tokens
            for token in answer_tokens
        ) / len(answer_tokens)

        if overlap >= 0.90 and similarity >= 0.75:
            return True


    return False


# ============================================================
# LOAD TRAINED MODEL
# ============================================================

@lru_cache(maxsize=1)
def _trained_model():

    if not MODEL_PATH.exists():

        print(
            "InterviewIQ: trained model not found:",
            MODEL_PATH
        )

        return None


    try:

        with open(
            MODEL_PATH,
            "rb"
        ) as file:

            bundle = pickle.load(file)


        if not isinstance(bundle, dict):

            print(
                "InterviewIQ: invalid model bundle."
            )

            return None


        required_keys = [
            "embedding_model",
            "model",
            "fusion",
            "labels",
        ]

        missing = [
            key
            for key in required_keys
            if key not in bundle
        ]

        if missing:

            print(
                "InterviewIQ: model bundle missing:",
                missing
            )

            return None


        print(
            "InterviewIQ: trained model loaded successfully."
        )

        return bundle


    except Exception as error:

        print(
            "InterviewIQ: model loading error:",
            error
        )

        return None


# ============================================================
# TF-IDF / SUBWORD EMBEDDING
# ============================================================

def _tfidf_embedding(
    embedding_model,
    texts
):

    vectorizer = embedding_model["vectorizer"]

    svd = embedding_model.get("svd")

    matrix = vectorizer.transform(
        texts
    )

    if svd is not None:

        matrix = svd.transform(
            matrix
        )

    return np.asarray(
        matrix,
        dtype=np.float32
    )


# ============================================================
# DISTRIBUTION-BASED EMBEDDING
# ============================================================

def _distribution_embedding(
    embedding_model,
    texts
):

    vectorizer = embedding_model["vectorizer"]

    word_vectors = embedding_model["word_vectors"]

    matrix = vectorizer.transform(
        texts
    )


    output = np.zeros(
        (
            len(texts),
            word_vectors.shape[1]
        ),
        dtype=np.float32
    )


    for index, row in enumerate(matrix):

        ids = row.indices

        weights = row.data


        if len(ids) == 0:
            continue


        output[index] = np.average(
            word_vectors[ids],
            axis=0,
            weights=weights
        )


    return output


# ============================================================
# GENERAL EMBEDDING FUNCTION
# ============================================================

def _embedding(
    embedding_model,
    texts
):

    embedding_type = embedding_model.get(
        "type",
        ""
    )


    if embedding_type in (
        "TFIDF-SVD",
        "Subword-SVD",
    ):

        return _tfidf_embedding(
            embedding_model,
            texts
        )


    if embedding_type in (
        "GloVe-style-SVD",
        "Word-Distribution-SVD",
    ):

        return _distribution_embedding(
            embedding_model,
            texts
        )


    raise ValueError(
        f"Unknown embedding type: {embedding_type}"
    )


# ============================================================
# LATE FUSION
# ============================================================

def _late_predict(
    model,
    question_vector,
    answer_vector
):

    qnet, anet, final = model


    question_representation = (
        qnet.predict_proba(
            question_vector
        )
    )

    answer_representation = (
        anet.predict_proba(
            answer_vector
        )
    )


    fused = np.hstack(
        [
            question_representation,
            answer_representation,
        ]
    )


    prediction = final.predict(
        fused
    )


    probabilities = final.predict_proba(
        fused
    )


    return prediction, probabilities


# ============================================================
# FEEDBACK
# ============================================================

def _feedback(label):

    feedback_map = {

        "Strong":
            (
                "Your answer covers the expected concept "
                "reasonably well. Try adding a concrete "
                "example when possible."
            ),

        "Average":
            (
                "Your answer is partially relevant. Add more "
                "technical detail, explanation, or an example "
                "to make it stronger."
            ),

        "Weak":
            (
                "Your answer needs more relevant technical "
                "content. Focus on directly explaining the "
                "concept asked in the question."
            ),
    }


    return feedback_map.get(
        label,
        "Please provide a more detailed answer."
    )


# ============================================================
# LABEL NORMALIZATION
# ============================================================

def _normalize_label(
    label
):

    if label is None:
        return "Weak"


    label = str(label).strip()


    # Handle possible numeric prediction
    if label in (
        "0",
        "0.0"
    ):
        return "Weak"


    if label in (
        "1",
        "1.0"
    ):
        return "Average"


    if label in (
        "2",
        "2.0"
    ):
        return "Strong"


    # Handle case differences
    label_lower = label.lower()


    if label_lower == "weak":
        return "Weak"


    if label_lower == "average":
        return "Average"


    if label_lower == "strong":
        return "Strong"


    return "Weak"


# ============================================================
# MAIN EVALUATION FUNCTION
#
# IMPORTANT:
# main.py calls this function with exactly 4 arguments:
#
# evaluate_answer(
#     answer,
#     question,
#     reference,
#     keywords
# )
#
# ============================================================

def evaluate_answer(
    answer: str,
    question: str,
    reference: str,
    keywords: list[str]
):

    # --------------------------------------------------------
    # Clean answer
    # --------------------------------------------------------

    normalized_answer = str(
        answer
    ).strip()


    # --------------------------------------------------------
    # Empty answer
    # --------------------------------------------------------

    if not normalized_answer:

        return {
            "score": 0.0,
            "label": "Weak",
            "feedback": "Please provide an answer.",
        }


    # --------------------------------------------------------
    # Detect copied question
    # --------------------------------------------------------

    if _copy_of_question(
        normalized_answer,
        question
    ):

        return {
            "score": 0.0,
            "label": "Weak",
            "feedback": (
                "Please answer the question in your own "
                "words and include relevant explanation "
                "or examples."
            ),
        }


    # --------------------------------------------------------
    # Load trained AI model
    # --------------------------------------------------------

    bundle = _trained_model()


    if bundle is None:

        return {
            "score": 0.0,
            "label": "Weak",
            "feedback": (
                "Trained model is not available. "
                "Please train the model first."
            ),
        }


    try:

        # ----------------------------------------------------
        # Extract model components
        # ----------------------------------------------------

        embedding_model = bundle[
            "embedding_model"
        ]

        classifier = bundle[
            "model"
        ]

        fusion = bundle[
            "fusion"
        ]

        labels = bundle[
            "labels"
        ]


        # ----------------------------------------------------
        # Question and Answer are embedded separately
        # ----------------------------------------------------

        question_vector = _embedding(
            embedding_model,
            [question]
        )

        answer_vector = _embedding(
            embedding_model,
            [normalized_answer]
        )


        # ----------------------------------------------------
        # EARLY FUSION
        # ----------------------------------------------------

        if str(fusion).lower() == "early":

            fused_input = np.hstack(
                [
                    question_vector,
                    answer_vector,
                ]
            )


            prediction = classifier.predict(
                fused_input
            )


            predicted_class = int(
                prediction[0]
            )


        # ----------------------------------------------------
        # LATE FUSION
        # ----------------------------------------------------

        else:

            prediction, _ = _late_predict(
                classifier,
                question_vector,
                answer_vector
            )


            predicted_class = int(
                prediction[0]
            )


        # ----------------------------------------------------
        # Convert predicted class to category
        # ----------------------------------------------------

        if isinstance(labels, dict):

            label = labels.get(
                predicted_class,
                labels.get(
                    str(predicted_class),
                    "Weak"
                )
            )

        else:

            label = labels[
                predicted_class
            ]


        label = _normalize_label(
            label
        )


        # ----------------------------------------------------
        # Internal database score
        #
        # NOT exposed to frontend.
        # ----------------------------------------------------

        score = LABEL_TO_SCORE.get(
            label,
            0.0
        )


        # ----------------------------------------------------
        # Final result
        # ----------------------------------------------------

        return {
            "score": score,
            "label": label,
            "feedback": _feedback(label),
        }


    except Exception as error:

        print(
            "InterviewIQ: model evaluation error:",
            error
        )


        return {
            "score": 0.0,
            "label": "Weak",
            "feedback": (
                "The model could not evaluate this answer. "
                "Please try again."
            ),
        }