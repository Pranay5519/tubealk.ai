import sqlite3
import json
from datetime import datetime

# Connect to SQLite
conn = sqlite3.connect("ragDatabase.db", check_same_thread=False)
cursor = conn.cursor()

# Create table for storing transcript extractions per thread
cursor.execute("""
CREATE TABLE IF NOT EXISTS transcript_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id TEXT,
    transcript TEXT,
    output_json TEXT,
    created_at TIMESTAMP
)
""")
#conn.commit()
cursor.execute("""
CREATE TABLE IF NOT EXISTS summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id TEXT,
    summary TEXT,
    created_at TIMESTAMP
)
""")
conn.commit()
conn.close()