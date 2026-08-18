import os
from typing import Any

import requests


def _normalize_sources(raw_sources: Any) -> list[dict[str, str]]:
    if not raw_sources:
        return []

    if isinstance(raw_sources, (str, dict)):
        raw_sources = [raw_sources]

    normalized_sources = []

    for source in raw_sources:
        if isinstance(source, str):
            if source.startswith(("http://", "https://")):
                normalized_sources.append(
                    {
                        "title": "Verified source",
                        "url": source,
                    }
                )

        elif isinstance(source, dict):
            url = (
                source.get("url")
                or source.get("source_url")
                or source.get("link")
                or ""
            )
            title = (
                source.get("title")
                or source.get("name")
                or source.get("source")
                or "Verified source"
            )

            if url:
                normalized_sources.append(
                    {
                        "title": str(title),
                        "url": str(url),
                    }
                )

    return normalized_sources


def ask_rag(question: str, language: str) -> dict[str, Any]:
    api_url = os.getenv("ATA_RAG_API_URL", "").strip()
    api_key = os.getenv("ATA_RAG_API_KEY", "").strip()

    if not api_url:
        return {
            "success": False,
            "answer": "",
            "sources": [],
            "error": "API endpoint is not configured.",
        }

    headers = {"Content-Type": "application/json"}

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request_data = {
        "question": question,
        "language": language,
    }

    try:
        response = requests.post(
            api_url,
            json=request_data,
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        response_data = response.json()

    except requests.RequestException as error:
        return {
            "success": False,
            "answer": "",
            "sources": [],
            "error": f"Backend connection failed: {error}",
        }

    except ValueError:
        return {
            "success": False,
            "answer": "",
            "sources": [],
            "error": "Backend returned invalid JSON.",
        }

    answer = (
        response_data.get("answer")
        or response_data.get("response")
        or response_data.get("message")
        or ""
    )
    sources = _normalize_sources(
        response_data.get("sources") or response_data.get("source")
    )

    if not isinstance(answer, str) or not answer.strip():
        return {
            "success": False,
            "answer": "",
            "sources": [],
            "error": "Backend response does not contain an answer.",
        }

    return {
        "success": True,
        "answer": answer.strip(),
        "sources": sources,
        "error": None,
    }