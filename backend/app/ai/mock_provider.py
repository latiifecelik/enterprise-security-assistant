"""
ai/mock_provider.py
-------------------
Development-only fallback AI provider.

IMPORTANT: This provider does NOT use Foundry Local or any LLM.
It returns templated placeholder responses so the rest of the
application can be developed and tested without waiting for
model downloads or requiring GPU/CPU inference.

The UI always displays "Development Mock Provider" when this is
active — never "Foundry Local".

This class will NEVER be used in the final production configuration
when Foundry Local is available.
"""

import logging
import time
from typing import Any, Dict, List

from app.ai.base import AIProvider

logger = logging.getLogger(__name__)


class MockAIProvider(AIProvider):
    """
    Fake AI provider for development and testing.

    Returns realistic-looking but templated responses.
    Always clearly identifies itself as a mock.
    """

    provider_name = "Development Mock Provider"

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: List[Dict[str, str]] | None = None,
    ) -> Dict[str, Any]:
        """Return a templated mock response — no actual inference."""
        logger.warning(
            "MockAIProvider.generate() called — this is NOT real AI inference."
        )

        # Simulate a tiny processing delay so the UI behaves realistically
        time.sleep(0.3)

        # Extract the user question from the message (after the last ==== block)
        question = user_message
        if "ANALYST QUESTION" in user_message:
            question = user_message.split("ANALYST QUESTION")[-1].strip()
            question = question.replace("=" * 44, "").strip()

        # Check if retrieved context is present in user_message
        has_context = "RETRIEVED CONTEXT FROM LOCAL KNOWLEDGE BASE" in user_message and "No relevant documents were found" not in user_message

        # Common cybersecurity keywords that indicate relevant queries even if documentation is thin
        sec_keywords = {
            "security", "soc", "incident", "log", "logs", "attack", "brute", "ssh", "auth",
            "authentication", "malware", "phish", "phishing", "cve", "vulnerability", "exploit",
            "firewall", "dns", "proxy", "edr", "ioc", "triage", "forensic", "lateral", "spray",
            "spraying", "stuffing", "credential", "credentials", "compromise", "alert", "c2", "command",
            "reconnaissance", "payload", "exfiltration", "active directory", "windows event", "mitre",
            "ransomware", "trojan", "analyst", "containment", "siem", "playbook", "investigate",
            "investigation", "privilege", "unauthorized", "intrusion", "network", "endpoint"
        }
        q_lower = question.lower()
        is_security_related = any(kw in q_lower for kw in sec_keywords)

        # Validate query coherence: detect keyboard mash, random strings, and meaningless inputs
        import re
        tokens = re.findall(r"\b[a-zA-Z0-9_\-]+\b", question.lower())

        # Check for gibberish tokens (long consonant runs or random character patterns)
        def is_gibberish_token(tok: str) -> bool:
            if len(tok) >= 6 and not re.search(r"[aeiouyAEIOUY]", tok):
                return True
            # Long tokens with unusual character diversity / consonant clustering
            if len(tok) >= 8 and re.search(r"[bcdfghjklmnpqrstvwxz]{5,}", tok):
                return True
            return False

        has_gibberish = any(is_gibberish_token(t) for t in tokens)

        # Check for meaningful cybersecurity question phrasing or domain depth
        # A single keyword like "soc" accompanied by noise is NOT a valid cybersecurity query
        valid_english_words = {
            "what", "how", "why", "when", "which", "where", "who", "can", "should", "is", "are",
            "explain", "describe", "steps", "guide", "procedure", "process", "difference", "between",
            "detect", "prevent", "analyze", "review", "check", "contain", "investigate", "mitigate",
            "incident", "response", "playbook", "authentication", "phishing", "malware", "network",
            "monitoring", "firewall", "brute", "force", "spraying", "stuffing", "credentials"
        }
        recognized_tokens = [t for t in tokens if t in valid_english_words or t in sec_keywords]
        ratio_recognized = len(recognized_tokens) / max(len(tokens), 1)

        # Reject if query is gibberish, too short with only a single generic keyword, or predominantly unrecognized tokens
        if has_gibberish or (len(tokens) <= 3 and len(recognized_tokens) < 2 and not any(t in question.lower() for t in ["what is", "how to", "explain"])) or ratio_recognized < 0.4:
            mock_response = (
                "⚠️ **Unclear or Invalid Query Detected**\n\n"
                "The input entered does not form a coherent cybersecurity question or incident description. "
                "Typing disconnected keywords or random characters cannot be processed by the Enterprise Security Assistant.\n\n"
                "**How to ask a question:**\n"
                "- *\"How should I investigate repeated failed SSH logins?\"*\n"
                "- *\"What is the difference between brute force and password spraying?\"*\n"
                "- *\"What log events should I check for credential stuffing?\"*\n"
                "- *\"What are the initial triage steps for a suspected phishing email?\"*\n\n"
                "Please enter a clear cybersecurity question or incident description to receive guided analysis."
            )
        elif not is_security_related:
            mock_response = (
                "⚠️ **Off-Topic Query Detected**\n\n"
                "Your inquiry does not appear to be related to cybersecurity, SOC operations, or incident analysis. "
                "The **Enterprise Security Assistant** is strictly designed for defensive security operations.\n\n"
                "**Supported Topic Areas:**\n"
                "- Incident triage and severity assessment (e.g., P1–P4 classification)\n"
                "- Authentication attack investigations (SSH brute force, password spraying, credential stuffing)\n"
                "- Network intrusion indicators (DNS tunneling, beaconing, firewall/proxy anomalies)\n"
                "- Phishing campaign triage, email header inspection, and user containment\n"
                "- Defensive log analysis (Windows Event IDs 4624/4625, Linux auth.log, cloud audit trails)\n\n"
                "Please submit a cybersecurity or incident response question to proceed."
            )
        else:
            context_summary = ""
            extracted_answer = ""
            if has_context:
                context_section = user_message.split("RETRIEVED CONTEXT FROM LOCAL KNOWLEDGE BASE")[-1]
                if "ANALYST QUESTION" in context_section:
                    context_section = context_section.split("ANALYST QUESTION")[0]
                context_summary = f"\n\n**📄 Retrieved Context from Local Knowledge Base:**\n```text\n{context_section.strip()[:700]}...\n```\n"

                # Check if question is an inquiry or definition (e.g., "what is", "explain", "describe")
                q_clean = question.lower().strip(" ?.")
                if any(q_clean.startswith(prefix) for prefix in ["what is", "what are", "explain", "describe", "define"]):
                    # Find relevant explanatory lines in context_section
                    clean_lines = [
                        line.strip() for line in context_section.splitlines()
                        if line.strip() and not line.strip().startswith("[Source") and not line.strip().startswith("Document:") and not line.strip().startswith("Page") and not line.strip().startswith("---") and not line.strip().startswith("==")
                    ]
                    # Look for lines that define or explain
                    explanation_lines = [l for l in clean_lines if len(l) > 30][:3]
                    if explanation_lines:
                        extracted_answer = (
                            "**Context Synthesis:**\n"
                            + "\n\n".join(f"> {line}" for line in explanation_lines)
                            + "\n\n"
                        )

            if extracted_answer:
                content_body = extracted_answer
            else:
                content_body = (
                    "**Recommended SOC Investigation Steps:**\n"
                    "1. **Triage & Scope:** Review relevant alert parameters and check source log streams (Windows Event ID 4624/4625, SSH auth.log, firewall logs).\n"
                    "2. **Evidence Preservation:** Establish asset timeline and record running processes, active connections, and credential audit trails.\n"
                    "3. **Containment:** Temporarily restrict compromised user accounts, invalidate active sessions, and block malicious indicators.\n\n"
                )

            mock_response = (
                "⚠️ **Offline Copilot (Fallback Mode — Local Model Not Yet Downloaded)**\n\n"
                "The local AI inference model is not yet loaded into memory. Operating in **RAG Retrieval / Fallback Mode**.\n\n"
                f"**Query Received:** {question[:300]}\n"
                f"{context_summary}\n"
                f"{content_body}"
                "💡 *To enable full on-device neural inference (`phi-3.5-mini`), navigate to the **System Status** tab and click **Download Model**.*"
            )

        return {
            "text": mock_response,
            "provider_info": {
                "provider": self.provider_name,
                "model": None,
                "is_mock": True,
            },
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "ready": True,   # mock is always "ready" (no real inference)
            "provider": self.provider_name,
            "model": None,
            "status_text": "Development Mock — No Real Inference",
            "is_mock": True,
        }
