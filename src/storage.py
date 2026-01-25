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
    """Initialize SQLite tables for conversations."""
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
