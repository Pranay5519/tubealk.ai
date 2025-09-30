import re
import sqlite3
import json
from datetime import datetime
from typing import Optional, Any
from testing_quiz.model_quiz import QuizList
# ================== UTILITIES ==================
def get_embed_url(url: str) -> str:
    """Convert any YouTube URL into an embeddable format."""
    match = re.search(r"v=([^&]+)", url)
    if match:
        return f"https://www.youtube.com/embed/{match.group(1)}"
    match = re.search(r"youtu\.be/([^?&]+)", url)
    if match:
        return f"https://www.youtube.com/embed/{match.group(1)}"
    if "embed" in url:
        return url
    return url


def save_quiz_to_db(thread_id: str, quiz: str):
    """
    Save quiz into database.
    """
    conn = sqlite3.connect(database="ragDatabase.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # ✅ Create the correct table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quizes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id TEXT,
        quiz TEXT,
        created_at TIMESTAMP
    )
    """)
    
    # ✅ Insert into the correct table
    cursor.execute(
        "INSERT INTO quizes (thread_id, quiz, created_at) VALUES (?, ?, ?)",
        (thread_id, quiz, datetime.now())
    )
    
    conn.commit()
    conn.close()


def load_quiz_from_db(thread_id: str) -> Optional[QuizList]:
    """
    Load quiz from the database using thread_id.
    Returns a QuizList object if found, else None.
    """
    conn = sqlite3.connect(database="ragDatabase.db", check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT quiz FROM quizes WHERE thread_id = ? ORDER BY created_at DESC LIMIT 1",
        (thread_id,)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        try:
            data = json.loads(result[0])  # convert string to dict
            return QuizList.model_validate(data)  # convert dict to QuizList object
        except Exception as e:
            print("Error loading QuizList from DB:", e)
            return None
    return None


# ✅ Test saving
save_quiz_to_db("random_thread_id", json.dumps({"sample": "quiz_data"}))