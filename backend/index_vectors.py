"""Load scraper chunks into PostgreSQL with OpenAI embeddings and pgvector."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterator

from backend.config import Settings
from backend.vector_retrieval import OpenAIEmbeddingProvider


def load_records(chunks_path: Path) -> Iterator[dict[str, Any]]:
    with chunks_path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {chunks_path}"
                ) from error
            if str(record.get("text", "")).strip() and str(
                record.get("url", "")
            ).strip():
                yield record


def chunk_hash(record: dict[str, Any]) -> str:
    supplied_hash = str(record.get("content_hash", "")).strip()
    if supplied_hash:
        return supplied_hash
    stable_content = "\n".join(
        str(record.get(key, ""))
        for key in ("url", "title", "section", "language", "text")
    )
    return hashlib.sha256(stable_content.encode("utf-8")).hexdigest()


def embedding_text(record: dict[str, Any]) -> str:
    return "\n".join(
        part
        for part in (
            str(record.get("title", "")).strip(),
            str(record.get("section", "")).strip(),
            str(record.get("faculty", "")).strip(),
            str(record.get("text", "")).strip(),
        )
        if part
    )


def batched(
    records: list[dict[str, Any]],
    batch_size: int,
) -> Iterator[list[dict[str, Any]]]:
    for start in range(0, len(records), batch_size):
        yield records[start : start + batch_size]


def index_chunks(
    settings: Settings,
    batch_size: int,
    rebuild: bool,
) -> int:
    if not settings.vector_database_url:
        raise RuntimeError("ATA_VECTOR_DATABASE_URL is required.")
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for embeddings.")
    if not settings.chunks_path.exists():
        raise FileNotFoundError(settings.chunks_path)

    import psycopg
    from pgvector.psycopg import register_vector
    from psycopg.types.json import Jsonb

    records = list(load_records(settings.chunks_path))
    provider = OpenAIEmbeddingProvider(
        api_key=settings.openai_api_key,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
    )

    with psycopg.connect(settings.vector_database_url) as connection:
        connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
        connection.commit()
        register_vector(connection)

        if rebuild:
            connection.execute("DROP TABLE IF EXISTS ata_chunks")

        dimensions = int(settings.embedding_dimensions)
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS ata_chunks (
                id BIGSERIAL PRIMARY KEY,
                content_hash TEXT UNIQUE NOT NULL,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                section TEXT NOT NULL,
                faculty TEXT NOT NULL,
                language TEXT NOT NULL,
                text TEXT NOT NULL,
                metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                embedding vector({dimensions}) NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS ata_chunks_language_idx
            ON ata_chunks (language)
            """
        )
        connection.commit()

        indexed = 0
        for batch in batched(records, batch_size):
            embeddings = provider.embed_documents(
                [embedding_text(record) for record in batch]
            )
            rows = []
            for record, embedding in zip(batch, embeddings, strict=True):
                metadata = {
                    key: record.get(key)
                    for key in ("lastUpdated", "source")
                    if record.get(key) not in (None, "")
                }
                rows.append(
                    (
                        chunk_hash(record),
                        str(record.get("url", "")).strip(),
                        str(record.get("title", "ATA University")).strip(),
                        str(record.get("section", "")).strip(),
                        str(record.get("faculty", "")).strip(),
                        str(record.get("language", "pl")).casefold(),
                        str(record.get("text", "")).strip(),
                        Jsonb(metadata),
                        embedding,
                    )
                )

            connection.executemany(
                """
                INSERT INTO ata_chunks (
                    content_hash, url, title, section, faculty,
                    language, text, metadata, embedding
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (content_hash) DO UPDATE SET
                    url = EXCLUDED.url,
                    title = EXCLUDED.title,
                    section = EXCLUDED.section,
                    faculty = EXCLUDED.faculty,
                    language = EXCLUDED.language,
                    text = EXCLUDED.text,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding,
                    updated_at = NOW()
                """,
                rows,
            )
            connection.commit()
            indexed += len(rows)
            print(f"Indexed {indexed}/{len(records)} chunks")

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS ata_chunks_embedding_hnsw_idx
            ON ata_chunks USING hnsw (embedding vector_cosine_ops)
            """
        )
        connection.commit()

    return indexed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Embed scraper output and load it into pgvector."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Embedding request batch size (default: 100).",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Drop the existing vector table before indexing.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be at least 1")
    count = index_chunks(
        settings=Settings.from_env(),
        batch_size=args.batch_size,
        rebuild=args.rebuild,
    )
    print(f"Vector indexing complete: {count} chunks")


if __name__ == "__main__":
    main()
