"""Environment-backed configuration for the ATA RAG API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


def _float_value(name: str, default: float) -> float:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        return float(raw_value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    chunks_path: Path
    top_k: int = 5
    confidence_threshold: float = 0.15
    backend_api_key: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-5.4-mini"
    vector_database_url: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    vector_similarity_threshold: float = 0.65
    cors_origins: tuple[str, ...] = ("http://localhost:8501",)

    @classmethod
    def from_env(cls) -> "Settings":
        chunks_path = Path(
            os.getenv(
                "ATA_CHUNKS_PATH",
                str(PROJECT_ROOT / "scraper" / "output" / "chunks.jsonl"),
            )
        ).expanduser()

        origin_value = os.getenv(
            "ATA_CORS_ORIGINS",
            "http://localhost:8501,http://127.0.0.1:8501",
        )
        origins = tuple(
            origin.strip() for origin in origin_value.split(",") if origin.strip()
        )

        return cls(
            chunks_path=chunks_path,
            top_k=_positive_int("ATA_TOP_K", 5),
            confidence_threshold=_float_value(
                "ATA_CONFIDENCE_THRESHOLD", 0.15
            ),
            backend_api_key=os.getenv("ATA_BACKEND_API_KEY", "").strip(),
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            openai_model=os.getenv(
                "OPENAI_MODEL", "gpt-5.4-mini"
            ).strip(),
            vector_database_url=os.getenv(
                "ATA_VECTOR_DATABASE_URL", ""
            ).strip(),
            embedding_model=os.getenv(
                "ATA_EMBEDDING_MODEL", "text-embedding-3-small"
            ).strip(),
            embedding_dimensions=_positive_int(
                "ATA_EMBEDDING_DIMENSIONS", 1536
            ),
            vector_similarity_threshold=_float_value(
                "ATA_VECTOR_SIMILARITY_THRESHOLD", 0.65
            ),
            cors_origins=origins,
        )
