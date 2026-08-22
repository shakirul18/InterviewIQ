from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import database
from .evaluator import evaluate_answer
from .questions import get_questions, get_roles

app = FastAPI(title="InterviewIQ", version="1.0.0")
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")


class StartRequest(BaseModel):
    role: str


class AnswerRequest(BaseModel):
    interview_id: int
    question_index: int = Field(ge=0)
    answer: str


@app.on_event("startup")
def startup():
    database.initialize_database()


@app.get("/")
def home():
    from fastapi.responses import FileResponse
    return FileResponse(static_path / "index.html")


@app.get("/api/roles")
def roles():
    return {"roles": get_roles()}


@app.post("/api/interviews")
def start_interview(data: StartRequest):
    questions = get_questions(data.role)
    if not questions:
        raise HTTPException(status_code=404, detail="Unknown job role")
    interview_id = database.create_interview(data.role)
    return {"interview_id": interview_id, "role": data.role, "questions": [{"index": i, "question": q["question"]} for i, q in enumerate(questions)]}


@app.post("/api/answers")
def submit_answer(data: AnswerRequest):
    interview, _ = database.interview_report(data.interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    questions = get_questions(interview["role"])
    if data.question_index >= len(questions):
        raise HTTPException(status_code=400, detail="Invalid question index")
    item = questions[data.question_index]
    result = evaluate_answer(data.answer, item["reference"], item["keywords"])
    database.save_answer(data.interview_id, data.question_index, item["question"], data.answer.strip(), result["score"], result["similarity"], result["feedback"])
    return result


@app.post("/api/interviews/{interview_id}/finish")
def finish(interview_id: int):
    interview, answers = database.interview_report(interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if not answers:
        raise HTTPException(status_code=400, detail="Submit at least one answer first")
    database.finish_interview(interview_id)
    interview, answers = database.interview_report(interview_id)
    score = interview["overall_score"]
    level = "Excellent" if score >= 75 else "Good" if score >= 55 else "Needs practice"
    return {"interview": interview, "answers": answers, "level": level}


@app.get("/api/history")
def get_history():
    return {"history": database.history()}
