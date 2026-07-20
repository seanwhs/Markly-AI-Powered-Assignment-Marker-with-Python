import os
import json
import shutil
import threading
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_FILE = "students.json"
_db_lock = threading.Lock()


def load_db() -> dict:
    """Load the student database from JSON file.

    Returns:
        Dictionary of student records, or empty dict if file missing/corrupted.
    """
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load database: %s", exc)
        return {}


def save_db(db: dict) -> None:
    """Save the student database atomically using temp file + replace.

    Args:
        db: Dictionary of student records to persist.

    Raises:
        TypeError: If db is not a dictionary.
        ValueError: If db cannot be serialized to JSON.
    """
    if not isinstance(db, dict):
        raise TypeError(f"db must be a dict, got {type(db).__name__}")

    # Validate JSON serializability before writing
    try:
        json.dumps(db)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Database is not JSON serializable: {exc}")

    if os.path.exists(DB_FILE):
        backup = DB_FILE + ".bak"
        try:
            shutil.copy2(DB_FILE, backup)
        except OSError as exc:
            logger.warning("Failed to create backup: %s", exc)

    tmp = DB_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)
    try:
        os.chmod(tmp, 0o600)
    except Exception:
        pass
    os.replace(tmp, DB_FILE)


def add_record(student: str, subject: str, grade: str, feedback: str) -> None:
    """Append a grading record to a student's history.

    Args:
        student: Normalized student name (lowercase + stripped).
        subject: Subject name.
        grade: Grade string (e.g., "8/10").
        feedback: Full feedback text.

    Raises:
        ValueError: If student name is empty.
    """
    if not student or not student.strip():
        raise ValueError("Student name cannot be empty")

    with _db_lock:
        db = load_db()
        key = student.strip().lower()
        if key not in db:
            db[key] = {"history": []}

        db[key]["history"].append({
            "subject": subject,
            "grade": grade,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        })
        save_db(db)
        logger.info("Recorded grade for %s: %s = %s", student, subject, grade)


def get_student_history(name: str) -> str:
    """Retrieve formatted grading history for a student.

    Args:
        name: Normalized student name (lowercase + stripped).

    Returns:
        Formatted string of last 5 records, or "No previous records."
    """
    if not name or not name.strip():
        return "No previous records."

    db = load_db()
    key = name.strip().lower()
    if key not in db:
        return "No previous records."

    return "\n".join([
        f"- {h['subject']} ({h['timestamp'][:10]}): {h['grade']}"
        for h in db[key]["history"][-5:]
    ])