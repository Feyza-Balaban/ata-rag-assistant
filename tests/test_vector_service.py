from pathlib import Path

from backend.config import Settings
from backend.llm import ExtractiveAnswerGenerator
from backend.retrieval import Chunk, ChunkIndex, SearchResult
from backend.service import RAGService
from backend.vector_retrieval import VectorSearchOutcome


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "chunks.jsonl"


class FakeVectorIndex:
    def search(
        self,
        question: str,
        language: str,
        top_k: int,
    ) -> VectorSearchOutcome:
        del question, language, top_k
        return VectorSearchOutcome(
            results=[
                SearchResult(
                    chunk=Chunk(
                        text="Semantic admission answer from the vector store.",
                        url="https://akademiata.pl/en/vector-admission",
                        title="Vector admission source",
                        section="Admissions",
                        language="en",
                    ),
                    score=0.88,
                )
            ],
            top_similarity=0.88,
        )


def test_service_fuses_vector_and_bm25_results() -> None:
    settings = Settings(
        chunks_path=FIXTURE_PATH,
        top_k=3,
        confidence_threshold=0.15,
        vector_similarity_threshold=0.65,
    )
    service = RAGService(
        settings=settings,
        index=ChunkIndex(FIXTURE_PATH),
        generator=ExtractiveAnswerGenerator(),
        vector_index=FakeVectorIndex(),
    )

    result = service.answer("Tell me about admissions.", "English")

    assert result.results
    assert result.confidence == 0.88
    assert result.mode == "local-extractive+hybrid-pgvector-bm25"
    assert any("vector-admission" in item.chunk.url for item in result.results)
