"""
ai/base.py
----------
Abstract base class for all AI providers.

WHY AN ABSTRACTION:
  We want to swap the real Foundry Local provider with a mock during
  development, or add future providers (Ollama, llama.cpp, etc.)
  without changing any business logic.

  Any class that inherits from AIProvider and implements `generate()`
  can be plugged in.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class AIProvider(ABC):
    """
    Abstract AI inference provider.

    Implementors must define:
        generate()   – run inference and return a result dict
        get_status() – return health/readiness information
        provider_name – human-readable name shown in the UI
    """

    provider_name: str = "Unknown Provider"

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: List[Dict[str, str]] | None = None,
    ) -> Dict[str, Any]:
        """
        Run inference and return the generated text.

        Args:
            system_prompt:        The grounding system prompt.
            user_message:         The formatted user message (context + question).
            conversation_history: Optional prior conversation turns as
                                  [{'role': 'user'|'assistant', 'content': str}].

        Returns:
            Dict with at minimum:
                text          – The generated response text.
                provider_info – Dict describing the provider and model used.
        """

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Return current status of the provider.

        Returns:
            Dict with at minimum:
                ready        – bool, whether inference is possible
                provider     – provider name string
                model        – model identifier or None
                status_text  – human-readable status for the UI
        """
