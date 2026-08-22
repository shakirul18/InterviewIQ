# InterviewIQ

InterviewIQ is a beginner-friendly, local AI-powered interview practice web app. It asks role-specific questions, evaluates answers with semantic similarity, gives feedback, and stores interview history.

## Features

- Choose a job role (Software Developer, Data Analyst, HR Executive)
- Practice a five-question interview
- Answer scoring using a lightweight pretrained NLP model (`all-MiniLM-L6-v2`)
- Fully local TF-IDF fallback if the model is unavailable
- Clear feedback, improvement tips, result report, and saved history
- SQLite database: no separate database server required

## Stack

- Backend: Python + FastAPI
- Frontend: HTML, CSS, Vanilla JavaScript
- Database: SQLite
- NLP: `sentence-transformers` (optional at runtime) with scikit-learn fallback

## Setup (Windows)

1. Install **Python 3.11 (recommended)** from [python.org](https://www.python.org/downloads/). Python 3.10–3.12 are also suitable. During installation tick **Add Python to PATH**. (Very new Python releases may not yet be supported by PyTorch, which the MiniLM package uses.)
2. Open PowerShell in this project folder.
3. Create and activate a virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

4. Install packages:

```powershell
pip install -r requirements.txt
```

5. Run the app:

```powershell
uvicorn app.main:app --reload
```

6. Open http://127.0.0.1:8000 in your browser.

The first semantic-model evaluation may download roughly 80 MB of model files once. If there is no internet connection, InterviewIQ automatically uses its built-in TF-IDF evaluation fallback. Both methods run locally; no answer is sent to an AI API.

## Project structure

```text
InterviewIQ/
├── app/
│   ├── main.py          # API routes and web server
│   ├── database.py      # SQLite setup and queries
│   ├── evaluator.py     # NLP score and feedback logic
│   ├── questions.py     # Role-specific question bank
│   └── static/          # HTML, CSS, JavaScript
├── requirements.txt
└── README.md
```

## Viva explanation

1. The user selects a target role and starts an interview.
2. FastAPI creates an interview session in SQLite and sends role-specific questions.
3. For each answer, the NLP evaluator compares it with a short reference answer using cosine similarity.
4. The similarity score, answer length, and relevant keywords produce a score out of 100 and simple feedback.
5. SQLite saves each answer and the final report calculates the overall average and performance level.

This is an NLP application, not a model-training project. A pretrained MiniLM model converts text into numerical embeddings. Cosine similarity tells how close the user's answer is to the expected answer meaning.

## Optional future upgrades

- Login system and user accounts
- Voice answer input with browser speech recognition
- More roles and a larger question bank
- Optional cloud AI API for dynamic questions (keep the current local question bank as fallback)
