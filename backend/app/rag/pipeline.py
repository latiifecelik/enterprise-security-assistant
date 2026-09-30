"""
rag/pipeline.py
---------------
The RAG Orchestrator — connects all the pieces.

Data flow:
  User question
      → TFIDFRetriever.retrieve()       (find relevant chunks)
      → PromptBuilder.build_prompt()    (format context + question)
      → AIProvider.generate()           (local inference)
      → format sources
      → return answer + sources
"""

import logging
import time
from typing import Any, Dict, List, Optional

from app.rag.retriever import retriever
from app.rag.prompt_builder import build_prompt, format_sources_for_response
from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Orchestrates retrieval → prompt construction → AI generation.

    The AI provider is injected at construction time so it can be
    swapped (real FoundryLocalProvider vs MockProvider) without
    changing this class.
    """

    def __init__(self, ai_provider) -> None:
        self._ai = ai_provider

    def run(
        self,
        query: str,
        top_k: Optional[int] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the full RAG pipeline for a single user question.

        Args:
            query:                The user's question.
            top_k:                Override for number of chunks to retrieve.
            conversation_history: Prior [{'role': ..., 'content': ...}] turns
                                  for multi-turn context (optional).

        Returns:
            Dict with:
                answer           – The generated text response.
                sources          – List of source citation dicts.
                retrieved_chunks – Full retrieval results (for debug panel).
                retrieval_stats  – Timing and score metadata.
                low_confidence   – True when best score < threshold.
                provider_info    – Which AI provider generated the answer.
        """
        total_start = time.perf_counter()

        # ── Step 1: Retrieve relevant chunks ──────────────────────────────
        t_retrieve = time.perf_counter()
        retrieved = retriever.retrieve(query, top_k=top_k)
        retrieve_ms = int((time.perf_counter() - t_retrieve) * 1000)

        # Determine confidence level based on best score
        best_score = retrieved[0]["score"] if retrieved else 0.0
        low_confidence = best_score < settings.MIN_SIMILARITY_THRESHOLD or not retrieved

        # ── Step 2: Build the grounded prompt ─────────────────────────────
        prompt = build_prompt(query, retrieved, low_confidence=low_confidence)

        # ── Step 3: Generate with local AI ────────────────────────────────
        t_generate = time.perf_counter()
        generation_result = self._ai.generate(
            system_prompt=prompt["system"],
            user_message=prompt["user"],
            conversation_history=conversation_history or [],
        )
        generate_ms = int((time.perf_counter() - t_generate) * 1000)

        # ── Step 4: Format sources for UI display ─────────────────────────
        # Only attach source citations to the UI if retrieval met the confidence threshold
        # and the answer is not a query rejection / off-topic warning
        answer_text = generation_result.get("text", "")
        is_rejection = "Unclear or Invalid Query" in answer_text or "Off-Topic Query Detected" in answer_text
        sources = format_sources_for_response(retrieved) if (not low_confidence and not is_rejection) else []

        total_ms = int((time.perf_counter() - total_start) * 1000)

        logger.info(
            "RAG pipeline: retrieve=%dms, generate=%dms, total=%dms, "
            "chunks=%d, best_score=%.3f, low_confidence=%s",
            retrieve_ms,
            generate_ms,
            total_ms,
            len(retrieved),
            best_score,
            low_confidence,
        )

        return {
            "answer": generation_result["text"],
            "sources": sources,
            "retrieved_chunks": retrieved,
            "retrieval_stats": {
                "chunk_count": len(retrieved),
                "best_score": round(best_score, 4),
                "retrieve_ms": retrieve_ms,
                "generate_ms": generate_ms,
                "total_ms": total_ms,
            },
            "low_confidence": low_confidence,
            "provider_info": generation_result.get("provider_info", {}),
        }
