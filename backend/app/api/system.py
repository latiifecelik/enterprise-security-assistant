"""
api/system.py
-------------
System status and health check endpoints.
"""

import logging
from fastapi import APIRouter, Request
from app.db.database import get_db
from app.db import repository
from app.rag.retriever import retriever

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health():
    """Basic liveness check — always returns 200 if the server is running."""
    return {"status": "ok", "service": "Enterprise Security Assistant API"}


@router.get("/system/status")
def system_status(request: Request):
    """
    Full system diagnostics — used by the System Status page in the UI.
    Returns real runtime state for every component.
    """
    ai_provider = request.app.state.ai_provider

    # Database
    try:
        with get_db() as conn:
            stats = repository.get_stats(conn)
        db_status = {"connected": True, "error": None}
    except Exception as exc:
        stats = {"document_count": 0, "chunk_count": 0, "conversation_count": 0}
        db_status = {"connected": False, "error": str(exc)}

    # Retriever
    index_stats = retriever.get_index_stats()

    # AI provider
    ai_status = ai_provider.get_status()

    return {
        "ai": {
            "provider": ai_status["provider"],
            "ready": ai_status["ready"],
            "model": ai_status.get("model"),
            "status_text": ai_status["status_text"],
            "is_mock": ai_status.get("is_mock", False),
            "state": ai_status.get("state"),
            "error": ai_status.get("error"),
        },
        "database": {
            **db_status,
            "path": "data/soc_copilot.db",
            "type": "SQLite",
        },
        "retriever": {
            "ready": index_stats["ready"],
            "type": "TF-IDF (scikit-learn)",
            "chunk_count": index_stats["chunk_count"],
            "feature_count": index_stats.get("feature_count", 0),
        },
        "knowledge_base": {
            "document_count": stats["document_count"],
            "chunk_count": stats["chunk_count"],
            "conversation_count": stats["conversation_count"],
        },
        "privacy": {
            "inference": "Local / On-device",
            "storage": "Local SQLite",
            "internet_required": "Only for initial model download",
            "cloud_llm": False,
        },
    }


@router.get("/system/models")
def list_models(request: Request):
    """
    List available Foundry Local models.
    Only meaningful when the real FoundryLocalProvider is active.
    """
    ai_provider = request.app.state.ai_provider
    if hasattr(ai_provider, "get_available_models"):
        return {"models": ai_provider.get_available_models()}
    return {"models": [], "note": "Model listing not available for this provider."}


@router.post("/system/download-model")
def download_model(request: Request):
    """
    Trigger model download for the configured Foundry Local model.
    This is a blocking call — for production use, wrap in a background task.
    """
    ai_provider = request.app.state.ai_provider
    if not hasattr(ai_provider, "download_model"):
        return {
            "success": False,
            "message": "Active provider does not support model download.",
        }
    result = ai_provider.download_model()
    return result


@router.post("/system/reindex")
def reindex():
    """Rebuild in-memory TF-IDF index from SQLite database."""
    from app.services.document_service import _rebuild_index
    _rebuild_index()
    return {"success": True, "index_stats": retriever.get_index_stats()}


@router.get("/retrieval/debug")
def retrieval_debug(query: str, top_k: int = 5, request: Request = None):
    """
    Debug endpoint — run retrieval for a query and return raw results.
    Used by the 'View Retrieved Context' panel in the UI.
    """
    if not query or not query.strip():
        return {"results": [], "message": "Empty query."}

    results = retriever.retrieve(query, top_k=top_k)
    return {
        "query": query,
        "top_k": top_k,
        "index_stats": retriever.get_index_stats(),
        "results": results,
    }
