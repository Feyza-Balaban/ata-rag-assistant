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
from backend.vector_retrieval import (
    OpenAIEmbeddingProvider,
    PgVectorIndex,
    VectorIndex,
    fuse_results,
)


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
        vector_index: VectorIndex | None = None,
    ) -> None:
        self.settings = settings
        self.index = index or ChunkIndex(settings.chunks_path)
        self.generator = generator or self._build_generator()
        self.vector_index = vector_index or self._build_vector_index()

    @property
    def retrieval_mode(self) -> str:
        return "hybrid-pgvector-bm25" if self.vector_index else "bm25"

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

    def _build_vector_index(self) -> VectorIndex | None:
        if not (
            self.settings.vector_database_url
            and self.settings.openai_api_key
        ):
            return None

        provider = OpenAIEmbeddingProvider(
            api_key=self.settings.openai_api_key,
            model=self.settings.embedding_model,
            dimensions=self.settings.embedding_dimensions,
        )
        return PgVectorIndex(
            database_url=self.settings.vector_database_url,
            embedding_provider=provider,
        )

    def answer(
        self,
        question: str,
        language: str,
        top_k: int | None = None,
    ) -> AnswerResult:
        effective_top_k = top_k or self.settings.top_k
        bm25_results = self.index.search(
            question,
            language,
            max(effective_top_k, 10),
        )
        top_score = bm25_results[0].score if bm25_results else 0.0
        confidence = score_to_confidence(top_score)
        results = bm25_results[:effective_top_k]
        retrieval_score = top_score
        retrieval_mode = "bm25"

        if self.vector_index:
            try:
                vector_outcome = self.vector_index.search(
                    question,
                    language,
                    max(effective_top_k, 10),
                )
            except Exception:
                retrieval_mode = "bm25-vector-fallback"
            else:
                if (
                    vector_outcome.results
                    and vector_outcome.top_similarity
                    >= self.settings.vector_similarity_threshold
                ):
                    results = fuse_results(
                        vector_outcome.results,
                        bm25_results,
                        effective_top_k,
                    )
                    confidence = max(
                        confidence,
                        vector_outcome.top_similarity,
                    )
                    retrieval_score = vector_outcome.top_similarity
                    retrieval_mode = "hybrid-pgvector-bm25"

        if confidence < self.settings.confidence_threshold:
            return AnswerResult(
                answer=not_found_message(language),
                results=[],
                confidence=confidence,
                retrieval_score=round(retrieval_score, 4),
                mode=f"{self.generator.mode}+{retrieval_mode}",
            )

        try:
            answer = self.generator.generate(question, language, results)
            mode = f"{self.generator.mode}+{retrieval_mode}"
        except Exception:
            fallback = ExtractiveAnswerGenerator()
            answer = fallback.generate(question, language, results)
            mode = (
                f"{fallback.mode}-after-provider-error+{retrieval_mode}"
            )

        return AnswerResult(
            answer=answer,
            results=results,
            confidence=confidence,
            retrieval_score=round(retrieval_score, 4),
            mode=mode,
        )
