"""
db/repository.py
----------------
Data-access layer — all SQL queries live here.

Functions accept an explicit sqlite3.Connection so they can be
composed inside a single transaction when needed.
Return values are plain Python dicts or lists of dicts.
"""

import json
import sqlite3
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Documents
# ═══════════════════════════════════════════════════════════════════════════

def insert_document(
    conn: sqlite3.Connection,
    filename: str,
    file_type: str,
    title: str,
    file_size: int,
) -> int:
    """Insert a new document record and return its generated id."""
    cur = conn.execute(
        """
        INSERT INTO documents (filename, file_type, title, file_size)
        VALUES (?, ?, ?, ?)
        """,
        (filename, file_type, title, file_size),
    )
    return cur.lastrowid


def update_document_chunk_count(
    conn: sqlite3.Connection, document_id: int, chunk_count: int
) -> None:
    conn.execute(
        "UPDATE documents SET chunk_count = ? WHERE id = ?",
        (chunk_count, document_id),
    )


def get_document(
    conn: sqlite3.Connection, document_id: int
) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        "SELECT * FROM documents WHERE id = ?", (document_id,)
    ).fetchone()
    return dict(row) if row else None


def list_documents(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM documents ORDER BY created_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def delete_document(conn: sqlite3.Connection, document_id: int) -> bool:
    """Delete document and its chunks (ON DELETE CASCADE handles chunks)."""
    cur = conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    return cur.rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════
# Chunks
# ═══════════════════════════════════════════════════════════════════════════

def insert_chunks(
    conn: sqlite3.Connection,
    document_id: int,
    chunks: List[Dict[str, Any]],
) -> None:
    """Bulk-insert all chunks for a document."""
    conn.executemany(
        """
        INSERT INTO chunks
            (document_id, chunk_index, content, page_number, char_start, char_end)
        VALUES
            (:document_id, :chunk_index, :content, :page_number, :char_start, :char_end)
        """,
        [
            {
                "document_id": document_id,
                "chunk_index": c["chunk_index"],
                "content": c["content"],
                "page_number": c.get("page_number"),
                "char_start": c.get("char_start"),
                "char_end": c.get("char_end"),
            }
            for c in chunks
        ],
    )


def get_all_chunks(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Return every chunk with its document filename — used to build the TF-IDF index."""
    rows = conn.execute(
        """
        SELECT c.id, c.document_id, c.chunk_index, c.content,
               c.page_number, c.char_start, c.char_end,
               d.filename, d.title
        FROM   chunks c
        JOIN   documents d ON d.id = c.document_id
        ORDER  BY c.document_id, c.chunk_index
        """
    ).fetchall()
    return [dict(r) for r in rows]


def get_chunks_for_document(
    conn: sqlite3.Connection, document_id: int
) -> List[Dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index",
        (document_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def delete_chunks_for_document(
    conn: sqlite3.Connection, document_id: int
) -> None:
    conn.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))


# ═══════════════════════════════════════════════════════════════════════════
# Conversations
# ═══════════════════════════════════════════════════════════════════════════

def insert_conversation(conn: sqlite3.Connection, title: str = "New Chat") -> int:
    cur = conn.execute(
        "INSERT INTO conversations (title) VALUES (?)", (title,)
    )
    return cur.lastrowid


def list_conversations(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM conversations ORDER BY updated_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_conversation(
    conn: sqlite3.Connection, conversation_id: int
) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
    ).fetchone()
    return dict(row) if row else None


def update_conversation_title(
    conn: sqlite3.Connection, conversation_id: int, title: str
) -> None:
    conn.execute(
        """
        UPDATE conversations
        SET title = ?, updated_at = datetime('now')
        WHERE id = ?
        """,
        (title, conversation_id),
    )


def touch_conversation(conn: sqlite3.Connection, conversation_id: int) -> None:
    """Update the updated_at timestamp (called after each new message)."""
    conn.execute(
        "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
        (conversation_id,),
    )


def delete_conversation(conn: sqlite3.Connection, conversation_id: int) -> bool:
    cur = conn.execute(
        "DELETE FROM conversations WHERE id = ?", (conversation_id,)
    )
    return cur.rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════
# Messages
# ═══════════════════════════════════════════════════════════════════════════

def insert_message(
    conn: sqlite3.Connection,
    conversation_id: int,
    role: str,
    content: str,
    retrieval_meta: Optional[Dict] = None,
) -> int:
    meta_json = json.dumps(retrieval_meta) if retrieval_meta else None
    cur = conn.execute(
        """
        INSERT INTO messages (conversation_id, role, content, retrieval_meta)
        VALUES (?, ?, ?, ?)
        """,
        (conversation_id, role, content, meta_json),
    )
    return cur.lastrowid


def list_messages(
    conn: sqlite3.Connection, conversation_id: int
) -> List[Dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at",
        (conversation_id,),
    ).fetchall()
    results = []
    for row in rows:
        d = dict(row)
        # Parse retrieval_meta back from JSON if present
        if d.get("retrieval_meta"):
            try:
                d["retrieval_meta"] = json.loads(d["retrieval_meta"])
            except json.JSONDecodeError:
                d["retrieval_meta"] = None
        results.append(d)
    return results


# ═══════════════════════════════════════════════════════════════════════════
# Stats
# ═══════════════════════════════════════════════════════════════════════════

def get_stats(conn: sqlite3.Connection) -> Dict[str, int]:
    doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    conv_count = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
    return {
        "document_count": doc_count,
        "chunk_count": chunk_count,
        "conversation_count": conv_count,
    }
