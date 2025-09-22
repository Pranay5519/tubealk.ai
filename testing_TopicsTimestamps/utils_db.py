import sqlite3
import json
from datetime import datetime
from model import TopicsOutput, parser  
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
   
import sqlite3
import json
from typing import Optional, Any

def load_topics_from_db(thread_id: str) -> Optional[TopicsOutput]:
    """
    Load transcript topics from the database using thread_id.
    Returns a TopicsOutput object if found, else None.
    """
    conn = sqlite3.connect(database="ragDatabase.db", check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT output_json FROM transcript_topics WHERE thread_id = ? ORDER BY created_at DESC LIMIT 1",
        (thread_id,)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        try:
            data = json.loads(result[0])  # convert string to dict
            return TopicsOutput.model_validate(data)  # convert dict to TopicsOutput object
        except Exception as e:
            print("Error loading TopicsOutput from DB:", e)
            return None
    return None

