import json
import re
import pickle
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
)
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline

warnings.filterwarnings("ignore")

# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent

DATA = ROOT / "data" / "InterviewIQ_Validated_Master_Dataset.csv"

OUT = ROOT / "models"
OUT.mkdir(exist_ok=True)

# ============================================================
# LABELS
# ============================================================

LABELS = {
    "Weak": 0,
    "Average": 1,
    "Strong": 2,
}

INV = {
    0: "Weak",
    1: "Average",
    2: "Strong",
}


# ============================================================
# TEXT TOKENIZER
# ============================================================

def tok(text):
    """
    Simple English tokenizer.
    """
    return re.findall(
        r"[A-Za-z]+(?:'[A-Za-z]+)?",
        str(text).lower()
    )


# ============================================================
# 1. TF-IDF + SVD EMBEDDING
# ============================================================

def build_tfidf_embedding(train_q, train_a, all_q, all_a):
    """
    TF-IDF representation followed by Truncated SVD.

    Question and Answer are transformed using the same
    vocabulary and projection space.
    """

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        max_features=800,
        sublinear_tf=True,
    )

    train_texts = list(train_q) + list(train_a)

    vectorizer.fit(train_texts)

    train_matrix = vectorizer.transform(train_texts)

    max_components = min(
        32,
        train_matrix.shape[0] - 1,
        train_matrix.shape[1] - 1,
    )

    if max_components >= 2:

        svd = TruncatedSVD(
            n_components=max_components,
            random_state=42,
        )

        svd.fit(train_matrix)

        q_vec = svd.transform(
            vectorizer.transform(all_q)
        ).astype(np.float32)

        a_vec = svd.transform(
            vectorizer.transform(all_a)
        ).astype(np.float32)

    else:

        svd = None

        q_vec = vectorizer.transform(
            all_q
        ).toarray().astype(np.float32)

        a_vec = vectorizer.transform(
            all_a
        ).toarray().astype(np.float32)

    return q_vec, a_vec, {
        "type": "TFIDF-SVD",
        "vectorizer": vectorizer,
        "svd": svd,
    }


# ============================================================
# 2. GLOVE-STYLE CO-OCCURRENCE + SVD
# ============================================================

def build_glove_style_embedding(train_q, train_a, all_q, all_a):
    """
    Lightweight GloVe-style distributional representation.

    A word co-occurrence matrix is constructed from the
    training corpus and reduced using SVD.
    """

    vectorizer = CountVectorizer(
        token_pattern=r"(?u)\b\w+\b",
        max_features=800,
    )

    train_texts = list(train_q) + list(train_a)

    vectorizer.fit(train_texts)

    train_counts = vectorizer.transform(train_texts).astype(
        np.float32
    )

    # Word-word co-occurrence matrix
    co_matrix = (
        train_counts.T @ train_counts
    ).toarray()

    # Log-scaled co-occurrence
    co_matrix = np.log1p(co_matrix)

    vocab_size = co_matrix.shape[0]

    if vocab_size >= 3:

        n_components = min(
            32,
            vocab_size - 1,
        )

        svd = TruncatedSVD(
            n_components=n_components,
            random_state=42,
        )

        word_vectors = svd.fit_transform(
            co_matrix
        ).astype(np.float32)

    else:

        svd = None

        word_vectors = co_matrix.astype(
            np.float32
        )

    def encode(texts):

        matrix = vectorizer.transform(texts)

        output = np.zeros(
            (
                len(texts),
                word_vectors.shape[1],
            ),
            dtype=np.float32,
        )

        for i, row in enumerate(matrix):

            ids = row.indices
            weights = row.data

            if len(ids) > 0:

                vectors = word_vectors[ids]

                output[i] = np.average(
                    vectors,
                    axis=0,
                    weights=weights,
                )

        return output

    q_vec = encode(all_q)
    a_vec = encode(all_a)

    return q_vec, a_vec, {
        "type": "GloVe-style-SVD",
        "vectorizer": vectorizer,
        "svd": svd,
        "word_vectors": word_vectors,
    }


