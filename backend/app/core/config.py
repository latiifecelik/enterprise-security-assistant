"""
core/config.py
--------------
Central application configuration.
All environment-variable-backed settings live here.
Import `settings` anywhere you need a config value.
"""

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent   # backend/
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class Settings:
    """Application settings — override via environment variables or .env file."""

    # ── Server ─────────────────────────────────────────────────────────────
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # ── Database ───────────────────────────────────────────────────────────
    DATABASE_PATH: str = os.getenv(
        "DATABASE_PATH", str(DATA_DIR / "soc_copilot.db")
    )

    # ── Document storage ───────────────────────────────────────────────────
    UPLOAD_DIR: Path = UPLOAD_DIR
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    ALLOWED_EXTENSIONS: set = {".pdf", ".txt", ".md", ".docx"}

    # ── Chunking ───────────────────────────────────────────────────────────
    # 1000 chars ≈ ~150 tokens — large enough for context, small enough for precision.
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    # 150-char overlap prevents context loss at chunk boundaries.
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))

    # ── Retrieval ──────────────────────────────────────────────────────────
    TOP_K: int = int(os.getenv("TOP_K", "5"))
    # Chunks below this score are considered low-confidence matches.
    MIN_SIMILARITY_THRESHOLD: float = float(
        os.getenv("MIN_SIMILARITY_THRESHOLD", "0.08")
    )

    # ── Foundry Local ──────────────────────────────────────────────────────
    FOUNDRY_APP_NAME: str = os.getenv("FOUNDRY_APP_NAME", "soc-copilot")
    # Preferred model alias — must be a valid alias in the Foundry catalog.
    FOUNDRY_MODEL_ALIAS: str = os.getenv("FOUNDRY_MODEL_ALIAS", "phi-3.5-mini")
    # Max tokens the model should generate per response (tuned for CPU latency).
    FOUNDRY_MAX_TOKENS: int = int(os.getenv("FOUNDRY_MAX_TOKENS", "384"))
    FOUNDRY_TEMPERATURE: float = float(os.getenv("FOUNDRY_TEMPERATURE", "0.1"))

    # ── Logging ────────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ── CORS ───────────────────────────────────────────────────────────────
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
