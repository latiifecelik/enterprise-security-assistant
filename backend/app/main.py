"""
app/main.py
-----------
FastAPI application entry point.

Startup sequence:
  1. Initialise SQLite database (create tables if needed).
  2. Rebuild TF-IDF index from stored chunks.
  3. Start the Foundry Local provider (or fall back to mock).
  4. Wire the RAG pipeline.
  5. Mount all API routers.
  6. Configure CORS for the React frontend.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import init_db
from app.services.document_service import rebuild_index_on_startup
from app.rag.pipeline import RAGPipeline
from app.api import chat, documents, system

# ── Logging setup ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def _create_ai_provider():
    """
    Try to initialise FoundryLocalProvider.
    Fall back to MockAIProvider if Foundry Local is unavailable.

    The fallback is CLEARLY labelled as a mock — never presented as
    real Foundry Local inference.
    """
    try:
        from app.ai.foundry_local import FoundryLocalProvider
        provider = FoundryLocalProvider()
        logger.info("AI Provider: Foundry Local initialised.")
        return provider
    except Exception as exc:
        logger.warning(
            "Could not initialise FoundryLocalProvider (%s). "
            "Falling back to MockAIProvider. "
            "This is NOT real AI inference.",
            exc,
        )
        from app.ai.mock_provider import MockAIProvider
        return MockAIProvider()


# ── Lifespan ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    logger.info("=== Enterprise Security Assistant starting up ===")

    # Layer 4: Database
    init_db()

    # Layer 3: RAG index
    rebuild_index_on_startup()

    # Layer 5: AI
    ai_provider = _create_ai_provider()
    app.state.ai_provider = ai_provider
    app.state.pipeline = RAGPipeline(ai_provider)

    logger.info("=== Enterprise Security Assistant ready ===")
    yield
    logger.info("=== Enterprise Security Assistant shutting down ===")


# ── Application factory ───────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="Enterprise Security Assistant",
        description=(
            "Privacy-preserving enterprise cybersecurity RAG assistant. "
            "All inference is performed locally using Microsoft Foundry Local."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS — allow the React dev server and any localhost origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(chat.router)
    app.include_router(documents.router)
    app.include_router(system.router)

    return app


app = create_app()


# ── Dev runner ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
