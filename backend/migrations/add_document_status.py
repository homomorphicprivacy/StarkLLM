"""
One-time migration: add `status` and `error_message` columns to the `documents` table.
Defaults status to 'indexed' so all existing documents remain fully functional.
Safe to run multiple times.
"""
import sqlite3
import os

DB_PATH = os.environ.get("SQLITE_PATH", "data/starkllm.db")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"[migration] Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(documents)")
    columns = [row[1] for row in cursor.fetchall()]

    if "status" not in columns:
        print("[migration] Adding 'status' column to 'documents' table...")
        cursor.execute("ALTER TABLE documents ADD COLUMN status TEXT NOT NULL DEFAULT 'indexed'")
        conn.commit()
    else:
        print("[migration] 'status' column already exists — skipping.")

    if "error_message" not in columns:
        print("[migration] Adding 'error_message' column to 'documents' table...")
        cursor.execute("ALTER TABLE documents ADD COLUMN error_message TEXT")
        conn.commit()
    else:
        print("[migration] 'error_message' column already exists — skipping.")

    print("[migration] Done.")
    conn.close()

if __name__ == "__main__":
    migrate()
