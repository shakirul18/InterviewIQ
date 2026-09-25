"""
InterviewIQ - lightweight AutoSAS-inspired local training pipeline.
This is an adaptation inspired by the AutoSAS short-answer scoring paper,
not the authors' exact original implementation.
"""
from pathlib import Path
from urllib.request import urlretrieve
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

DATA_URL = "https://huggingface.co/datasets/nlpatunt/D_ASAP-SAS/resolve/main/train.csv"
DATA_DIR = Path("data")
MODEL_DIR = Path("models")
DATA_FILE = DATA_DIR / "asap_sas_train.csv"
MODEL_FILE = MODEL_DIR / "autosas_lite.pkl"
MAX_ROWS = 2500
RANDOM_STATE = 42

def normalize_text(text):
    return " ".join(str(text).strip().lower().split())

def basic_features(texts):
    rows = []
    for text in texts:
        words = text.split()
        unique_words = set(words)
        sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
        rows.append([
            len(text), len(words), len(unique_words),
            len(unique_words) / max(1, len(words)),
            sum(len(w) for w in words) / max(1, len(words)),
            sentences, len(text) / max(1, sentences),
            sum(c.isdigit() for c in text), sum(c.isupper() for c in text)
        ])
    return np.asarray(rows, dtype=float)

def load_dataset():
    DATA_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        print("Downloading ASAP-SAS dataset...")
        urlretrieve(DATA_URL, DATA_FILE)

    df = pd.read_csv(DATA_FILE)
    required = {"essay_set", "essay_text", "Score1"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = df.dropna(subset=["essay_text", "Score1"]).copy()
    df["essay_text"] = df["essay_text"].map(normalize_text)
    df["Score1"] = pd.to_numeric(df["Score1"], errors="coerce")
    df = df.dropna(subset=["Score1"])

    if len(df) > MAX_ROWS:
        parts = []
        per_group = max(1, MAX_ROWS // df["essay_set"].nunique())
        for _, group in df.groupby("essay_set"):
            parts.append(group.sample(n=min(per_group, len(group)), random_state=RANDOM_STATE))
        df = pd.concat(parts).sample(frac=1, random_state=RANDOM_STATE)
        if len(df) > MAX_ROWS:
            df = df.sample(MAX_ROWS, random_state=RANDOM_STATE)

    return df.reset_index(drop=True)

def main():
    df = load_dataset()
    print(f"Dataset loaded: {len(df)} rows")
    print(f"Using {len(df)} samples for local training.")

    texts = df["essay_text"].tolist()
    y = df["Score1"].astype(float).to_numpy()

    X_basic = basic_features(texts)
    print("Basic features:", X_basic.shape)

    vectorizer = TfidfVectorizer(
        max_features=1500,
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True,
    )
    X_tfidf = vectorizer.fit_transform(texts).toarray()
    print("TF-IDF features:", X_tfidf.shape)

    X = np.hstack([X_basic, X_tfidf])
    print("Final feature matrix:", X.shape)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE
    )

    model = RandomForestRegressor(
        n_estimators=300,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        max_features="sqrt",
        min_samples_leaf=2,
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    rmse = mean_squared_error(y_test, y_pred) ** 0.5
    mae = mean_absolute_error(y_test, y_pred)

    print(f"\nTest RMSE: {rmse:.4f}")
    print(f"Test MAE : {mae:.4f}")

    MODEL_DIR.mkdir(exist_ok=True)
    import joblib
    joblib.dump({
        "model": model,
        "vectorizer": vectorizer,
        "feature_type": "AutoSAS-inspired TF-IDF + linguistic features",
        "target": "Score1",
        "score_range": [0, 3],
    }, MODEL_FILE)

    print("\nAUTO-SAS MODEL TRAINING COMPLETED")
    print(f"Model: {MODEL_FILE}")
    print(f"Samples: {len(df)}")
    print(f"Features: {X.shape[1]}")
    print(f"RMSE: {rmse:.4f}")
    print(f"MAE : {mae:.4f}")

if __name__ == "__main__":
    main()
