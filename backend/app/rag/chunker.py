"""
rag/chunker.py
--------------
WHY WE NEED IT:
  LLMs have a limited context window. We cannot feed an entire 50-page PDF to
  a model.  Chunking splits documents into overlapping pieces so each piece
  fits comfortably, while the overlap ensures we do not lose context at
  boundaries.

HOW IT WORKS:
  1. Receive the full text of a document.
  2. Walk through the text character by character.
  3. At each chunk boundary, try to break at the nearest sentence end (. ! ?)
     to avoid splitting mid-sentence.
  4. Add CHUNK_OVERLAP characters from the previous chunk to the start of the
     next chunk so context carries over.
  5. Return a list of chunk dicts with position metadata.

WHY THESE DEFAULTS:
  CHUNK_SIZE  = 1000 chars ≈ 150-200 tokens — large enough to carry a full
                paragraph of cybersecurity text, small enough to be precise.
  CHUNK_OVERLAP = 150 chars — one or two sentences worth; prevents losing the
                  context of the last sentence in a chunk.
"""

import re
import logging
from typing import Any, Dict, List

from app.core.config import settings

logger = logging.getLogger(__name__)


def _find_sentence_boundary(text: str, position: int, window: int = 80) -> int:
    """
    Search backwards from `position` within `window` characters for a
    sentence-ending punctuation character (.  !  ?).

    Returns the adjusted position if found, otherwise returns the original
    position (hard cut).
    """
    start = max(0, position - window)
    segment = text[start:position]
    # Look for the last sentence-ending punctuation in the segment
    match = None
    for m in re.finditer(r"[.!?]\s+", segment):
        match = m
    if match:
        return start + match.end()
    return position


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> List[Dict[str, Any]]:
    """
    Split `text` into overlapping chunks.

    Args:
        text:          Full normalised document text.
        chunk_size:    Maximum chunk length in characters.
        chunk_overlap: Characters shared between consecutive chunks.

    Returns:
        List of dicts:
            chunk_index  – sequential index (0-based)
            content      – chunk text
            char_start   – start offset in the original text
            char_end     – end offset in the original text
    """
    size = chunk_size or settings.CHUNK_SIZE
    overlap = chunk_overlap or settings.CHUNK_OVERLAP

    if not text or not text.strip():
        return []

    chunks: List[Dict[str, Any]] = []
    start = 0
    idx = 0

    while start < len(text):
        end = min(start + size, len(text))

        # If we are not at the very end of the text, try to break at a
        # sentence boundary to avoid cutting mid-sentence.
        if end < len(text):
            end = _find_sentence_boundary(text, end)

        chunk_content = text[start:end].strip()

        if chunk_content:
            chunks.append(
                {
                    "chunk_index": idx,
                    "content": chunk_content,
                    "char_start": start,
                    "char_end": end,
                    "page_number": None,  # set by caller when known
                }
            )
            idx += 1

        # Move start forward, but keep `overlap` characters for context.
        start = max(start + 1, end - overlap)

    logger.debug(
        "Chunked text: %d chars → %d chunks (size=%d, overlap=%d)",
        len(text),
        len(chunks),
        size,
        overlap,
    )
    return chunks


def chunk_pages(
    pages: List[Dict[str, Any]],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> List[Dict[str, Any]]:
    """
    Chunk a list of page dicts (each has 'text' and 'page_number').

    Page metadata is attached to each chunk so we can cite page numbers
    in the UI.

    Args:
        pages: List of {'page_number': int, 'text': str} dicts.

    Returns:
        Flat list of chunk dicts with 'page_number' populated.
    """
    all_chunks: List[Dict[str, Any]] = []
    global_index = 0

    for page in pages:
        page_text = page.get("text", "")
        page_num = page.get("page_number")

        page_chunks = chunk_text(page_text, chunk_size, chunk_overlap)
        for c in page_chunks:
            c["chunk_index"] = global_index
            c["page_number"] = page_num
            all_chunks.append(c)
            global_index += 1

    return all_chunks