# ============================================================
# 3. WORD DISTRIBUTIONAL SVD
# ============================================================

def build_word_distribution_embedding(
    train_q,
    train_a,
    all_q,
    all_a,
):
    """
    Lightweight word-distributional embedding.

    This is NOT a dependency on the Gensim Word2Vec package.
    It learns word representations from the training corpus
    using a word-context matrix and SVD.
    """

    vectorizer = CountVectorizer(
        token_pattern=r"(?u)\b\w+\b",
        max_features=800,
    )

    train_texts = list(train_q) + list(train_a)

    vectorizer.fit(train_texts)

    counts = vectorizer.transform(
        train_texts
    ).astype(np.float32)

    # Binary occurrence matrix
    binary = (counts > 0).astype(np.float32)

    # Context similarity matrix
    context_matrix = (
        binary.T @ binary
    ).toarray()

    # Smooth the matrix
    context_matrix = np.log1p(
        context_matrix
    )

    vocab_size = context_matrix.shape[0]

    if vocab_size >= 3:

        n_components = min(
            32,
            vocab_size - 1,
        )

        svd = TruncatedSVD(
            n_components=n_components,
            random_state=123,
        )

        word_vectors = svd.fit_transform(
            context_matrix
        ).astype(np.float32)

    else:

        svd = None

        word_vectors = context_matrix.astype(
            np.float32
        )

    def encode(texts):

        matrix = vectorizer.transform(texts)

        output = np.zeros(
            (
                len(texts),
                word_vectors.shape[1],
            ),
            dtype=np.float32,
        )

        for i, row in enumerate(matrix):

            ids = row.indices

            if len(ids) > 0:

                output[i] = np.mean(
                    word_vectors[ids],
                    axis=0,
                )

        return output

    q_vec = encode(all_q)
    a_vec = encode(all_a)

    return q_vec, a_vec, {
        "type": "Word-Distribution-SVD",
        "vectorizer": vectorizer,
        "svd": svd,
        "word_vectors": word_vectors,
    }


# ============================================================
# 4. SUBWORD / CHARACTER N-GRAM EMBEDDING
# ============================================================

def build_subword_embedding(
    train_q,
    train_a,
    all_q,
    all_a,
):
    """
    Subword representation using character n-grams.

    This provides a FastText-inspired subword baseline without
    requiring the Gensim FastText package.
    """

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
        max_features=1000,
        sublinear_tf=True,
    )

    train_texts = list(train_q) + list(train_a)

    vectorizer.fit(train_texts)

    train_matrix = vectorizer.transform(
        train_texts
    )

    max_components = min(
        32,
        train_matrix.shape[0] - 1,
        train_matrix.shape[1] - 1,
    )

    if max_components >= 2:

        svd = TruncatedSVD(
            n_components=max_components,
            random_state=123,
        )

        svd.fit(train_matrix)

        q_vec = svd.transform(
            vectorizer.transform(all_q)
        ).astype(np.float32)

        a_vec = svd.transform(
            vectorizer.transform(all_a)
        ).astype(np.float32)

    else:

        svd = None

        q_vec = vectorizer.transform(
            all_q
        ).toarray().astype(np.float32)

        a_vec = vectorizer.transform(
            all_a
        ).toarray().astype(np.float32)

    return q_vec, a_vec, {
        "type": "Subword-SVD",
        "vectorizer": vectorizer,
        "svd": svd,
    }


# ============================================================
# BUILD ALL EMBEDDINGS
# ============================================================

def build_embeddings(
    train_q,
    train_a,
    all_q,
    all_a,
):

    print("\nBuilding embedding representations...")

    tf_q, tf_a, tf_obj = build_tfidf_embedding(
        train_q,
        train_a,
        all_q,
        all_a,
    )

    print("  [1/4] TF-IDF + SVD complete")

    gl_q, gl_a, gl_obj = build_glove_style_embedding(
        train_q,
        train_a,
        all_q,
        all_a,
    )

    print("  [2/4] GloVe-style SVD complete")

    wd_q, wd_a, wd_obj = build_word_distribution_embedding(
        train_q,
        train_a,
        all_q,
        all_a,
    )

    print("  [3/4] Word Distribution SVD complete")

    sub_q, sub_a, sub_obj = build_subword_embedding(
        train_q,
        train_a,
        all_q,
        all_a,
    )

    print("  [4/4] Subword SVD complete")

    return {

        "TFIDF-SVD": (
            tf_q,
            tf_a,
            tf_obj,
        ),

        "GloVe-style-SVD": (
            gl_q,
            gl_a,
            gl_obj,
        ),

        "Word-Distribution-SVD": (
            wd_q,
            wd_a,
            wd_obj,
        ),

        "Subword-SVD": (
            sub_q,
            sub_a,
            sub_obj,
        ),
    }


