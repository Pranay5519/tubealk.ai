import sqlite3
import json
from datetime import datetime

# ================== DATABASE (SQLite) ==================
def save_topics_to_db(thread_id: str, topics: str):
    """
    Save transcript captions into database.
    """
    conn = sqlite3.connect(database="ragDatabase.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transcript_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id TEXT,
        output_json TEXT,
        created_at TIMESTAMP
    )
    """)
    cursor.execute(
        "INSERT INTO transcript_topics (thread_id ,output_json, created_at) VALUES (?, ?, ?)",
        (thread_id, topics, datetime.now())
    )
    conn.commit()
    conn.close()
   