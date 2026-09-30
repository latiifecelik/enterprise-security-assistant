"""Pydantic schemas for chat-related API requests and responses."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Request models ────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[int] = None
    top_k: Optional[int] = Field(None, ge=1, le=20)


class ConversationCreateRequest(BaseModel):
    title: str = Field(default="New Chat", max_length=200)


# ── Response models ───────────────────────────────────────────────────────

class SourceCitation(BaseModel):
    rank: int
    chunk_id: Optional[int]
    document_id: Optional[int]
    document_name: str
    document_title: str
    page_number: Optional[int]
    score: float
    content_preview: str
    content: str


class RetrievalStats(BaseModel):
    chunk_count: int
    best_score: float
    retrieve_ms: int
    generate_ms: int
    total_ms: int


class ChatResponse(BaseModel):
    message_id: int
    conversation_id: int
    answer: str
    sources: List[SourceCitation]
    retrieved_chunks: List[Dict[str, Any]]
    retrieval_stats: RetrievalStats
    low_confidence: bool
    provider_info: Dict[str, Any]


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    retrieval_meta: Optional[Dict[str, Any]]
    created_at: str
