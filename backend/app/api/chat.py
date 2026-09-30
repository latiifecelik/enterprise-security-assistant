"""
api/chat.py
-----------
Chat and conversation REST endpoints.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationCreateRequest,
    ConversationResponse,
    MessageResponse,
)
from app.services import chat_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


def _get_pipeline(request: Request):
    """Extract the RAG pipeline from app state."""
    return request.app.state.pipeline


# ── Conversations ─────────────────────────────────────────────────────────

@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations():
    return chat_service.list_conversations()


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
def create_conversation(body: ConversationCreateRequest):
    return chat_service.create_conversation(title=body.title)


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: int):
    conv = chat_service.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conv


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: int):
    deleted = chat_service.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found.")


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=List[MessageResponse],
)
def get_messages(conversation_id: int):
    conv = chat_service.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return chat_service.get_messages(conversation_id)


# ── Chat ──────────────────────────────────────────────────────────────────

@router.post("/chat")
def chat(body: ChatRequest, request: Request):
    """
    Main chat endpoint.

    If conversation_id is omitted, a new conversation is created automatically.
    """
    pipeline = _get_pipeline(request)

    # Create conversation if not provided
    if body.conversation_id is None:
        conv = chat_service.create_conversation()
        conversation_id = conv["id"]
    else:
        conversation_id = body.conversation_id

    try:
        result = chat_service.chat(
            pipeline=pipeline,
            conversation_id=conversation_id,
            user_question=body.question,
            top_k=body.top_k,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        # AI provider unavailable — return a structured chat response
        # instead of a raw 503 so the UI shows something meaningful.
        error_msg = str(exc)
        logger.warning("AI unavailable during chat: %s", error_msg)

        from app.db.database import get_db
        from app.db import repository
        try:
            with get_db() as conn:
                repository.insert_message(conn, conversation_id, "user", body.question)
                repository.touch_conversation(conn, conversation_id)
        except Exception:
            pass

        return {
            "message_id": -1,
            "conversation_id": conversation_id,
            "answer": (
                "⚠️ **AI Runtime Unavailable**\n\n"
                f"{error_msg}\n\n"
                "**What you can do:**\n"
                "- Go to **System Status** page and click **Download Model** to download `phi-3.5-mini`\n"
                "- Once downloaded, the model loads automatically\n"
                "- Document retrieval is still working — your knowledge base is ready\n\n"
                "*Note: Model download requires an internet connection (~2.4 GB).*"
            ),
            "sources": [],
            "retrieved_chunks": [],
            "retrieval_stats": {"chunk_count": 0, "best_score": 0.0, "retrieve_ms": 0, "generate_ms": 0, "total_ms": 0},
            "low_confidence": True,
            "provider_info": {"provider": "Foundry Local", "model": None, "is_mock": False},
        }
    except Exception as exc:
        logger.error("Chat error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during chat.")
