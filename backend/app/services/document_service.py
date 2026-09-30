"""
services/document_service.py
-----------------------------
Business logic for document ingestion.

This layer sits between the API handlers and the database/RAG modules.
It keeps the API thin and the logic testable.

Flow:
  upload → validate → extract text → chunk → store → rebuild index
"""

import hashlib
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.db import repository
from app.db.database import get_db
from app.rag import chunker
from app.rag.retriever import retriever

logger = logging.getLogger(__name__)


# ── Text extraction ──────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: Path) -> List[Dict[str, Any]]:
    """
    Extract text from a PDF, returning one dict per page.
    Uses pdfplumber for reliable text extraction.
    """
    import pdfplumber

    pages = []
    with pdfplumber.open(str(file_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            text = _normalise_text(text)
            if text.strip():
                pages.append({"page_number": i, "text": text})
    return pages


def extract_text_from_txt(file_path: Path) -> List[Dict[str, Any]]:
    """Read plain text files."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    text = _normalise_text(text)
    return [{"page_number": None, "text": text}] if text.strip() else []


def extract_text_from_markdown(file_path: Path) -> List[Dict[str, Any]]:
    """Read Markdown files as plain text (keep structure as-is)."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    text = _normalise_text(text)
    return [{"page_number": None, "text": text}] if text.strip() else []


def extract_text_from_docx(file_path: Path) -> List[Dict[str, Any]]:
    """Extract text from a DOCX file using python-docx."""
    from docx import Document as DocxDocument

    doc = DocxDocument(str(file_path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = "\n\n".join(paragraphs)
    text = _normalise_text(text)
    return [{"page_number": None, "text": text}] if text.strip() else []


def _normalise_text(text: str) -> str:
    """
    Clean up extracted text:
      - collapse multiple blank lines to at most two
      - strip leading/trailing whitespace
    """
    import re
    # Normalise line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse runs of 3+ newlines to two
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ── Dispatcher ───────────────────────────────────────────────────────────

def extract_pages(file_path: Path, file_type: str) -> List[Dict[str, Any]]:
    """Route extraction to the correct handler based on file type."""
    extractors = {
        ".pdf":  extract_text_from_pdf,
        ".txt":  extract_text_from_txt,
        ".md":   extract_text_from_markdown,
        ".docx": extract_text_from_docx,
    }
    fn = extractors.get(file_type.lower())
    if fn is None:
        raise ValueError(f"Unsupported file type: {file_type}")
    return fn(file_path)


# ── Main ingestion function ───────────────────────────────────────────────

def ingest_document(
    file_path: Path,
    original_filename: str,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Full document ingestion pipeline:
      1. Validate file
      2. Determine file type
      3. Extract text (per page when possible)
      4. Chunk the text
      5. Store in SQLite
      6. Rebuild TF-IDF index

    Returns a summary dict describing the ingested document.
    """
    t_start = time.perf_counter()
    file_type = Path(original_filename).suffix.lower()

    if file_type not in settings.ALLOWED_EXTENSIONS:
        raise ValueError(
            f"File type '{file_type}' is not supported. "
            f"Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    file_size = file_path.stat().st_size
    doc_title = title or Path(original_filename).stem.replace("_", " ").replace("-", " ")

    logger.info("Ingesting document: %s (%d bytes)", original_filename, file_size)

    # ── Extract ─────────────────────────────────────────────────────────
    try:
        pages = extract_pages(file_path, file_type)
    except Exception as exc:
        raise RuntimeError(f"Text extraction failed: {exc}") from exc

    if not pages:
        raise ValueError("No readable text was found in the document.")

    # ── Chunk ────────────────────────────────────────────────────────────
    chunks = chunker.chunk_pages(pages)
    if not chunks:
        raise ValueError("Chunking produced no chunks from the document text.")

    logger.info("Chunked '%s': %d chunks", original_filename, len(chunks))

    # ── Store ────────────────────────────────────────────────────────────
    with get_db() as conn:
        doc_id = repository.insert_document(
            conn,
            filename=original_filename,
            file_type=file_type,
            title=doc_title,
            file_size=file_size,
        )
        repository.insert_chunks(conn, doc_id, chunks)
        repository.update_document_chunk_count(conn, doc_id, len(chunks))

    logger.info("Stored document id=%d with %d chunks", doc_id, len(chunks))

    # ── Rebuild index ────────────────────────────────────────────────────
    _rebuild_index()

    elapsed = time.perf_counter() - t_start
    logger.info("Ingestion complete in %.2fs", elapsed)

    return {
        "document_id": doc_id,
        "filename": original_filename,
        "title": doc_title,
        "file_type": file_type,
        "file_size": file_size,
        "chunk_count": len(chunks),
        "ingestion_ms": int(elapsed * 1000),
    }


def delete_document(document_id: int) -> bool:
    """Delete a document and its chunks, then rebuild the index."""
    with get_db() as conn:
        deleted = repository.delete_document(conn, document_id)

    if deleted:
        _rebuild_index()
        logger.info("Deleted document id=%d and rebuilt index.", document_id)

    return deleted


# ── Index management ─────────────────────────────────────────────────────

def _rebuild_index() -> None:
    """Pull all chunks from SQLite and rebuild the in-memory TF-IDF index."""
    with get_db() as conn:
        all_chunks = repository.get_all_chunks(conn)
    retriever.build_index(all_chunks)
    logger.info("TF-IDF index rebuilt: %d chunks", len(all_chunks))


def rebuild_index_on_startup() -> None:
    """Called at application startup to restore the retriever state."""
    logger.info("Startup: rebuilding TF-IDF index…")
    _rebuild_index()
