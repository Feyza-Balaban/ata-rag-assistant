from pathlib import Path

from backend.retrieval import ChunkIndex, score_to_confidence


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "chunks.jsonl"


def test_retrieval_returns_relevant_tuition_source() -> None:
    index = ChunkIndex(FIXTURE_PATH)

    results = index.search(
        "Where can I find the Computer Science tuition fee?",
        "English",
        top_k=3,
    )

    assert results
    assert results[0].chunk.title == "Tuition fees"
    assert results[0].chunk.url.endswith("/en/tuition")
    assert score_to_confidence(results[0].score) > 0.15


def test_retrieval_returns_empty_for_unrelated_question() -> None:
    index = ChunkIndex(FIXTURE_PATH)

    results = index.search("What is the weather today?", "English", top_k=3)

    assert results == []


def test_multilingual_synonyms_retrieve_source_without_turkish_chunks() -> None:
    index = ChunkIndex(FIXTURE_PATH)

    results = index.search(
        "Bilgisayar bölümü öğrenim ücreti nedir?",
        "Türkçe",
        top_k=3,
    )

    assert results
    assert results[0].chunk.title == "Tuition fees"
