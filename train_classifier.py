"""Train a small, explainable answer-quality classifier for InterviewIQ.

This is separate from the MiniLM similarity feedback used by the web app.
It demonstrates a standard supervised-learning workflow and reports test accuracy.
"""

from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler


DATASET = Path(__file__).parent / "data" / "training_answers.csv"


def answer_length(texts):
    """A transparent feature: detailed answers are normally higher quality."""
    return np.array([[len(str(text).split())] for text in texts])


def main():
    data = pd.read_csv(DATASET)
    x_train, x_test, y_train, y_test = train_test_split(
        data["answer"], data["label"], test_size=0.30, random_state=42, stratify=data["label"]
    )
    model = Pipeline([
        ("features", FeatureUnion([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), stop_words="english", min_df=1)),
            ("answer_length", Pipeline([
                ("count_words", FunctionTransformer(answer_length, validate=False)),
                ("scale", StandardScaler()),
            ])),
        ])),
        ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
    ])
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    print(f"Dataset rows: {len(data)}")
    print(f"Training rows: {len(x_train)} | Test rows: {len(x_test)}")
    print(f"Test accuracy: {accuracy_score(y_test, predictions) * 100:.2f}%")
    print("\nClassification report:")
    print(classification_report(y_test, predictions, zero_division=0))
    print("Note: this starter dataset is intentionally small. Add real, manually labelled answers before reporting the score as a final research result.")


if __name__ == "__main__":
    main()
