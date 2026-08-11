"""
build_chunks.py

pages.json -> documents.jsonl + chunks.jsonl

Also tracks a crawl_state.json snapshot of each page's content_hash from
the previous run, so this run can report which pages are new, changed,
or unchanged. That is the basis for a "nightly cron: only re-embed
changed pages" workflow - the backend decides what to re-embed using
this diff.

Usage:
    python scraper/build_chunks.py
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

from chunker import chunk_markdown
from metadata import build_chunk_metadata

PAGES_PATH = "scraper/pages.json"
PDFS_PATH = "scraper/pdfs.json"
OUTPUT_DIR = "scraper/output"
CRAWL_STATE_PATH = os.path.join(OUTPUT_DIR, "crawl_state.json")


def detect_pdf_language(url: str) -> str:
    path = urlparse(url).path.lower()
    if path.startswith("/en/"):
        return "en"
    if path.startswith("/uk/"):
        return "uk"
    if path.startswith("/ru/"):
        return "ru"
    return "pl"


def load_previous_state():
    if not os.path.exists(CRAWL_STATE_PATH):
        return {}
    with open(CRAWL_STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(PAGES_PATH, "r", encoding="utf-8") as f:
        pages = json.load(f)

    previous_state = load_previous_state()
    new_state = {}

    run_timestamp = datetime.now(timezone.utc).isoformat()

    documents_path = os.path.join(OUTPUT_DIR, "documents.jsonl")
    chunks_path = os.path.join(OUTPUT_DIR, "chunks.jsonl")

    n_docs = 0
    n_chunks = 0
    n_unchanged = 0
    n_changed = 0
    n_new = 0

    with open(documents_path, "w", encoding="utf-8") as docs_f, \
         open(chunks_path, "w", encoding="utf-8") as chunks_f:

        for page in pages:
            markdown = page.get("markdown", "")
            if not markdown.strip():
                continue

            url = page["url"]
            content_hash = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
            new_state[url] = content_hash

            if url not in previous_state:
                n_new += 1
            elif previous_state[url] == content_hash:
                n_unchanged += 1
            else:
                n_changed += 1

            doc_record = {
                "url": url,
                "title": page["title"],
                "language": page.get("language", "pl"),
                "markdown": markdown,
                "last_modified": run_timestamp,
                "content_hash": content_hash,
            }
            docs_f.write(json.dumps(doc_record, ensure_ascii=False) + "\n")
            n_docs += 1

            for chunk in chunk_markdown(markdown, page["title"]):
                record = build_chunk_metadata(page, chunk, run_timestamp, content_hash)
                record["text"] = chunk["text"]
                chunks_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                n_chunks += 1

    with open(CRAWL_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(new_state, f, ensure_ascii=False, indent=2)

    print(f"[build_chunks] {n_docs} pages -> {documents_path}")
    print(f"[build_chunks] {n_chunks} chunks -> {chunks_path}")
    print(
        f"[build_chunks] change report: "
        f"{n_new} new, {n_changed} changed, {n_unchanged} unchanged"
    )
    print(f"[build_chunks] crawl_state.json updated -> {CRAWL_STATE_PATH}")

    if os.path.exists(PDFS_PATH):
        with open(PDFS_PATH, "r", encoding="utf-8") as f:
            pdf_urls = json.load(f)
        pdfs_out_path = os.path.join(OUTPUT_DIR, "pdfs.jsonl")
        with open(pdfs_out_path, "w", encoding="utf-8") as pdfs_f:
            for url in pdf_urls:
                pdfs_f.write(json.dumps(
                    {"url": url, "language": detect_pdf_language(url)},
                    ensure_ascii=False,
                ) + "\n")
        print(f"[build_chunks] {len(pdf_urls)} pdf urls -> {pdfs_out_path}")


if __name__ == "__main__":
    main()