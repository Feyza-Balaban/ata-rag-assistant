"""Request and response models used by the FastAPI application."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    language: str = Field(default="English", max_length=30)
    top_k: int | None = Field(default=None, ge=1, le=10)


class Source(BaseModel):
    title: str
    url: str
    section: str = ""


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    confidence: float = Field(ge=0.0, le=1.0)
    retrieval_score: float = Field(ge=0.0)
    mode: str


class HealthResponse(BaseModel):
    status: str
    indexed_chunks: int
    chunks_path: str
    llm_enabled: bool
    retrieval_mode: str


class MetricsResponse(BaseModel):
    total_questions: int
    unanswered_questions: int
    average_confidence: float
    average_latency_ms: float
