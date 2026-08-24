"""FastAPI entry point for the ATA University RAG assistant."""

from __future__ import annotations

import hmac
import time
from dataclasses import dataclass

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from backend.config import Settings
from backend.schemas import (
    AskRequest,
    AskResponse,
    HealthResponse,
    MetricsResponse,
    Source,
)
from backend.service import RAGService


@dataclass
class MetricsTracker:
    total_questions: int = 0
    unanswered_questions: int = 0
    confidence_sum: float = 0.0
    latency_sum_ms: float = 0.0

    def record(self, confidence: float, latency_ms: float, answered: bool) -> None:
        self.total_questions += 1
        self.confidence_sum += confidence
        self.latency_sum_ms += latency_ms
        if not answered:
            self.unanswered_questions += 1

    def snapshot(self) -> MetricsResponse:
        count = self.total_questions
        return MetricsResponse(
            total_questions=count,
            unanswered_questions=self.unanswered_questions,
            average_confidence=round(
                self.confidence_sum / count if count else 0.0, 4
            ),
            average_latency_ms=round(
                self.latency_sum_ms / count if count else 0.0, 2
            ),
        )


def create_app(
    settings: Settings | None = None,
    service: RAGService | None = None,
) -> FastAPI:
    active_settings = settings or Settings.from_env()
    active_service = service or RAGService(active_settings)
    metrics = MetricsTracker()

    app = FastAPI(
        title="ATA RAG Assistant API",
        version="1.0.0",
        description="Source-grounded answers from ATA University content.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(active_settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

    def verify_api_key(
        authorization: str | None = Header(default=None),
    ) -> None:
        expected_key = active_settings.backend_api_key
        if not expected_key:
            return
        supplied_key = ""
        if authorization and authorization.startswith("Bearer "):
            supplied_key = authorization.removeprefix("Bearer ").strip()
        if not hmac.compare_digest(supplied_key, expected_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key.",
            )

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {
            "name": "ATA RAG Assistant API",
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        indexed_chunks = len(active_service.index.chunks)
        return HealthResponse(
            status="ready" if indexed_chunks else "waiting_for_data",
            indexed_chunks=indexed_chunks,
            chunks_path=str(active_settings.chunks_path),
            llm_enabled=active_service.generator.mode == "openai-responses",
            retrieval_mode=active_service.retrieval_mode,
        )

    @app.get("/metrics", response_model=MetricsResponse)
    def get_metrics(_: None = Depends(verify_api_key)) -> MetricsResponse:
        return metrics.snapshot()

    @app.post("/ask", response_model=AskResponse)
    def ask(
        request: AskRequest,
        _: None = Depends(verify_api_key),
    ) -> AskResponse:
        started_at = time.perf_counter()
        result = active_service.answer(
            question=request.question.strip(),
            language=request.language.strip(),
            top_k=request.top_k,
        )
        latency_ms = (time.perf_counter() - started_at) * 1000

        sources = []
        seen_urls: set[str] = set()
        for search_result in result.results:
            chunk = search_result.chunk
            if chunk.url in seen_urls:
                continue
            seen_urls.add(chunk.url)
            sources.append(
                Source(
                    title=chunk.title or "ATA University source",
                    url=chunk.url,
                    section=chunk.section,
                )
            )
            if len(sources) == 3:
                break

        answered = bool(sources)
        metrics.record(result.confidence, latency_ms, answered)
        return AskResponse(
            answer=result.answer,
            sources=sources,
            confidence=result.confidence,
            retrieval_score=result.retrieval_score,
            mode=result.mode,
        )

    return app


app = create_app()
