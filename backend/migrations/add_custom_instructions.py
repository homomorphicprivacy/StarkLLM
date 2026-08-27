"""
One-time migration: add `profile_context` and `custom_instructions` columns to the `users` table.
Safe to run multiple times — checks if columns already exist first.
"""
import sqlite3
import os

DB_PATH = os.environ.get("SQLITE_PATH", "data/starkllm.db")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"[migration] Database not found at {DB_PATH}, maybe it's not created yet.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check existing columns
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]

    if "profile_context" not in columns:
        print("[migration] Adding 'profile_context' column to 'users' table...")
        cursor.execute("ALTER TABLE users ADD COLUMN profile_context TEXT")
        conn.commit()
    else:
        print("[migration] 'profile_context' column already exists — skipping.")

    if "custom_instructions" not in columns:
        print("[migration] Adding 'custom_instructions' column to 'users' table...")
        cursor.execute("ALTER TABLE users ADD COLUMN custom_instructions TEXT")
        conn.commit()
    else:
        print("[migration] 'custom_instructions' column already exists — skipping.")

    print("[migration] Done.")
    conn.close()

if __name__ == "__main__":
    migrate()
