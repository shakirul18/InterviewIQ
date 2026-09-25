# InterviewIQ

InterviewIQ is an AI-powered interview practice and short-answer evaluation web application. A candidate selects a role, receives interview questions, submits answers, and receives qualitative feedback as **Weak**, **Average**, or **Strong**.

## Research basis

The current evaluation pipeline is a lightweight adaptation inspired by:

**Yaman Kumar, Swati Aggarwal, Debanjan Mahata, Rajiv Ratn Shah, Ponnurangam Kumaraguru, and Roger Zimmermann.**  
*Get IT Scored Using AutoSAS — An Automated System for Scoring Short Answers.* AAAI 2019.

- Official AAAI paper: https://ojs.aaai.org/index.php/AAAI/article/view/5031
- arXiv: https://arxiv.org/abs/2012.11243
- DOI: https://doi.org/10.1609/aaai.v33i01.33019662

> **Note:** InterviewIQ is an **AutoSAS-inspired adaptation**, not the authors' exact original implementation. The project adapts the short-answer scoring idea into a small local model that can be integrated with the existing interview web application.

## Main features

- Role-based interview practice
- Random selection of interview questions
- Automated short-answer evaluation
- Qualitative results: **Weak / Average / Strong**
- Feedback after each submitted answer
- Question-by-question final report
- Interview history
- FastAPI backend
- HTML/CSS/JavaScript frontend
- SQLite database
- Local machine learning model
- No cloud LLM API required for answer evaluation

## Architecture

```text
InterviewIQ/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── questions.py
│   ├── autosas_evaluator.py
│   └── static/
│       ├── index.html
│       ├── app.js
│       └── style.css
├── data/
├── models/
├── train_autosas.py
├── requirements.txt
└── README.md
```

### Evaluation pipeline

The local model uses:

- **1,500 TF-IDF features** from the answer text
- **9 basic linguistic features**
- **RandomForestRegressor** for short-answer score prediction

This gives a **1,509-feature** model input.

The training configuration is:

```text
Maximum local samples : 2500
Target                 : Score1
Target range           : 0–3
Model                  : RandomForestRegressor
Trees                  : 300
random_state           : 42
max_features           : sqrt
min_samples_leaf       : 2
```

The application then converts the internal evaluation into the qualitative labels shown to the candidate.

## Dataset

The training pipeline uses the public **ASAP-SAS** short-answer scoring dataset.

- Hugging Face mirror: https://huggingface.co/datasets/nlpatunt/D_ASAP-SAS
- Kaggle: https://www.kaggle.com/competitions/asap-sas

For local training, the script intentionally limits the dataset to approximately 2,500 samples so that the experiment remains practical on a student laptop.

## Installation

### 1. Clone

```bash
git clone https://github.com/shakirul18/InterviewIQ.git
cd InterviewIQ
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

## Train the model

If `models/autosas_lite.pkl` is not already present:

```powershell
python train_autosas.py
```

The script downloads the public ASAP-SAS training data, selects a small stratified sample, extracts TF-IDF and linguistic features, trains the Random Forest model, and saves:

```text
models/autosas_lite.pkl
```

## Run the web application

From the repository root:

```powershell
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## API endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/roles` | GET | Get available interview roles |
| `/api/interviews` | POST | Start an interview |
| `/api/answers` | POST | Evaluate and save an answer |
| `/api/interviews/{id}/finish` | POST | Finish an interview and generate the report |
| `/api/history` | GET | Get interview history |

The answer endpoint intentionally exposes only qualitative information:

```json
{
  "label": "Strong",
  "feedback": "Good answer. Your response is relevant and covers the main idea clearly."
}
```

Internal model scores and similarity signals are not returned to the frontend.

## Local training result

One local development run of this adaptation produced:

- RMSE: **0.6499**
- MAE: **0.5223**

These are results from this project's local training setup. They are **not** the performance numbers reported by the original AutoSAS paper.

The original paper reported its own results using its own implementation, experimental setup, feature engineering, prompt-wise evaluation, and dataset protocol. Those results should therefore be treated separately from this adaptation.

## Project scope

The project has two distinct layers:

1. **Research/model layer** — a compact AutoSAS-inspired short-answer scoring pipeline trained on public ASAP-SAS data.
2. **Application layer** — InterviewIQ's question bank, interview workflow, FastAPI API, database, UI, feedback presentation, and history/report functionality.

This separation makes it possible to demonstrate how a published research direction can be integrated into a working interview-practice application.

## Limitations

- This is not the original AutoSAS source implementation.
- The local experiment uses a small subset of the public dataset.
- A single compact model is used for the local application.
- The final Weak/Average/Strong labels are application-level qualitative categories, not a replacement for human assessment.
- The system is intended for interview practice, academic demonstration, and research prototyping; it should not be used as a sole high-stakes hiring decision system.

## References

1. Kumar, Y., Aggarwal, S., Mahata, D., Shah, R. R., Kumaraguru, P., & Zimmermann, R. (2019). *Get IT Scored Using AutoSAS — An Automated System for Scoring Short Answers*. Proceedings of the AAAI Conference on Artificial Intelligence, 33(01), 9612–9619. https://doi.org/10.1609/aaai.v33i01.33019662
2. ASAP-SAS public dataset: https://www.kaggle.com/competitions/asap-sas