# ============================================================
# BALANCING
# ============================================================

def balance(X, y):

    rng = np.random.default_rng(42)

    classes, counts = np.unique(
        y,
        return_counts=True,
    )

    target = counts.max()

    indices = []

    for cls in classes:

        class_indices = np.where(
            y == cls
        )[0]

        selected = rng.choice(
            class_indices,
            size=target,
            replace=True,
        )

        indices.extend(selected)

    indices = np.asarray(indices)

    rng.shuffle(indices)

    return X[indices], y[indices]


# ============================================================
# EARLY FUSION
# ============================================================

def early_model(Xtr, ytr):

    model = make_pipeline(
        StandardScaler(),

        MLPClassifier(
            hidden_layer_sizes=(64, 32),
            activation="relu",
            solver="adam",
            alpha=0.0005,
            batch_size=32,
            learning_rate_init=0.001,
            max_iter=800,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=30,
            random_state=42,
        ),
    )

    return model


# ============================================================
# LATE FUSION
# ============================================================

def late_model(
    qtr,
    atr,
    ytr,
):

    # Question branch
    qnet = make_pipeline(

        StandardScaler(),

        MLPClassifier(
            hidden_layer_sizes=(32,),
            activation="relu",
            solver="adam",
            alpha=0.0005,
            max_iter=600,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=25,
            random_state=42,
        ),
    )

    # Answer branch
    anet = make_pipeline(

        StandardScaler(),

        MLPClassifier(
            hidden_layer_sizes=(32,),
            activation="relu",
            solver="adam",
            alpha=0.0005,
            max_iter=600,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=25,
            random_state=43,
        ),
    )

    qnet.fit(
        qtr,
        ytr,
    )

    anet.fit(
        atr,
        ytr,
    )

    # Learned probability representations
    q_hidden = qnet.predict_proba(qtr)
    a_hidden = anet.predict_proba(atr)

    fused = np.hstack(
        [
            q_hidden,
            a_hidden,
        ]
    )

    # Final neural classifier
    final = make_pipeline(

        StandardScaler(),

        MLPClassifier(
            hidden_layer_sizes=(32, 16),
            activation="relu",
            solver="adam",
            alpha=0.0005,
            max_iter=700,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=30,
            random_state=44,
        ),
    )

    final.fit(
        fused,
        ytr,
    )

    return (
        qnet,
        anet,
        final,
    )


# ============================================================
# LATE FUSION PREDICTION
# ============================================================

def late_predict(
    model,
    q,
    a,
):

    qnet, anet, final = model

    q_rep = qnet.predict_proba(q)
    a_rep = anet.predict_proba(a)

    fused = np.hstack(
        [
            q_rep,
            a_rep,
        ]
    )

    return final.predict(
        fused
    )


# ============================================================
# MAIN TRAINING PIPELINE
# ============================================================

