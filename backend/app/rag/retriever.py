"""
rag/retriever.py
----------------
WHY WE NEED IT:
  When a user asks a question we need to find the most relevant passages
  from the knowledge base WITHOUT sending data to the cloud.  TF-IDF
  (Term Frequency – Inverse Document Frequency) is a classic information-
  retrieval technique that does exactly this: it measures how "important"
  a word is to a specific document relative to the whole collection.

HOW IT WORKS:
  1. At index-build time: all chunk texts are vectorised using TF-IDF.
     Each chunk becomes a sparse numeric vector.
  2. At query time: the user's question is transformed into the same vector
     space.
  3. Cosine similarity is computed between the query vector and every chunk
     vector. Cosine similarity measures the angle between two vectors — 1.0
     means identical direction (very relevant), 0.0 means orthogonal (no
     shared terms).
  4. Chunks are ranked by score and the top-K are returned.

WHY TF-IDF (vs embeddings):
  + Zero external API calls — runs entirely on CPU with scikit-learn.
  + Interpretable: you can see exactly which terms drove the match.
  + Fast: sparse matrix operations, index builds in milliseconds.
  - Does not capture semantic meaning ("SSH brute force" ≠ "repeated login
    attempts" lexically). Semantic embeddings handle this better, but they
    require a separate embedding model.
"""

import logging
import time
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings

logger = logging.getLogger(__name__)


class TFIDFRetriever:
    """
    In-memory TF-IDF index over document chunks.

    The index is rebuilt every time documents are added or deleted.
    For this application size (hundreds of chunks) this is instant.
    """

    def __init__(self) -> None:
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._matrix = None                   # sparse TF-IDF matrix
        self._chunks: List[Dict[str, Any]] = []  # parallel list to matrix rows
        self._is_ready: bool = False

    # ── Index management ────────────────────────────────────────────────────

    def build_index(self, chunks: List[Dict[str, Any]]) -> None:
        """
        (Re)build the TF-IDF index from a list of chunk dicts.

        Each dict must have at minimum:
            id, document_id, content, filename, title,
            chunk_index, page_number
        """
        if not chunks:
            self._is_ready = False
            self._chunks = []
            self._matrix = None
            logger.info("TF-IDF index cleared (no chunks).")
            return

        t0 = time.perf_counter()

        texts = [c["content"] for c in chunks]

        self._vectorizer = TfidfVectorizer(
            stop_words="english",
            strip_accents="unicode",
            lowercase=True,
            analyzer="word",
            ngram_range=(1, 2),   # unigrams + bigrams improve phrase matching
            min_df=1,             # include even rare terms (small corpus)
            sublinear_tf=True,    # log(1+tf) instead of raw tf — reduces impact
                                  # of very frequent terms
        )
        self._matrix = self._vectorizer.fit_transform(texts)
        self._chunks = chunks
        self._is_ready = True

        elapsed = time.perf_counter() - t0
        logger.info(
            "TF-IDF index built: %d chunks, %d features, %.3fs",
            len(chunks),
            self._matrix.shape[1],
            elapsed,
        )

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    # ── Retrieval ────────────────────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find the top-K chunks most relevant to `query`.

        Args:
            query:     The user's natural-language question.
            top_k:     How many results to return. Defaults to settings.TOP_K.
            min_score: Minimum cosine-similarity threshold. Chunks below this
                       score are discarded. Defaults to settings.MIN_SIMILARITY_THRESHOLD.

        Returns:
            List of result dicts (sorted by score descending):
                rank          – 1-based rank
                chunk_id      – chunk database id
                document_id   – parent document id
                document_name – original filename
                document_title
                chunk_index
                page_number
                content       – chunk text
                score         – cosine similarity (0.0 – 1.0)
        """
        if not self._is_ready:
            logger.warning("Retriever called but index is not built yet.")
            return []

        if not query or not query.strip():
            return []

        k = top_k or settings.TOP_K
        threshold = min_score if min_score is not None else settings.MIN_SIMILARITY_THRESHOLD

        t0 = time.perf_counter()

        # Transform the query into the same TF-IDF vector space
        query_vec = self._vectorizer.transform([query])

        # Cosine similarity between query and every chunk vector
        scores = cosine_similarity(query_vec, self._matrix).flatten()

        # Rank all chunks by score (descending)
        ranked_indices = np.argsort(scores)[::-1]

        results: List[Dict[str, Any]] = []
        rank = 1
        for idx in ranked_indices:
            if rank > k:
                break
            score = float(scores[idx])
            if score < threshold:
                break   # remaining chunks have even lower scores
            chunk = self._chunks[idx]
            results.append(
                {
                    "rank": rank,
                    "chunk_id": chunk.get("id"),
                    "document_id": chunk.get("document_id"),
                    "document_name": chunk.get("filename", "Unknown"),
                    "document_title": chunk.get("title", "Unknown"),
                    "chunk_index": chunk.get("chunk_index"),
                    "page_number": chunk.get("page_number"),
                    "content": chunk.get("content", ""),
                    "score": round(score, 4),
                }
            )
            rank += 1

        elapsed = time.perf_counter() - t0
        logger.info(
            "Retrieval: query=%r -> %d results in %.3fs",
            query[:60],
            len(results),
            elapsed,
        )
        return results

    def get_index_stats(self) -> Dict[str, Any]:
        """Return diagnostic information about the current index."""
        if not self._is_ready:
            return {"ready": False, "chunk_count": 0, "feature_count": 0}
        return {
            "ready": True,
            "chunk_count": len(self._chunks),
            "feature_count": int(self._matrix.shape[1]),
        }


# ── Singleton instance ────────────────────────────────────────────────────
# One retriever shared across the whole application.
retriever = TFIDFRetriever()
