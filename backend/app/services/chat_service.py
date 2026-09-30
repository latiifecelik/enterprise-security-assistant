"""
services/chat_service.py
------------------------
Business logic for conversations and chat messages.
Keeps the API handlers thin and the RAG pipeline decoupled.
"""

import logging
from typing import Any, Dict, List, Optional

from app.db import repository
from app.db.database import get_db
from app.rag.pipeline import RAGPipeline

logger = logging.getLogger(__name__)


def create_conversation(title: str = "New Chat") -> Dict[str, Any]:
    with get_db() as conn:
        conv_id = repository.insert_conversation(conn, title)
        conv = repository.get_conversation(conn, conv_id)
    return dict(conv)


def list_conversations() -> List[Dict[str, Any]]:
    with get_db() as conn:
        return repository.list_conversations(conn)


def get_conversation(conversation_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        return repository.get_conversation(conn, conversation_id)


def delete_conversation(conversation_id: int) -> bool:
    with get_db() as conn:
        return repository.delete_conversation(conn, conversation_id)


def get_messages(conversation_id: int) -> List[Dict[str, Any]]:
    with get_db() as conn:
        return repository.list_messages(conn, conversation_id)


def chat(
    pipeline: RAGPipeline,
    conversation_id: int,
    user_question: str,
    top_k: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Process a user message through the RAG pipeline and persist the exchange.

    Steps:
      1. Load conversation history for multi-turn context.
      2. Save the user message.
      3. Run the RAG pipeline.
      4. Save the assistant message (with retrieval metadata).
      5. Auto-title the conversation if it's still "New Chat".
      6. Return the full result.
    """
    # Validate conversation exists
    with get_db() as conn:
        conv = repository.get_conversation(conn, conversation_id)
    if not conv:
        raise ValueError(f"Conversation {conversation_id} not found.")

    # Load history for multi-turn context (last 10 turns)
    with get_db() as conn:
        history_rows = repository.list_messages(conn, conversation_id)
    history = [
        {"role": r["role"], "content": r["content"]}
        for r in history_rows[-10:]
    ]

    # Save user message
    with get_db() as conn:
        repository.insert_message(conn, conversation_id, "user", user_question)
        repository.touch_conversation(conn, conversation_id)

    # Run RAG pipeline
    result = pipeline.run(
        query=user_question,
        top_k=top_k,
        conversation_history=history,
    )

    # Build retrieval metadata to persist with the message
    retrieval_meta = {
        "sources": result["sources"],
        "retrieval_stats": result["retrieval_stats"],
        "low_confidence": result["low_confidence"],
        "provider_info": result["provider_info"],
    }

    # Save assistant message
    with get_db() as conn:
        msg_id = repository.insert_message(
            conn,
            conversation_id,
            "assistant",
            result["answer"],
            retrieval_meta=retrieval_meta,
        )
        repository.touch_conversation(conn, conversation_id)

    # Auto-title: use the first 60 chars of the first question
    if conv["title"] == "New Chat":
        auto_title = user_question[:60].strip()
        if len(user_question) > 60:
            auto_title += "…"
        with get_db() as conn:
            repository.update_conversation_title(conn, conversation_id, auto_title)

    return {
        "message_id": msg_id,
        "conversation_id": conversation_id,
        "answer": result["answer"],
        "sources": result["sources"],
        "retrieved_chunks": result["retrieved_chunks"],
        "retrieval_stats": result["retrieval_stats"],
        "low_confidence": result["low_confidence"],
        "provider_info": result["provider_info"],
    }
