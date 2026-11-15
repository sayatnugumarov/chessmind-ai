"""Settings read from environment variables (and backend/.env if present)."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    stockfish_path: str = field(default_factory=lambda: os.getenv("STOCKFISH_PATH", ""))
    engine_time_limit: float = field(default_factory=lambda: _float("ENGINE_TIME_LIMIT", 0.1))
    engine_deep_time_limit: float = field(
        default_factory=lambda: _float("ENGINE_DEEP_TIME_LIMIT", 0.5)
    )
    llm_base_url: str = field(
        default_factory=lambda: os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    )
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "openai/gpt-oss-120b"))
    coach_language: str = field(default_factory=lambda: os.getenv("COACH_LANGUAGE", "ru"))
    cors_origins: list[str] = field(
        default_factory=lambda: [
            o.strip()
            for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
            if o.strip()
        ]
    )


settings = Settings()
