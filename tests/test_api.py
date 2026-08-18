from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import create_app
from backend.config import Settings
from backend.service import RAGService


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "chunks.jsonl"


def build_client(api_key: str = "") -> TestClient:
    settings = Settings(
        chunks_path=FIXTURE_PATH,
        top_k=3,
        confidence_threshold=0.15,
        backend_api_key=api_key,
    )
    return TestClient(create_app(settings, RAGService(settings)))


def test_health_and_ask_contract() -> None:
    client = build_client()

    health_response = client.get("/health")
    ask_response = client.post(
        "/ask",
        json={
            "question": "Where can I find Computer Science tuition fees?",
            "language": "English",
        },
    )

    assert health_response.status_code == 200
    assert health_response.json()["indexed_chunks"] == 3
    assert ask_response.status_code == 200
    assert ask_response.json()["sources"][0]["url"].endswith("/en/tuition")


def test_optional_api_key_is_enforced() -> None:
    client = build_client("secret-test-key")

    unauthorized = client.post(
        "/ask",
        json={"question": "Admissions requirements", "language": "English"},
    )
    authorized = client.post(
        "/ask",
        headers={"Authorization": "Bearer secret-test-key"},
        json={"question": "Admissions requirements", "language": "English"},
    )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200

