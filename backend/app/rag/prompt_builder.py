"""
rag/prompt_builder.py
---------------------
WHY WE NEED IT:
  A local LLM has no memory of your documents. The only way to "ground"
  its answers in your knowledge base is to inject the retrieved passages
  directly into the prompt. This is the core idea behind RAG.

HOW IT WORKS:
  1. Receive the top-K retrieved chunks.
  2. Format each chunk as a labelled source block.
  3. Wrap everything in a carefully designed system prompt that instructs
     the model to:
       - Prefer document evidence over its general knowledge.
       - Cite sources by their label ([Source 1], [Source 2], …).
       - Admit when the documents do not contain enough information.
       - Never invent citations or quote text that is not in the context.

HALLUCINATION CONTROL:
  The system prompt explicitly tells the model to:
  - Use ONLY the provided context for factual claims.
  - Say "the local knowledge base does not contain sufficient information"
    when evidence is weak.
  - Never fabricate document names, page numbers, or quotes.

  Additionally, at the API layer we pass a low_confidence flag when the
  best retrieval score falls below MIN_SIMILARITY_THRESHOLD. The prompt
  is adjusted to warn the model that the retrieved context may not be
  directly relevant.
"""

from typing import Any, Dict, List, Optional


# ── System prompt template ───────────────────────────────────────────────

_SYSTEM_PROMPT = """You are an Enterprise Security Assistant — an on-device, defensive cybersecurity AI.
Your job is to help enterprise security analysts and SOC teams investigate security incidents,
understand local cybersecurity documentation, and follow defensive operational procedures.

CRITICAL OPERATIONAL RULES — MUST BE STRICTLY FOLLOWED:
1. LANGUAGE: Respond ONLY in English. Do not use any other language under any circumstances.
2. SCOPE AND RELEVANCE: You specialize strictly in cybersecurity, SOC operations, threat analysis, incident response, network monitoring, authentication security, and security log analysis.
   - If the user asks an off-topic or irrelevant question (such as cooking, casual conversation, sports, general entertainment, homework, non-security trivia, or everyday tasks):
     * You MUST politely decline to answer.
     * State clearly that the question is outside the scope of the Enterprise Security Assistant.
     * Remind the user of the system's specialized domain (SOC incident response, log analysis, threat triage, defensive security).
     * Suggest 2-3 relevant cybersecurity topics they can ask about instead.
   - If the user enters gibberish, random character sequences (e.g. "asdgasjdhgasd", "qweqwe"), or disconnected keywords without a clear question:
     * Politely state that the input is unclear or invalid.
     * Remind them to ask a coherent cybersecurity question.
3. GROUNDING & EVIDENCE:
   - Base your answers primarily on the RETRIEVED CONTEXT provided below.
   - When the retrieved context contains relevant evidence, explicitly cite the sources: e.g., "According to [Source 1]..." or "[Source 2]".
   - If the retrieved context does not contain sufficient information to answer a cybersecurity question, state: "The local knowledge base does not contain sufficient documentation on this specific topic."
4. NO FABRICATION: Never invent document names, page numbers, citations, hashes, or CVE details not in the context.
5. DEFENSIVE ONLY: Only provide defensive, analytical, and remediation guidance. Never provide offensive exploit payloads or attacks.
"""

_LOW_CONFIDENCE_NOTE = """
NOTE: The retrieved context has LOW similarity scores. The documents in the knowledge base
may not directly address this specific question. Treat the retrieved context as potentially
only tangentially related, and be especially careful not to over-claim.
"""


def build_prompt(
    query: str,
    retrieved_chunks: List[Dict[str, Any]],
    low_confidence: bool = False,
) -> Dict[str, str]:
    """
    Build the system and user messages to send to the LLM.

    Args:
        query:           The user's question.
        retrieved_chunks: Output from TFIDFRetriever.retrieve() — list of
                          dicts with keys: rank, document_name, page_number,
                          content, score.
        low_confidence:  True when the best score is below threshold.
                         Adds an extra warning to the system prompt.

    Returns:
        Dict with keys:
            'system'  – the system prompt string
            'user'    – the user message string (context + question)
    """
    # Build the context block
    context_blocks: List[str] = []
    for chunk in retrieved_chunks:
        rank = chunk.get("rank", "?")
        doc_name = chunk.get("document_name", "Unknown document")
        page = chunk.get("page_number")
        score = chunk.get("score", 0.0)
        content = chunk.get("content", "").strip()

        page_str = f"Page {page}" if page else "Page N/A"
        block = (
            f"[Source {rank}]\n"
            f"Document: {doc_name}\n"
            f"{page_str} | Similarity: {score:.3f}\n"
            f"---\n"
            f"{content}"
        )
        context_blocks.append(block)

    if context_blocks:
        context_section = "\n\n".join(context_blocks)
        retrieved_context = (
            "RETRIEVED CONTEXT FROM LOCAL KNOWLEDGE BASE\n"
            "============================================\n\n"
            + context_section
        )
    else:
        retrieved_context = (
            "RETRIEVED CONTEXT FROM LOCAL KNOWLEDGE BASE\n"
            "============================================\n"
            "No relevant documents were found in the knowledge base for this query."
        )

    system = _SYSTEM_PROMPT
    if low_confidence and retrieved_chunks:
        system = system + _LOW_CONFIDENCE_NOTE

    user_message = (
        f"{retrieved_context}\n\n"
        f"============================================\n"
        f"ANALYST QUESTION\n"
        f"============================================\n"
        f"{query}"
    )

    return {"system": system, "user": user_message}


def format_sources_for_response(
    retrieved_chunks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Convert raw retrieval results into the clean source format
    that is stored with the message and displayed in the UI.

    Each returned dict has:
        rank, document_name, document_title, page_number, score, content_preview
    """
    sources = []
    for chunk in retrieved_chunks:
        content = chunk.get("content", "")
        sources.append(
            {
                "rank": chunk.get("rank"),
                "chunk_id": chunk.get("chunk_id"),
                "document_id": chunk.get("document_id"),
                "document_name": chunk.get("document_name", "Unknown"),
                "document_title": chunk.get("document_title", "Unknown"),
                "page_number": chunk.get("page_number"),
                "score": chunk.get("score", 0.0),
                # First 300 chars as a preview in the UI
                "content_preview": content[:300] + ("…" if len(content) > 300 else ""),
                # Full content for the "View Retrieved Context" panel
                "content": content,
            }
        )
    return sources
