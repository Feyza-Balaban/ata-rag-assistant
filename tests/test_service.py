from pathlib import Path

from backend.config import Settings
from backend.service import RAGService


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "chunks.jsonl"


def build_service() -> RAGService:
    return RAGService(
        Settings(
            chunks_path=FIXTURE_PATH,
            top_k=3,
            confidence_threshold=0.15,
        )
    )


def test_service_returns_answer_and_sources() -> None:
    result = build_service().answer(
        "Tell me about Computer Science tuition fees.",
        "English",
    )

    assert result.results
    assert "tuition" in result.answer.casefold()
    assert result.mode == "local-extractive+bm25"


def test_service_refuses_when_context_is_missing() -> None:
    result = build_service().answer("What is today's weather?", "English")

    assert result.results == []
    assert "could not find" in result.answer.casefold()


def test_service_localizes_ukrainian_refusal() -> None:
    result = build_service().answer("Яка сьогодні погода?", "Українська")

    assert result.results == []
    assert "не вдалося знайти" in result.answer.casefold()
