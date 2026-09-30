"""Pydantic schemas for document API requests and responses."""

from typing import Optional
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    title: str
    file_size: int
    chunk_count: int
    created_at: str


class DocumentListResponse(BaseModel):
    documents: list
    total_count: int
    total_chunks: int


class IngestionResponse(BaseModel):
    document_id: int
    filename: str
    title: str
    file_type: str
    file_size: int
    chunk_count: int
    ingestion_ms: int
    message: str
