# InterviewIQ — AI Interview Practice System

InterviewIQ is a local AI-powered interview practice web application for Software Developer, Data Analyst, and HR Executive roles.

## AI architecture

The academic model treats the task as supervised Question–Answer classification.

1. The validated dataset is stored in `data/InterviewIQ_Validated_Master_Dataset.csv`.
2. Unresolved validation rows are excluded from model training.
3. Question and Answer are represented separately.
4. Four lightweight embedding/representation strategies are compared:
   - TF-IDF-SVD
   - GloVe-style co-occurrence-SVD
   - Word-Distribution-SVD
   - Subword-SVD
5. Two fusion strategies are evaluated:
   - Early Fusion: concatenate Question + Answer representations before the MLP.
   - Late Fusion: process Question and Answer through separate neural branches, then combine their representations.
6. A small MLP neural classifier predicts `Weak`, `Average`, or `Strong`.
7. `models/best_model.pkl` is the trained deployment model.
8. The web app performs local inference with the trained model.

## Important dataset note

The current validated CSV contains 985 resolved records, but only 20 unique questions and 20 unique answers are present. Repeated Q&A content means the current hold-out metrics should not be described as generalization to 1000 unique interview examples. For research-quality evaluation, expand the dataset with genuinely distinct answers.

## Run on Windows — Python 3.14

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000`.

If PowerShell activation is blocked, use the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Output

The web interface intentionally displays only the three model categories:

- Weak
- Average
- Strong

No score, percentage, confidence, or similarity is displayed.

## Optional model training

The trained deployment model is already included. To reproduce the comparison:

```powershell
python train_interviewiq.py
```

This writes:

- `models/model_comparison.csv`
- `models/best_model.pkl`
- `models/training_metadata.json`

## Model comparison from the included training run

The included comparison was generated from the current validated dataset. The measured macro-F1 values are:

| Embedding | Fusion | Macro-F1 |
|---|---|---:|
| TFIDF-SVD | Early | 0.3303 |
| TFIDF-SVD | Late | 0.3206 |
| GloVe-style-SVD | Early | 0.3303 |
| GloVe-style-SVD | Late | 0.3079 |
| Word-Distribution-SVD | Early | 0.3303 |
| Word-Distribution-SVD | Late | 0.3079 |
| Subword-SVD | Early | 0.3274 |
| Subword-SVD | Late | 0.3278 |

The included deployment model is the TFIDF-SVD + Early Fusion + MLP configuration from this comparison.

## Project structure

```text
InterviewIQ/
├── app/
│   ├── database.py
│   ├── evaluator.py
│   ├── main.py
│   ├── questions.py
│   └── static/
├── data/
│   ├── InterviewIQ_Validated_Master_Dataset.csv
│   └── training_answers.csv
├── models/
│   ├── best_model.pkl
│   ├── model_comparison.csv
│   └── training_metadata.json
├── InterviewIQ_Model_Training.ipynb
├── InterviewIQ_Final_Model_Training.ipynb
├── train_interviewiq.py
├── train_classifier.py
├── train_deploy_model.py
├── requirements.txt
├── README.md
└── RUN_NOW.txt
```
