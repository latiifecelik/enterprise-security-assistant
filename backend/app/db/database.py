"""
db/database.py
--------------
SQLite connection management.

We use Python's built-in sqlite3 — no ORM, no extra dependency.
A context-manager helper makes it easy to get a connection anywhere.
Foreign-key enforcement and WAL mode are enabled for every connection.
"""

import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


def _make_connection(db_path: str) -> sqlite3.Connection:
    """Open a SQLite connection with sensible defaults."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row          # rows behave like dicts
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # better concurrent read performance
    return conn


@contextmanager
def get_db():
    """
    Yield a SQLite connection for use inside a `with` block.

    Usage:
        with get_db() as conn:
            conn.execute("SELECT ...")
    """
    conn = _make_connection(settings.DATABASE_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Create all tables if they do not already exist.
    Safe to call on every startup — uses CREATE TABLE IF NOT EXISTS.
    """
    schema_sql = """
    -- ── documents ─────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS documents (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        filename    TEXT    NOT NULL,
        file_type   TEXT    NOT NULL,
        title       TEXT    NOT NULL,
        file_size   INTEGER NOT NULL DEFAULT 0,
        chunk_count INTEGER NOT NULL DEFAULT 0,
        created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    CREATE INDEX IF NOT EXISTS idx_documents_created_at
        ON documents (created_at);

    -- ── chunks ────────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS chunks (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        chunk_index INTEGER NOT NULL,
        content     TEXT    NOT NULL,
        page_number INTEGER,
        char_start  INTEGER,
        char_end    INTEGER,
        created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    CREATE INDEX IF NOT EXISTS idx_chunks_document_id
        ON chunks (document_id);

    -- ── conversations ─────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS conversations (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        title      TEXT    NOT NULL DEFAULT 'New Chat',
        created_at TEXT    NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    -- ── messages ──────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS messages (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
        role            TEXT    NOT NULL CHECK (role IN ('user', 'assistant')),
        content         TEXT    NOT NULL,
        -- JSON-encoded retrieval metadata (sources, scores) for assistant msgs
        retrieval_meta  TEXT,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
        ON messages (conversation_id);
    """

    with get_db() as conn:
        conn.executescript(schema_sql)

    logger.info("Database initialised at %s", settings.DATABASE_PATH)
