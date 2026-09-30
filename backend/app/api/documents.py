"""
api/documents.py
----------------
Document upload and knowledge-base management endpoints.
"""

import logging
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.database import get_db
from app.db import repository
from app.services import document_service
from app.schemas.document import DocumentResponse, DocumentListResponse, IngestionResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
def list_documents():
    with get_db() as conn:
        docs = repository.list_documents(conn)
        stats = repository.get_stats(conn)
    return {
        "documents": docs,
        "total_count": len(docs),
        "total_chunks": stats["chunk_count"],
    }


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int):
    with get_db() as conn:
        doc = repository.get_document(conn, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


@router.post("", response_model=IngestionResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(default=None),
):
    """
    Upload and ingest a document into the knowledge base.

    Supported types: .pdf, .txt, .md, .docx
    """
    # Validate extension
    suffix = Path(file.filename).suffix.lower()
    if suffix not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{suffix}'. "
                f"Allowed: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}"
            ),
        )

    # Validate size
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    # Write to a temp file so extraction tools can open it by path
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=suffix, dir=settings.UPLOAD_DIR
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        result = document_service.ingest_document(
            file_path=tmp_path,
            original_filename=file.filename,
            title=title,
        )
        return {**result, "message": "Document ingested successfully."}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        # Clean up temp file
        if tmp_path.exists():
            tmp_path.unlink()


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int):
    """Delete a document and its chunks, then rebuild the retrieval index."""
    # Verify exists first
    with get_db() as conn:
        doc = repository.get_document(conn, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    deleted = document_service.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete document.")
