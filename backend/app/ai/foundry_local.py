"""
ai/foundry_local.py
--------------------
REAL Microsoft Foundry Local provider.

HOW IT WORKS:
  1. On startup, FoundryLocalManager is initialised with the app configuration.
  2. We check whether the configured model alias is already cached locally.
     If cached, we load it immediately.
     If not cached, we mark the provider as "model_not_downloaded" and expose
     a download() method that the API can call to trigger a download.
  3. The SDK exposes an OpenAI-compatible endpoint via start_web_service().
     We call that endpoint using the openai client pointed at localhost.
  4. Every generate() call sends a chat-completion request to the local
     web service — no data leaves the machine.

IMPORTANT:
  - provider_name is always "Foundry Local" when this class is active.
  - The UI status reflects the real runtime state (loading, ready, error).
  - No cloud API keys are used or needed.
"""

import logging
import time
import threading
from typing import Any, Dict, List, Optional

from app.ai.base import AIProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class FoundryLocalProvider(AIProvider):
    """
    AI provider backed by Microsoft Foundry Local SDK v1.2.4.

    Lifecycle:
        __init__()        – initialise SDK, detect cached model
        ensure_ready()    – load model into runtime (blocking)
        download_model()  – download model if not cached (blocking, with callback)
        generate()        – run chat-completion inference
        get_status()      – return current state
    """

    provider_name = "Foundry Local"

    # Internal state machine values
    _STATE_INIT = "initializing"
    _STATE_NO_MODEL = "model_not_downloaded"
    _STATE_LOADING = "model_loading"
    _STATE_READY = "ready"
    _STATE_ERROR = "error"

    def __init__(self) -> None:
        self._state = self._STATE_INIT
        self._error_message: Optional[str] = None
        self._manager = None
        self._model = None           # IModel instance from the catalog
        self._model_alias: str = settings.FOUNDRY_MODEL_ALIAS
        self._service_url: Optional[str] = None
        self._openai_client = None
        self._lock = threading.Lock()

        self._initialise()

    def _initialise(self) -> None:
        """Initialise the Foundry Local SDK and detect model state."""
        try:
            from foundry_local_sdk import FoundryLocalManager, Configuration

            config = Configuration(app_name=settings.FOUNDRY_APP_NAME)
            self._manager = FoundryLocalManager(config)

            # Check whether the preferred model is already downloaded
            cached = self._manager.catalog.get_cached_models()
            cached_aliases = {m.alias for m in cached}

            if self._model_alias in cached_aliases:
                logger.info(
                    "Foundry Local: model '%s' found in cache. Loading…",
                    self._model_alias,
                )
                self._state = self._STATE_LOADING
                # Load in a background thread so we don't block startup
                threading.Thread(target=self._load_model, daemon=True).start()
            else:
                logger.info(
                    "Foundry Local: model '%s' not cached. "
                    "Call download_model() to download it.",
                    self._model_alias,
                )
                self._state = self._STATE_NO_MODEL

        except Exception as exc:
            self._state = self._STATE_ERROR
            self._error_message = str(exc)
            logger.error("Foundry Local init failed: %s", exc, exc_info=True)

    def _load_model(self) -> None:
        """Load the model into the Foundry Local runtime (blocking)."""
        try:
            with self._lock:
                self._state = self._STATE_LOADING

            model_obj = self._manager.catalog.get_model(self._model_alias)
            if model_obj is None:
                raise ValueError(
                    f"Model alias '{self._model_alias}' not found in catalog."
                )

            # Start the built-in OpenAI-compatible web service
            self._manager.start_web_service()
            urls = self._manager.urls  # list of bound URLs

            if not urls:
                raise RuntimeError("Foundry Local web service returned no URLs.")

            self._service_url = urls[0]
            logger.info("Foundry Local web service started at %s", self._service_url)

            # Load the model into the runtime
            model_obj.load()
            self._model = model_obj

            # Create an OpenAI client pointed at the local service
            import openai
            self._openai_client = openai.OpenAI(
                base_url=f"{self._service_url}/v1",
                api_key="foundry-local",  # placeholder — not sent anywhere
            )

            with self._lock:
                self._state = self._STATE_READY
            logger.info(
                "Foundry Local: model '%s' ready for inference.", self._model_alias
            )

        except Exception as exc:
            with self._lock:
                self._state = self._STATE_ERROR
                self._error_message = str(exc)
            logger.error("Foundry Local model load failed: %s", exc, exc_info=True)

    def download_model(
        self,
        progress_callback=None,
    ) -> Dict[str, Any]:
        """
        Download the configured model from the Foundry catalog.

        This is a blocking call. The caller should run it in a background
        thread or task queue for production use.

        Returns:
            Dict with success, message, model_alias.
        """
        try:
            logger.info(
                "Foundry Local: downloading model '%s'…", self._model_alias
            )
            with self._lock:
                self._state = self._STATE_LOADING

            model_obj = self._manager.catalog.get_model(self._model_alias)
            if model_obj is None:
                raise ValueError(
                    f"Model alias '{self._model_alias}' not found in catalog."
                )

            # Download the model (blocking)
            model_obj.download(progress_callback=progress_callback)
            logger.info("Foundry Local: download complete. Loading…")

            # Now load it
            self._load_model()

            return {
                "success": True,
                "message": f"Model '{self._model_alias}' downloaded and loaded.",
                "model_alias": self._model_alias,
            }

        except Exception as exc:
            with self._lock:
                self._state = self._STATE_ERROR
                self._error_message = str(exc)
            logger.error("Model download failed: %s", exc, exc_info=True)
            return {
                "success": False,
                "message": str(exc),
                "model_alias": self._model_alias,
            }

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: List[Dict[str, str]] | None = None,
    ) -> Dict[str, Any]:
        """Run chat-completion against the local Foundry web service."""
        if self._state != self._STATE_READY:
            logger.info("Foundry Local not ready (state=%s). Delegating to fallback mock generator.", self._state)
            from app.ai.mock_provider import MockAIProvider
            fallback = MockAIProvider()
            res = fallback.generate(system_prompt, user_message, conversation_history)
            res["provider_info"] = {
                "provider": "Foundry Local (Fallback Mock)",
                "model": f"{self._model_alias} [not loaded / state: {self._state}]",
                "is_mock": True,
                "note": f"Model '{self._model_alias}' is not yet downloaded/loaded into memory. You can initiate download from System Status.",
            }
            return res

        # Build the messages list
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        t0 = time.perf_counter()
        response = self._openai_client.chat.completions.create(
            model=self._model_alias,
            messages=messages,
            max_tokens=settings.FOUNDRY_MAX_TOKENS,
            temperature=settings.FOUNDRY_TEMPERATURE,
        )
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        answer_text = response.choices[0].message.content or ""
        logger.info(
            "Foundry Local inference: %d tokens in %dms",
            response.usage.completion_tokens if response.usage else -1,
            elapsed_ms,
        )

        return {
            "text": answer_text,
            "provider_info": {
                "provider": self.provider_name,
                "model": self._model_alias,
                "is_mock": False,
                "inference_ms": elapsed_ms,
            },
        }

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            state = self._state

        status_map = {
            self._STATE_INIT:     "Initialising…",
            self._STATE_NO_MODEL: f"Model '{self._model_alias}' not downloaded",
            self._STATE_LOADING:  f"Loading '{self._model_alias}'…",
            self._STATE_READY:    f"Ready — {self._model_alias}",
            self._STATE_ERROR:    f"Error: {self._error_message}",
        }

        return {
            "ready": state == self._STATE_READY,
            "provider": self.provider_name,
            "model": self._model_alias if state == self._STATE_READY else None,
            "state": state,
            "status_text": status_map.get(state, "Unknown"),
            "is_mock": False,
            "service_url": self._service_url,
            "error": self._error_message if state == self._STATE_ERROR else None,
        }

    def get_available_models(self) -> List[Dict[str, Any]]:
        """List all models in the Foundry catalog (for status/settings page)."""
        if self._manager is None:
            return []
        try:
            models = self._manager.catalog.list_models()
            cached_ids = {
                m.id for m in self._manager.catalog.get_cached_models()
            }
            return [
                {
                    "alias": m.alias,
                    "id": m.id,
                    "cached": m.id in cached_ids,
                }
                for m in models
                if getattr(m.info, "task", "") == "chat-completion"
            ]
        except Exception as exc:
            logger.error("Failed to list Foundry models: %s", exc)
            return []
