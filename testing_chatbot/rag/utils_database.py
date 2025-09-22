import sqlite3


# ================== DATABASE (SQLite) ==================
def save_captions_to_db(thread_id: str, captions: str):
    """
    Save transcript captions into database.
    """
    conn = sqlite3.connect(database="ragDatabase.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transcripts (
        thread_id TEXT PRIMARY KEY,
        captions TEXT
    )
    """)
    cursor.execute("""
    INSERT OR REPLACE INTO transcripts (thread_id, captions) VALUES (?, ?)
    """, (thread_id, captions))
    conn.commit()
    conn.close()


def save_youtube_url_to_db(thread_id: str, youtube_url: str):
    """
    Save YouTube video URL for a thread.
    """
    conn = sqlite3.connect(database="ragDatabase.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS url (
        thread_id TEXT PRIMARY KEY,
        youtube_url TEXT,
        FOREIGN KEY(thread_id) REFERENCES transcripts(thread_id)
    )
    """)
    cursor.execute("""
    INSERT OR REPLACE INTO url (thread_id, youtube_url) VALUES (?, ?)
    """, (thread_id, youtube_url))
    conn.commit()
    conn.close()


def load_captions_from_db(thread_id: str) -> str | None:
    """
    Load transcript captions for a thread.
    """
    conn = sqlite3.connect(database="ragDatabase.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT captions FROM transcripts WHERE thread_id = ?", (thread_id,))
    row = cursor.fetchone()
    return row[0] if row else None


def load_url_from_db(thread_id: str) -> str | None:
    """
    Load YouTube URL for a thread.
    """
    conn = sqlite3.connect(database="ragDatabase.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT youtube_url FROM url WHERE thread_id = ?", (thread_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def delete_all_threads_from_db():
    """
    Delete all chat threads & related data from database.
    """
    try:
        conn = sqlite3.connect(r"C:\Users\prana\Desktop\PROJECTS\tubetalk.ai\ragDataBase.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table_name in tables:
            cursor.execute(f"DELETE FROM {table_name[0]};")
        conn.commit()
        conn.close()
        print("✅ All threads deleted successfully.")
    except Exception as e:
        print("❌ Error while deleting threads:", e)


def check_is_thread_empty_db(conn, thread_id: str) -> bool:
    """
    Check if thread has no checkpoints.
    """
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM checkpoints WHERE thread_id = ?;", (thread_id,))
        count = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        return True  # Table not created yet
    return count == 0