def main():

    print("=" * 70)
    print("INTERVIEWIQ FINAL AI MODEL TRAINING")
    print("=" * 70)

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    if not DATA.exists():

        raise FileNotFoundError(
            f"Dataset not found:\n{DATA}"
        )

    df = pd.read_csv(DATA)

    # Keep only valid labels
    df = df[
        df["Final_Label"].isin(LABELS)
    ].copy()

    df = df.reset_index(
        drop=True
    )

    print(
        f"\nRecords used: {len(df)}"
    )

    print(
        f"Unique Questions: "
        f"{df['Question'].nunique()}"
    )

    print(
        f"Unique Answers: "
        f"{df['Answer'].nunique()}"
    )

    print("\nLabel distribution:")

    print(
        df["Final_Label"].value_counts()
    )

    # --------------------------------------------------------
    # Prepare text and labels
    # --------------------------------------------------------

    y = df[
        "Final_Label"
    ].map(LABELS).to_numpy()

    questions = (
        df["Question"]
        .fillna("")
        .astype(str)
        .to_numpy()
    )

    answers = (
        df["Answer"]
        .fillna("")
        .astype(str)
        .to_numpy()
    )

    # --------------------------------------------------------
    # Train/Test split
    # --------------------------------------------------------

    indices = np.arange(
        len(df)
    )

    train_idx, test_idx = train_test_split(
        indices,
        test_size=0.25,
        stratify=y,
        random_state=42,
    )

    print(
        f"\nTraining records: "
        f"{len(train_idx)}"
    )

    print(
        f"Testing records: "
        f"{len(test_idx)}"
    )

    # --------------------------------------------------------
    # Build embeddings
    # --------------------------------------------------------

    embeddings = build_embeddings(
        questions[train_idx],
        answers[train_idx],
        questions,
        answers,
    )

    # --------------------------------------------------------
    # Model comparison
    # --------------------------------------------------------

    results = []

    saved_model = None

    for name, (
        q_embedding,
        a_embedding,
        embedding_object,
    ) in embeddings.items():

        print("\n" + "=" * 70)

        print(
            f"Embedding: {name}"
        )

        print("=" * 70)

        # ====================================================
        # EARLY FUSION
        # ====================================================

        print(
            "\nTraining Early Fusion..."
        )

        X_train = np.hstack(
            [
                q_embedding[train_idx],
                a_embedding[train_idx],
            ]
        )

        X_test = np.hstack(
            [
                q_embedding[test_idx],
                a_embedding[test_idx],
            ]
        )

        X_balanced, y_balanced = balance(
            X_train,
            y[train_idx],
        )

        early = early_model(
            X_balanced,
            y_balanced,
        )

        early.fit(
            X_balanced,
            y_balanced,
        )

        early_pred = early.predict(
            X_test
        )

        p, r, f, _ = (
            precision_recall_fscore_support(
                y[test_idx],
                early_pred,
                average="macro",
                zero_division=0,
            )
        )

        early_acc = accuracy_score(
            y[test_idx],
            early_pred,
        )

        results.append(
            {
                "Embedding": name,
                "Fusion": "Early",
                "Accuracy": early_acc,
                "Precision_macro": p,
                "Recall_macro": r,
                "F1_macro": f,
            }
        )

        print(
            f"Early Fusion F1: {f:.4f}"
        )

        if (
            saved_model is None
            or f > saved_model[0]
        ):

            saved_model = (
                f,
                name,
                "Early",
                early,
                embedding_object,
            )

        # ====================================================
        # LATE FUSION
        # ====================================================

        print(
            "\nTraining Late Fusion..."
        )

        q_train = q_embedding[
            train_idx
        ]

        a_train = a_embedding[
            train_idx
        ]

        # IMPORTANT:
        # Balance using the SAME indices for Q and A
        # so that Question-Answer pairs remain aligned.

        rng = np.random.default_rng(42)

        classes, counts = np.unique(
            y[train_idx],
            return_counts=True,
        )

        target = counts.max()

        balanced_indices = []

        for cls in classes:

            cls_indices = np.where(
                y[train_idx] == cls
            )[0]

            selected = rng.choice(
                cls_indices,
                size=target,
                replace=True,
            )

            balanced_indices.extend(
                selected
            )

        balanced_indices = np.asarray(
            balanced_indices
        )

        rng.shuffle(
            balanced_indices
        )

        q_balanced = q_train[
            balanced_indices
        ]

        a_balanced = a_train[
            balanced_indices
        ]

        y_balanced = y[
            train_idx
        ][balanced_indices]

        late = late_model(
            q_balanced,
            a_balanced,
            y_balanced,
        )

        late_pred = late_predict(
            late,
            q_embedding[test_idx],
            a_embedding[test_idx],
        )

        p, r, f, _ = (
            precision_recall_fscore_support(
                y[test_idx],
                late_pred,
                average="macro",
                zero_division=0,
            )
        )

        late_acc = accuracy_score(
            y[test_idx],
            late_pred,
        )

        results.append(
            {
                "Embedding": name,
                "Fusion": "Late",
                "Accuracy": late_acc,
                "Precision_macro": p,
                "Recall_macro": r,
                "F1_macro": f,
            }
        )

        print(
            f"Late Fusion F1: {f:.4f}"
        )

        if f > saved_model[0]:

            saved_model = (
                f,
                name,
                "Late",
                late,
                embedding_object,
            )

    # --------------------------------------------------------
    # Save comparison results
    # --------------------------------------------------------

    result_df = pd.DataFrame(
        results
    ).sort_values(
        "F1_macro",
        ascending=False,
    )

    result_path = (
        OUT / "model_comparison.csv"
    )

    result_df.to_csv(
        result_path,
        index=False,
    )

    # --------------------------------------------------------
    # Save best model
    # --------------------------------------------------------

    (
        best_f1,
        best_embedding,
        best_fusion,
        best_model,
        best_embedding_object,
    ) = saved_model

    model_bundle = {

        "fusion": best_fusion,

        "embedding": best_embedding,

        "model": best_model,

        "embedding_model": best_embedding_object,

        "labels": INV,

    }

    model_path = (
        OUT / "best_model.pkl"
    )

    with open(
        model_path,
        "wb",
    ) as f:

        pickle.dump(
            model_bundle,
            f,
        )

    # --------------------------------------------------------
    # Save metadata
    # --------------------------------------------------------

    metadata = {

        "records_used": int(len(df)),

        "unique_questions": int(
            df["Question"].nunique()
        ),

        "unique_answers": int(
            df["Answer"].nunique()
        ),

        "train_records": int(
            len(train_idx)
        ),

        "test_records": int(
            len(test_idx)
        ),

        "best_embedding": best_embedding,

        "best_fusion": best_fusion,

        "best_macro_f1": float(
            best_f1
        ),

        "architecture": (
            "Separate Question/Answer "
            "Representations -> "
            "Early/Late Fusion -> "
            "MLP Neural Classifier"
        ),

    }

    metadata_path = (
        OUT / "training_metadata.json"
    )

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2,
        ),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Print final results
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("FINAL MODEL COMPARISON")
    print("=" * 70)

    print(
        result_df.to_string(
            index=False
        )
    )

    print("\n")
    print("=" * 70)

    print(
        f"Best Embedding: "
        f"{best_embedding}"
    )

    print(
        f"Best Fusion: "
        f"{best_fusion}"
    )

    print(
        f"Best Macro-F1: "
        f"{best_f1:.4f}"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    if best_fusion == "Early":

        best_q = embeddings[
            best_embedding
        ][0]

        best_a = embeddings[
            best_embedding
        ][1]

        best_test_X = np.hstack(
            [
                best_q[test_idx],
                best_a[test_idx],
            ]
        )

        best_prediction = (
            best_model.predict(
                best_test_X
            )
        )

    else:

        best_q = embeddings[
            best_embedding
        ][0]

        best_a = embeddings[
            best_embedding
        ][1]

        best_prediction = late_predict(
            best_model,
            best_q[test_idx],
            best_a[test_idx],
        )

    cm = confusion_matrix(
        y[test_idx],
        best_prediction,
        labels=[0, 1, 2],
    )

    print(
        "\nConfusion Matrix"
    )

    print(
        pd.DataFrame(
            cm,
            index=[
                "Actual Weak",
                "Actual Average",
                "Actual Strong",
            ],
            columns=[
                "Pred Weak",
                "Pred Average",
                "Pred Strong",
            ],
        )
    )

    print("\n")
    print(
        "Saved files:"
    )

    print(
        f"  {result_path}"
    )

    print(
        f"  {model_path}"
    )

    print(
        f"  {metadata_path}"
    )

    print("\nTraining completed successfully.")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()