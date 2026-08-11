"""
Metadata enrichment for chunks produced from pages.json.
Adds url, title, section, faculty, language, lastUpdated, source,
content_hash to every chunk so the backend can filter/cite by them.
"""
from urllib.parse import urlparse

FACULTY_HINTS = {
    "architektura": "Architektura",
    "informatyka": "Informatyka",
    "cyberbezpieczenstwo": "Informatyka",
    "sztuczna-inteligencja": "Informatyka",
    "programowanie": "Informatyka",
    "zarzadzanie": "Zarządzanie",
    "budownictwo": "Budownictwo",
    "logistyka": "Logistyka",
    "ochrona-srodowiska": "Ochrona środowiska",
    "wzornictwo": "Wzornictwo",
    "kandydat": "Rekrutacja",
    "zasady-rekrutacji": "Rekrutacja",
    "kalkulator-czesnego": "Czesne / opłaty",
    "kontakt": "Kontakt",
    "erasmus": "Erasmus",
    "dziekanat": "Dziekanat",
    "wazne-dokumenty": "Dokumenty / Regulaminy",
    "aktualnosci": "Aktualności",
}


def detect_faculty(url: str) -> str:
    path = urlparse(url).path.lower()
    for hint, label in FACULTY_HINTS.items():
        if hint in path:
            return label
    return "Ogólne"


def build_chunk_metadata(page: dict, chunk: dict, last_modified: str, content_hash: str) -> dict:
    return {
        "url": page["url"],
        "title": page["title"],
        "section": chunk["section"],
        "faculty": detect_faculty(page["url"]),
        "language": page.get("language", "pl"),
        "lastUpdated": last_modified,
        "source": "website",
        "content_hash": content_hash,
    }