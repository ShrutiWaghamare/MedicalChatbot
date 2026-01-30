"""
SQLite storage utilities for chat history.
"""
from __future__ import annotations

import os
import sqlite3
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chatbot.db")


def get_db_path() -> str:
    """Get database path from env or default."""
    return os.getenv("CHATBOT_DB_PATH", DEFAULT_DB_PATH)


def ensure_db_dir(db_path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    ensure_db_dir(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize SQLite tables for conversations and reactions."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversations_session
            ON conversations (session_id)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                reaction TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                UNIQUE(session_id, message_id)
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_reactions_session
            ON reactions (session_id)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                visited_at TEXT NOT NULL,
                user_agent TEXT,
                referrer TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_visits_session
            ON visits (session_id)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_visits_visited_at
            ON visits (visited_at)
            """
        )
        try:
            conn.execute("ALTER TABLE reactions ADD COLUMN message_content TEXT")
        except sqlite3.OperationalError:
            pass


def insert_message(session_id: str, role: str, content: str, timestamp: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO conversations (session_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, role, content, timestamp),
        )


def fetch_messages(session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    query = "SELECT role, content, timestamp FROM conversations WHERE session_id = ? ORDER BY id ASC"
    params: List[Any] = [session_id]
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def delete_messages(session_id: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))


def insert_reaction(
    session_id: str,
    message_id: str,
    reaction: str,
    timestamp: str,
    message_content: Optional[str] = None,
) -> None:
    """Save or replace reaction for a message (like/dislike). Optionally store message text."""
    content = (message_content or "")[:2000]
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO reactions (session_id, message_id, reaction, timestamp, message_content)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(session_id, message_id) DO UPDATE SET
                reaction = excluded.reaction,
                timestamp = excluded.timestamp,
                message_content = excluded.message_content
            """,
            (session_id, message_id, reaction, timestamp, content),
        )


def delete_reaction(session_id: str, message_id: str) -> None:
    """Remove reaction for a message."""
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM reactions WHERE session_id = ? AND message_id = ?",
            (session_id, message_id),
        )


def fetch_reactions(limit: Optional[int] = 200) -> List[Dict[str, Any]]:
    """Fetch recent reactions (for admin/viewing feedback)."""
    query = """
        SELECT session_id, message_id, reaction, timestamp, message_content
        FROM reactions
        ORDER BY id DESC
        LIMIT ?
    """
    with get_connection() as conn:
        rows = conn.execute(query, (limit,)).fetchall()
    return [dict(row) for row in rows]


def record_visit(
    session_id: str,
    visited_at: str,
    user_agent: Optional[str] = None,
    referrer: Optional[str] = None,
) -> None:
    """Record a visitor page load (one row per visit)."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO visits (session_id, visited_at, user_agent, referrer)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, visited_at, user_agent or "", referrer or ""),
        )


def fetch_visits(limit: Optional[int] = 500) -> List[Dict[str, Any]]:
    """Fetch recent visits for admin/analytics."""
    query = """
        SELECT id, session_id, visited_at, user_agent, referrer
        FROM visits
        ORDER BY id DESC
        LIMIT ?
    """
    with get_connection() as conn:
        rows = conn.execute(query, (limit,)).fetchall()
    return [dict(row) for row in rows]


def get_visit_counts() -> Dict[str, int]:
    """Return total page loads and unique visitors (distinct sessions)."""
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
        unique = conn.execute("SELECT COUNT(DISTINCT session_id) FROM visits").fetchone()[0]
    return {"total_visits": total, "unique_visitors": unique}
