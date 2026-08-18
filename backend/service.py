"""RAG orchestration independent from the web framework."""

from __future__ import annotations

from dataclasses import dataclass

from backend.config import Settings
from backend.llm import (
    AnswerGenerator,
    ExtractiveAnswerGenerator,
    OpenAIAnswerGenerator,
    not_found_message,
)
from backend.retrieval import ChunkIndex, SearchResult, score_to_confidence


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    results: list[SearchResult]
    confidence: float
    retrieval_score: float
    mode: str


class RAGService:
    def __init__(
        self,
        settings: Settings,
        index: ChunkIndex | None = None,
        generator: AnswerGenerator | None = None,
    ) -> None:
        self.settings = settings
        self.index = index or ChunkIndex(settings.chunks_path)
        self.generator = generator or self._build_generator()

    def _build_generator(self) -> AnswerGenerator:
        if self.settings.openai_api_key:
            try:
                return OpenAIAnswerGenerator(
                    api_key=self.settings.openai_api_key,
                    model=self.settings.openai_model,
                )
            except RuntimeError:
                pass
        return ExtractiveAnswerGenerator()

    def answer(
        self,
        question: str,
        language: str,
        top_k: int | None = None,
    ) -> AnswerResult:
        effective_top_k = top_k or self.settings.top_k
        results = self.index.search(question, language, effective_top_k)
        top_score = results[0].score if results else 0.0
        confidence = score_to_confidence(top_score)

        if confidence < self.settings.confidence_threshold:
            return AnswerResult(
                answer=not_found_message(language),
                results=[],
                confidence=confidence,
                retrieval_score=round(top_score, 4),
                mode=self.generator.mode,
            )

        try:
            answer = self.generator.generate(question, language, results)
            mode = self.generator.mode
        except Exception:
            fallback = ExtractiveAnswerGenerator()
            answer = fallback.generate(question, language, results)
            mode = f"{fallback.mode}-after-provider-error"

        return AnswerResult(
            answer=answer,
            results=results,
            confidence=confidence,
            retrieval_score=round(top_score, 4),
            mode=mode,
        )

