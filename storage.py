import os
import json
from datetime import datetime

DB_FILE = "students.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)

def add_record(student, subject, grade, feedback):
    db = load_db()
    if student not in db:
        db[student] = {"history": []}

    db[student]["history"].append({
        "subject": subject,
        "grade": grade,
        "feedback": feedback,
        "timestamp": datetime.now().isoformat()
    })
    save_db(db)

def get_student_history(name):
    db = load_db()
    if name not in db:
        return "No previous records."

    return "\n".join([
        f"- {h['subject']} ({h['timestamp'][:10]}): {h['grade']}"
        for h in db[name]["history"][-5:]
    ])