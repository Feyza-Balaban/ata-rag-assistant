"""Small dependency-free BM25 index used for local and fallback retrieval."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


TOKEN_PATTERN = re.compile(r"[^\W_]+", flags=re.UNICODE)

LANGUAGE_ALIASES = {
    "english": "en",
    "en": "en",
    "polski": "pl",
    "polish": "pl",
    "pl": "pl",
    "türkçe": "tr",
    "turkish": "tr",
    "tr": "tr",
}

STOPWORDS = {
    "a",
    "about",
    "and",
    "are",
    "bu",
    "co",
    "czy",
    "dla",
    "do",
    "gibi",
    "ile",
    "is",
    "jak",
    "jaki",
    "na",
    "nedir",
    "of",
    "olan",
    "the",
    "to",
    "ve",
    "what",
    "where",
    "w",
    "z",
}

SYNONYM_GROUPS = (
    {"admission", "admissions", "apply", "application", "başvuru", "kabul", "rekrutacja"},
    {"cost", "czesne", "fee", "fees", "harç", "tuition", "ücret", "ücreti"},
    {"address", "adres", "contact", "iletişim", "kontakt"},
    {"dean", "dekan", "dziekanat"},
    {"burs", "scholarship", "stypendium"},
    {"belgeler", "documents", "dokumenty"},
    {"calendar", "dönem", "kalendarz", "semester", "semestr", "takvim"},
    {"bilgisayar", "computer", "informatyka", "informatics"},
)

SYNONYM_LOOKUP = {
    term: group
    for group in SYNONYM_GROUPS
    for term in group
}


def tokenize(value: str) -> list[str]:
    return [
        token
        for token in TOKEN_PATTERN.findall(value.casefold())
        if len(token) > 1 and token not in STOPWORDS
    ]


def expand_query_terms(terms: list[str]) -> list[str]:
    expanded = set(terms)
    for term in terms:
        expanded.update(SYNONYM_LOOKUP.get(term, ()))
    return sorted(expanded)


@dataclass(frozen=True)
class Chunk:
    text: str
    url: str
    title: str
    section: str
    language: str
    faculty: str = ""


@dataclass(frozen=True)
class SearchResult:
    chunk: Chunk
    score: float


class ChunkIndex:
    """Loads scraper JSONL output and ranks chunks with BM25."""

    def __init__(self, chunks_path: Path) -> None:
        self.chunks_path = chunks_path
        self.chunks: list[Chunk] = []
        self._term_frequencies: list[Counter[str]] = []
        self._document_lengths: list[int] = []
        self._document_frequencies: Counter[str] = Counter()
        self._average_length = 0.0
        self.reload()

    def reload(self) -> int:
        self.chunks = []
        self._term_frequencies = []
        self._document_lengths = []
        self._document_frequencies = Counter()

        if not self.chunks_path.exists():
            self._average_length = 0.0
            return 0

        with self.chunks_path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"Invalid JSON on line {line_number} of "
                        f"{self.chunks_path}"
                    ) from error

                text = str(record.get("text", "")).strip()
                url = str(record.get("url", "")).strip()
                if not text or not url:
                    continue

                chunk = Chunk(
                    text=text,
                    url=url,
                    title=str(record.get("title", "ATA University")).strip(),
                    section=str(record.get("section", "")).strip(),
                    language=str(record.get("language", "pl")).casefold(),
                    faculty=str(record.get("faculty", "")).strip(),
                )
                searchable_text = " ".join(
                    part
                    for part in (
                        chunk.title,
                        chunk.section,
                        chunk.faculty,
                        chunk.text,
                    )
                    if part
                )
                terms = tokenize(searchable_text)
                frequencies = Counter(terms)

                self.chunks.append(chunk)
                self._term_frequencies.append(frequencies)
                self._document_lengths.append(len(terms))
                self._document_frequencies.update(frequencies.keys())

        if self._document_lengths:
            self._average_length = sum(self._document_lengths) / len(
                self._document_lengths
            )
        else:
            self._average_length = 0.0
        return len(self.chunks)

    def search(
        self,
        question: str,
        language: str,
        top_k: int,
    ) -> list[SearchResult]:
        query_terms = expand_query_terms(tokenize(question))
        if not query_terms or not self.chunks:
            return []

        normalized_language = LANGUAGE_ALIASES.get(
            language.casefold().strip(), language.casefold().strip()
        )
        matching_language_exists = any(
            chunk.language.startswith(normalized_language)
            for chunk in self.chunks
        )

        results: list[SearchResult] = []
        document_count = len(self.chunks)
        average_length = max(self._average_length, 1.0)
        k1 = 1.5
        b = 0.75

        for index, chunk in enumerate(self.chunks):
            if matching_language_exists and not chunk.language.startswith(
                normalized_language
            ):
                continue

            frequencies = self._term_frequencies[index]
            document_length = self._document_lengths[index]
            score = 0.0

            for term in query_terms:
                term_frequency = frequencies.get(term, 0)
                if not term_frequency:
                    continue
                document_frequency = self._document_frequencies.get(term, 0)
                inverse_document_frequency = math.log(
                    1
                    + (document_count - document_frequency + 0.5)
                    / (document_frequency + 0.5)
                )
                denominator = term_frequency + k1 * (
                    1 - b + b * document_length / average_length
                )
                score += inverse_document_frequency * (
                    term_frequency * (k1 + 1) / denominator
                )

            if score > 0:
                results.append(SearchResult(chunk=chunk, score=score))

        results.sort(key=lambda result: result.score, reverse=True)
        return results[:top_k]


def score_to_confidence(score: float) -> float:
    if score <= 0:
        return 0.0
    return round(min(score / (score + 2.0), 1.0), 4)
