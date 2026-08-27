"""
One-time migration: add generation settings columns to the `users` table.
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

    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]

    new_cols = {
        "default_model": "TEXT",
        "temperature": "REAL",
        "top_p": "REAL",
        "max_tokens": "INTEGER"
    }

    for col, dtype in new_cols.items():
        if col not in columns:
            print(f"[migration] Adding '{col}' column to 'users' table...")
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {dtype}")
            conn.commit()
        else:
            print(f"[migration] '{col}' column already exists — skipping.")

    print("[migration] Done.")
    conn.close()

if __name__ == "__main__":
    migrate()
