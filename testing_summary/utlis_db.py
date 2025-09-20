import sqlite3
from typing import Optional
from pydantic import BaseModel, Field

# Assume these are already defined
class Subtopic(BaseModel):
    subtopic: str
    timestamp: float
    importance: Optional[str] = None

class MainTopic(BaseModel):
    topic: str
    timestamp: float
    subtopics: list[Subtopic]

class TopicsOutput(BaseModel):
    main_topics: list[MainTopic]

# ----------------------------
# Function to fetch and format
# ----------------------------
def extract_topics_from_db(thread_id: str) -> str:
    """
    Fetch TopicsOutput from DB using thread_id and return a nicely formatted string.
    """
    formatted_str = ""
    conn = sqlite3.connect("ragDatabase.db", check_same_thread=False)
    cursor = conn.cursor()

    # Fetch the latest output_json for this thread
    cursor.execute("SELECT output_json FROM transcript_topics WHERE thread_id=? ORDER BY id DESC", (thread_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return f"No topics found for thread_id '{thread_id}'."

    # Restore Pydantic object from JSON
    output_json = row[0]
    try:
        topics_output = TopicsOutput.model_validate_json(output_json)
    except Exception as e:
        return f"Error parsing JSON from DB: {e}"

    # Nicely format main topics and subtopics
    for i, main_topic in enumerate(topics_output.main_topics, 1):
        formatted_str += f"\n{i}: {main_topic.topic}  ⏰ {main_topic.timestamp}\n"
        #formatted_str += "----------------------------------------------------\n"
        for j, sub in enumerate(main_topic.subtopics, 1):
            importance = f" [{sub.importance}]" if sub.importance else ""
            formatted_str += f"   {i}.{j}: {sub.subtopic}  ⏰ {sub.timestamp}{importance}\n"
        #formatted_str += "====================================================\n"

    return formatted_str

import sqlite3
from datetime import datetime


def save_summary_to_db(thread_id: str, summary_text: str):
    """
    Save a summary string for a given thread_id into the summary table.
    """
    # Open connection
    conn = sqlite3.connect("ragDatabase.db", timeout=30, check_same_thread=False)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id TEXT,
        summary TEXT,
        created_at TIMESTAMP
    )
    """)
    
    # Insert the summary
    cursor.execute(
        "INSERT INTO summary (thread_id, summary, created_at) VALUES (?, ?, ?)",
        (thread_id, summary_text, datetime.now())
    )
    
    # Commit and close
    conn.commit()
    conn.close()

import sqlite3

def get_summary_if_exists(thread_id: str) -> str | None:
    """
    Check if a summary for the given thread_id exists in the database.
    Returns the summary string if found, else None.
    """
    conn = sqlite3.connect("ragDatabase.db", check_same_thread=False)
    cursor = conn.cursor()

    # Query for the summary with the given thread_id
    cursor.execute("SELECT summary FROM summary WHERE thread_id=?", (thread_id,))
    row = cursor.fetchall()
    conn.close()

    if row:
        return row[0][0]  # return the summary string

    return None
