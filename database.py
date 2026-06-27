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
        # Maps a notification message (sent to an admin) back to the original
        # user, so that replying to that message in Telegram can be relayed
        # to the right person. Keyed by (admin_id, message_id) since each
        # admin sees their own copy of every notification.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                admin_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (admin_id, message_id)
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


def save_notification(admin_id: int, message_id: int, user_id: int):
    """Remembers that this notification message (sent to this admin) is about this user,
    so a later reply to it can be relayed back to them."""
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        conn.execute(
            "INSERT INTO notifications (admin_id, message_id, user_id) VALUES (?, ?, ?) "
            "ON CONFLICT(admin_id, message_id) DO UPDATE SET user_id = excluded.user_id",
            (admin_id, message_id, user_id),
        )
        conn.commit()


def get_notification_user(admin_id: int, message_id: int) -> Optional[int]:
    """Looks up which user a notification message was about, or None if unknown
    (e.g. it wasn't a tracked notification, or it's since been pruned)."""
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        cur = conn.execute(
            "SELECT user_id FROM notifications WHERE admin_id = ? AND message_id = ?",
            (admin_id, message_id),
        )
        row = cur.fetchone()
        return row[0] if row else None


def prune_old_notifications(keep_days: int = 30):
    """Deletes notification mappings older than keep_days. Cheap to call
    occasionally — the table is tiny (one row per forwarded message)."""
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        conn.execute(
            f"DELETE FROM notifications WHERE created_at < datetime('now', '-{int(keep_days)} days')"
        )
        conn.commit()
