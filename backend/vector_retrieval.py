"""Optional OpenAI embedding and PostgreSQL/pgvector retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from backend.retrieval import Chunk, SearchResult, normalize_language


@dataclass(frozen=True)
class VectorSearchOutcome:
    results: list[SearchResult]
    top_similarity: float


class VectorIndex(Protocol):
    def search(
        self,
        question: str,
        language: str,
        top_k: int,
    ) -> VectorSearchOutcome:
        ...


class EmbeddingProvider(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...


class OpenAIEmbeddingProvider:
    """Creates document and query embeddings with one configured model."""

    def __init__(self, api_key: str, model: str, dimensions: int) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.dimensions = dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
            dimensions=self.dimensions,
        )
        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


class LocalEmbeddingProvider:
    """Lazy, API-key-free multilingual Sentence Transformers provider."""

    def __init__(self, model: str, dimensions: int) -> None:
        self.model_name = model
        self.dimensions = dimensions
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self.model_name)
            if hasattr(model, "get_embedding_dimension"):
                actual_dimensions = model.get_embedding_dimension()
            else:
                actual_dimensions = (
                    model.get_sentence_embedding_dimension()
                )

            if actual_dimensions != self.dimensions:
                raise ValueError(
                    "ATA_EMBEDDING_DIMENSIONS does not match the local "
                    f"model: expected {actual_dimensions}, configured "
                    f"{self.dimensions}."
                )

            self._model = model

        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._load_model().encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def build_embedding_provider(
    provider: str,
    model: str,
    dimensions: int,
    openai_api_key: str = "",
) -> EmbeddingProvider:
    normalized_provider = provider.casefold().strip()

    if normalized_provider in {"local", "sentence-transformers"}:
        return LocalEmbeddingProvider(model, dimensions)

    if normalized_provider == "openai":
        if not openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required when "
                "ATA_EMBEDDING_PROVIDER=openai."
            )

        return OpenAIEmbeddingProvider(
            api_key=openai_api_key,
            model=model,
            dimensions=dimensions,
        )

    raise ValueError(
        "ATA_EMBEDDING_PROVIDER must be 'local' or 'openai'."
    )


class PgVectorIndex:
    """Performs cosine-similarity search over the ata_chunks table."""

    def __init__(
        self,
        database_url: str,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.database_url = database_url
        self.embedding_provider = embedding_provider

    def search(
        self,
        question: str,
        language: str,
        top_k: int,
    ) -> VectorSearchOutcome:
        import numpy as np
        import psycopg
        from pgvector.psycopg import register_vector

        query_embedding = np.asarray(
            self.embedding_provider.embed_query(question),
            dtype=np.float32,
        )
        normalized_language = normalize_language(language)

        with psycopg.connect(self.database_url) as connection:
            register_vector(connection)
            rows = connection.execute(
                """
                SELECT
                    text,
                    url,
                    title,
                    section,
                    language,
                    faculty,
                    1 - (embedding <=> %s) AS similarity
                FROM ata_chunks
                WHERE language = %s
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (
                    query_embedding,
                    normalized_language,
                    query_embedding,
                    top_k,
                ),
            ).fetchall()

        results = []
        similarities = []

        for row in rows:
            similarity = max(0.0, min(float(row[6]), 1.0))
            similarities.append(similarity)
            results.append(
                SearchResult(
                    chunk=Chunk(
                        text=row[0],
                        url=row[1],
                        title=row[2],
                        section=row[3],
                        language=row[4],
                        faculty=row[5],
                    ),
                    score=similarity,
                )
            )

        return VectorSearchOutcome(
            results=results,
            top_similarity=max(similarities, default=0.0),
        )


def fuse_results(
    vector_results: list[SearchResult],
    bm25_results: list[SearchResult],
    top_k: int,
) -> list[SearchResult]:
    """Combine semantic and lexical ranks with reciprocal-rank fusion."""

    scores: dict[tuple[str, str, str], float] = {}
    representatives: dict[
        tuple[str, str, str],
        SearchResult,
    ] = {}

    for weight, ranked_results in (
        (1.0, vector_results),
        (0.7, bm25_results),
    ):
        for rank, result in enumerate(ranked_results, start=1):
            key = (
                result.chunk.url,
                result.chunk.section,
                result.chunk.text,
            )
            scores[key] = (
                scores.get(key, 0.0) + weight / (60 + rank)
            )
            representatives.setdefault(key, result)

    ranked_keys = sorted(
        scores,
        key=scores.get,
        reverse=True,
    )[:top_k]

    return [
        SearchResult(
            chunk=representatives[key].chunk,
            score=round(scores[key], 6),
        )
        for key in ranked_keys
    ]