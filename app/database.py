import sqlite3
from pathlib import Path
from datetime import datetime

DATABASE_PATH = Path(__file__).parent / "interviewiq.db"


def connection():
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    return db


def initialize_database():
    with connection() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            overall_score REAL
        );
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interview_id INTEGER NOT NULL,
            question_index INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            score REAL NOT NULL,
            similarity REAL NOT NULL,
            feedback TEXT NOT NULL,
            FOREIGN KEY(interview_id) REFERENCES interviews(id)
        );
        """)


def create_interview(role: str) -> int:
    with connection() as db:
        cursor = db.execute("INSERT INTO interviews (role, started_at) VALUES (?, ?)", (role, datetime.now().isoformat(timespec="seconds")))
        return cursor.lastrowid


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
