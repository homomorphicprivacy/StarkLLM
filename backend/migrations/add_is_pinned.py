"""
One-time migration: add `is_pinned` column to the `chats` table.
Safe to run multiple times — checks if column already exists first.
"""
import sqlite3
import os

DB_PATH = os.environ.get("SQLITE_PATH", "/app/data/starkllm.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check existing columns
    cursor.execute("PRAGMA table_info(chats)")
    columns = [row[1] for row in cursor.fetchall()]

    if "is_pinned" not in columns:
        print("[migration] Adding 'is_pinned' column to 'chats' table...")
        cursor.execute("ALTER TABLE chats ADD COLUMN is_pinned INTEGER NOT NULL DEFAULT 0")
        conn.commit()
        print("[migration] Done.")
    else:
        print("[migration] 'is_pinned' column already exists — skipping.")

    conn.close()

if __name__ == "__main__":
    migrate()
