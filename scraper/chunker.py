"""
Heading-based chunking.
Splits markdown by headings instead of a fixed character count, so each
chunk is a coherent section (e.g. "Admissions > Required documents")
rather than an arbitrary slice that might cut a sentence in half.

If a single section is still very long (e.g. a big regulation article),
it is further split by paragraph, but the heading breadcrumb is
preserved on every sub-chunk so retrieval context isn't lost.
"""
import re

MAX_CHUNK_CHARS = 1800
MIN_CHUNK_CHARS = 15

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def _split_into_sections(markdown: str):
    sections = []
    current_headings = []
    current_body = []

    def flush():
        body = "\n".join(current_body).strip()
        breadcrumb = " > ".join(h[1] for h in current_headings)
        sections.append((breadcrumb, body))

    for line in markdown.splitlines():
        match = HEADING_RE.match(line.strip())
        if match:
            flush()
            level = len(match.group(1))
            text = match.group(2).strip()
            current_headings = [h for h in current_headings if h[0] < level]
            current_headings.append((level, text))
            current_body = []
        else:
            current_body.append(line)
    flush()

    return [(section, body) for section, body in sections if body.strip()]


def _split_long_body(body: str, max_chars: int):
    paragraphs = [p for p in body.split("\n\n") if p.strip()]
    chunks, current = [], ""
    for p in paragraphs:
        if current and len(current) + len(p) + 2 > max_chars:
            chunks.append(current.strip())
            current = p
        else:
            current = f"{current}\n\n{p}" if current else p
    if current.strip():
        chunks.append(current.strip())
    return chunks or [body]


def chunk_markdown(markdown: str, page_title: str):
    sections = _split_into_sections(markdown)
    if not sections:
        sections = [("", markdown)]

    def _normalize(s: str) -> str:
        return s.strip().lower()

    chunks = []
    for breadcrumb, body in sections:
        if not breadcrumb:
            full_breadcrumb = page_title
        elif _normalize(breadcrumb) == _normalize(page_title) or \
                _normalize(breadcrumb).startswith(_normalize(page_title) + " > "):
            full_breadcrumb = breadcrumb
        else:
            full_breadcrumb = f"{page_title} > {breadcrumb}"
        pieces = (
            _split_long_body(body, MAX_CHUNK_CHARS)
            if len(body) > MAX_CHUNK_CHARS
            else [body]
        )
        for piece in pieces:
            if len(piece.strip()) >= MIN_CHUNK_CHARS:
                chunks.append({"section": full_breadcrumb, "text": piece.strip()})

    return chunks


if __name__ == "__main__":
    sample = (
        "# Admissions\n\nThe admission process starts in June.\n\n"
        "## Required documents\n\n- ID card\n- Diploma\n- Photo\n\n"
        "## Deadlines\n\nApplications close on September 30."
    )
    for c in chunk_markdown(sample, "Admissions 2026"):
        print("---", c["section"])
        print(c["text"])