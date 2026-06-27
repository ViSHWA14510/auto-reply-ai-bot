"""SQLite database layer for storing bot users."""

import sqlite3
from contextlib import closing
from typing import Optional, List

from config import DATABASE_PATH


def init_db():
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()


def add_user(user_id: int, username: Optional[str], first_name: Optional[str]) -> bool:
    """Insert a user if not already present. Returns True if this is a brand-new user."""
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        cur = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        if cur.fetchone():
            return False
        conn.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name),
        )
        conn.commit()
        return True


def get_all_user_ids() -> List[int]:
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        cur = conn.execute("SELECT user_id FROM users")
        return [row[0] for row in cur.fetchall()]


def get_user_count() -> int:
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM users")
        return cur.fetchone()[0]


def remove_user(user_id: int):
    """Remove a user — used during broadcast cleanup if they blocked the bot."""
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        cur = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else default


def set_setting(key: str, value: str):
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        conn.commit()


def is_admin_online() -> bool:
    """Defaults to True (online) until the admin explicitly sets /offline."""
    return get_setting("admin_status", "online") == "online"


def set_admin_status(status: str):
    """status should be 'online' or 'offline'."""
    set_setting("admin_status", status)
