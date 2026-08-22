import json
import sqlite3
from datetime import datetime
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "interviewiq.db"


def connection():
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    return db


def initialize_database():
    with connection() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL,
            started_at TEXT NOT NULL, completed_at TEXT, overall_score REAL
        );
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, interview_id INTEGER NOT NULL,
            question_index INTEGER NOT NULL, question TEXT NOT NULL, answer TEXT NOT NULL,
            score REAL NOT NULL, similarity REAL NOT NULL, feedback TEXT NOT NULL,
            FOREIGN KEY(interview_id) REFERENCES interviews(id)
        );
        CREATE TABLE IF NOT EXISTS interview_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, interview_id INTEGER NOT NULL,
            question_index INTEGER NOT NULL, question TEXT NOT NULL,
            reference_answer TEXT NOT NULL, keywords TEXT NOT NULL,
            FOREIGN KEY(interview_id) REFERENCES interviews(id),
            UNIQUE(interview_id, question_index)
        );
        """)


def create_interview(role: str) -> int:
    with connection() as db:
        cursor = db.execute("INSERT INTO interviews (role, started_at) VALUES (?, ?)", (role, datetime.now().isoformat(timespec="seconds")))
        return cursor.lastrowid


def save_interview_questions(interview_id: int, questions: list[dict]):
    with connection() as db:
        db.executemany(
            """INSERT INTO interview_questions (interview_id, question_index, question, reference_answer, keywords)
               VALUES (?, ?, ?, ?, ?)""",
            [(interview_id, i, item["question"], item["reference"], json.dumps(item["keywords"])) for i, item in enumerate(questions)],
        )


def get_interview_question(interview_id: int, question_index: int):
    with connection() as db:
        row = db.execute("SELECT * FROM interview_questions WHERE interview_id = ? AND question_index = ?", (interview_id, question_index)).fetchone()
        if not row:
            return None
        item = dict(row)
        item["keywords"] = json.loads(item["keywords"])
        return item


def save_answer(interview_id, question_index, question, answer, score, similarity, feedback):
    with connection() as db:
        db.execute("""INSERT INTO answers (interview_id, question_index, question, answer, score, similarity, feedback)
                      VALUES (?, ?, ?, ?, ?, ?, ?)""", (interview_id, question_index, question, answer, score, similarity, feedback))


def finish_interview(interview_id: int):
    with connection() as db:
        scores = db.execute("SELECT score FROM answers WHERE interview_id = ?", (interview_id,)).fetchall()
        average = round(sum(row["score"] for row in scores) / len(scores), 1) if scores else 0
        db.execute("UPDATE interviews SET completed_at = ?, overall_score = ? WHERE id = ?", (datetime.now().isoformat(timespec="seconds"), average, interview_id))
        return average


def interview_report(interview_id: int):
    with connection() as db:
        interview = db.execute("SELECT * FROM interviews WHERE id = ?", (interview_id,)).fetchone()
        answers = db.execute("SELECT * FROM answers WHERE interview_id = ? ORDER BY question_index", (interview_id,)).fetchall()
        return dict(interview) if interview else None, [dict(row) for row in answers]


def history():
    with connection() as db:
        rows = db.execute("SELECT id, role, started_at, overall_score FROM interviews WHERE completed_at IS NOT NULL ORDER BY id DESC LIMIT 20").fetchall()
        return [dict(row) for row in rows]
