# Scraper

## Scraper: web scraping, cleaning, chunking, metadata

### What this covers (per task breakdown)
- Web scraper (requests + Playwright hybrid)
- Recursive crawling with URL filtering
- Duplicate/noise content handling
- HTML → clean Markdown
- Dynamic (JS-rendered) tuition/pricing extraction
- Heading-based intelligent chunking
- Chunk metadata (section, faculty, language, lastUpdated, source, content_hash)
- Final JSON/JSONL output for backend ingestion
- Nightly re-crawl support (content_hash diffing)
- Coolify-ready (Dockerfile)

### Domain correction
The original spec PDF referenced `akademiata.edu.pl` — the real, correct
domain is **`akademiata.pl`**. All code targets the correct domain,
covering both `akademiata.pl` and `uczelnia.akademiata.pl` subdomains.

### How to run
pip install -r scraper/requirements.txt
playwright install --with-deps chromium
python scraper/scraper.py # crawls the site -> pages.json, pdfs.json
python scraper/build_chunks.py # pages.json -> documents.jsonl, chunks.jsonl

### Output contract (for backend/embedding ingestion)
`scraper/output/documents.jsonl` — one page per line:
```json
{"url": "...", "title": "...", "language": "pl", "markdown": "...",
 "last_modified": "...", "content_hash": "..."}
```

`scraper/output/chunks.jsonl` — one chunk per line, **this is the file to embed**:
```json
{"url": "...", "title": "...", "section": "Informatyka > Fees",
 "faculty": "Informatyka", "language": "pl", "lastUpdated": "...",
 "source": "website", "content_hash": "...", "text": "..."}
```

`scraper/output/pdfs.jsonl` — discovered PDF URLs (content not yet extracted, see Known Limitations).

`scraper/output/crawl_state.json` — url → content_hash map from the last run,
used to report which pages are new/changed/unchanged on the next run.

`scraper/output/errors.jsonl` — any URL that failed to fetch/parse, with the reason.

### Current run stats (last full crawl)
- 200 pages crawled, 0 errors
- 4140 chunks generated
- 33 PDF URLs discovered

### Known limitations / not yet done
- **PDF content extraction is not implemented.** We only collect PDF URLs
  (`pdfs.jsonl`); OCR/text extraction from PDFs is a separate follow-up task.
- **`/aktualnosci/` (news) pages are excluded on purpose** — decided this
  is out of scope for the MVP chatbot's core use case (tuition/admissions/programs).
- Crawl is currently capped at `max_pages=200` (`scraper/scraper.py`,
  `__main__` block) — this covered the site well in testing, but if the
  site grows, this number may need to be raised.
- The Dockerfile has not been build-tested locally; it should work but
  hasn't been verified end-to-end against Coolify yet.
- Nightly re-crawl currently requires manually running `scraper.py` then
  `build_chunks.py`; actual scheduling (cron / Coolify scheduled task)
  is not yet wired up.

### Debug/exploration scripts
`scraper/debug/` contains scripts used to diagnose the dynamic pricing
widget's load timing and content structure (`compare_dynamic.py`,
`poll_probe.py`, `timing_probe.py`, etc.). Not part of the production
pipeline, kept for reference.