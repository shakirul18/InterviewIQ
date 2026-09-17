import random
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import database
from .evaluator import evaluate_answer
from .questions import get_questions, get_roles


# ============================================================
# InterviewIQ FastAPI Application
# ============================================================

app = FastAPI(
    title="InterviewIQ",
    version="2.0.0"
)


# ============================================================
# Static Files
# ============================================================

static_path = Path(__file__).parent / "static"

app.mount(
    "/static",
    StaticFiles(directory=static_path),
    name="static"
)


# ============================================================
# Request Models
# ============================================================

class StartRequest(BaseModel):
    role: str


class AnswerRequest(BaseModel):
    interview_id: int
    question_index: int = Field(ge=0)
    answer: str


# ============================================================
# Internal Label Helpers
#
# Score is kept internally because the database currently
# stores the numeric evaluation value.
#
# IMPORTANT:
# These values are NOT exposed to the frontend.
# ============================================================

def _label_from_score(score):
    try:
        score = float(score)
    except (TypeError, ValueError):
        return "Weak"

    if score >= 75:
        return "Strong"

    if score >= 25:
        return "Average"

    return "Weak"


def _session_label(answers):
    if not answers:
        return "Weak"

    scores = []

    for answer in answers:
        try:
            scores.append(float(answer.get("score", 0)))
        except (TypeError, ValueError):
            scores.append(0.0)

    if not scores:
        return "Weak"

    average_score = sum(scores) / len(scores)

    return _label_from_score(average_score)


# ============================================================
# Startup
# ============================================================

@app.on_event("startup")
def startup():
    database.initialize_database()


# ============================================================
# Home Page
# ============================================================

@app.get("/")
def home():
    from fastapi.responses import FileResponse

    return FileResponse(
        static_path / "index.html"
    )


# ============================================================
# Roles
# ============================================================

@app.get("/api/roles")
def roles():
    return {
        "roles": get_roles()
    }


# ============================================================
# Start New Interview
# ============================================================

@app.post("/api/interviews")
def start_interview(data: StartRequest):

    question_bank = get_questions(data.role)

    if not question_bank:
        raise HTTPException(
            status_code=404,
            detail="Unknown job role"
        )

    interview_id = database.create_interview(
        data.role
    )

    questions = random.sample(
        question_bank,
        k=min(5, len(question_bank))
    )

    database.save_interview_questions(
        interview_id,
        questions
    )

    return {
        "interview_id": interview_id,
        "role": data.role,
        "questions": [
            {
                "index": i,
                "question": q["question"]
            }
            for i, q in enumerate(questions)
        ]
    }


# ============================================================
# Submit Answer
# ============================================================

@app.post("/api/answers")
def submit_answer(data: AnswerRequest):

    # --------------------------------------------------------
    # Validate interview
    # --------------------------------------------------------

    interview, _ = database.interview_report(
        data.interview_id
    )

    if not interview:
        raise HTTPException(
            status_code=404,
            detail="Interview not found"
        )


    # --------------------------------------------------------
    # Validate question
    # --------------------------------------------------------

    item = database.get_interview_question(
        data.interview_id,
        data.question_index
    )

    if not item:
        raise HTTPException(
            status_code=400,
            detail="Invalid question index"
        )


    # --------------------------------------------------------
    # Validate answer text
    # --------------------------------------------------------

    answer_text = data.answer.strip()

    if not answer_text:
        raise HTTPException(
            status_code=400,
            detail="Answer cannot be empty"
        )


    # --------------------------------------------------------
    # AI Evaluation
    # --------------------------------------------------------

    result = evaluate_answer(
        answer_text,
        item["question"],
        item["reference_answer"],
        item["keywords"]
    )


    # --------------------------------------------------------
    # Save internal result
    #
    # The database still stores score because the existing
    # database structure requires it.
    #
    # Score is NOT returned to the frontend.
    # --------------------------------------------------------

    database.save_answer(
        data.interview_id,
        data.question_index,
        item["question"],
        answer_text,
        result["score"],
        0.0,
        result["feedback"]
    )


    # --------------------------------------------------------
    # FRONTEND RESPONSE
    #
    # Only these two fields are exposed.
    #
    # No score
    # No similarity
    # No confidence
    # No method
    # --------------------------------------------------------

    return {
        "label": result["label"],
        "feedback": result["feedback"]
    }


# ============================================================
# Finish Interview
# ============================================================

@app.post("/api/interviews/{interview_id}/finish")
def finish(interview_id: int):

    interview, answers = database.interview_report(
        interview_id
    )

    if not interview:
        raise HTTPException(
            status_code=404,
            detail="Interview not found"
        )

    if not answers:
        raise HTTPException(
            status_code=400,
            detail="Submit at least one answer first"
        )


    # Mark interview as finished
    database.finish_interview(
        interview_id
    )


    # Get updated interview data
    interview, answers = database.interview_report(
        interview_id
    )


    # Calculate final category internally
    session_label = _session_label(
        answers
    )


    # --------------------------------------------------------
    # Clean question-by-question results
    # --------------------------------------------------------

    clean_answers = []

    for answer in answers:

        clean_answers.append({
            "question": answer["question"],
            "label": _label_from_score(
                answer["score"]
            ),
            "feedback": answer["feedback"]
        })


    # --------------------------------------------------------
    # Frontend receives ONLY categories and feedback.
    # --------------------------------------------------------

    return {
        "role": interview["role"],
        "label": session_label,
        "answers": clean_answers
    }


# ============================================================
# Practice History
# ============================================================

@app.get("/api/history")
def get_history():

    history = database.history()

    return {
        "history": [
            {
                "role": item["role"],
                "started_at": item["started_at"],
                "label": _label_from_score(
                    item["overall_score"]
                )
            }
            for item in history
        ]
    }