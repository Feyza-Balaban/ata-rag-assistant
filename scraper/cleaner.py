import re

from bs4 import BeautifulSoup
from markdownify import markdownify as md


def dedupe_blocks(text):
    """
    Remove repeated text/markdown blocks while preserving
    the order of their first appearance.
    """
    blocks = text.split("\n\n")

    seen = set()
    unique_blocks = []

    for block in blocks:
        cleaned_block = block.strip()

        if not cleaned_block:
            continue

        # Normalize whitespace only for comparison.
        normalized = re.sub(
            r"\s+",
            " ",
            cleaned_block,
        ).strip()

        if normalized in seen:
            continue

        seen.add(normalized)
        unique_blocks.append(cleaned_block)

    return "\n\n".join(unique_blocks)


def remove_noise_blocks(text):
    """
    Remove common non-content blocks such as countdown
    timers and cookie consent banners.
    """
    if not text:
        return ""

    # Remove ATA countdown / reservation widget.
    # This is based on the real text structure found
    # on the Informatyka page.
    text = re.sub(
        r"(?is)"
        r"\bstart\s*"
        r"pierwszego\s*"
        r"zarezerwuj\s*"
        r"liczba\s+miejsc\s*"
        r"start\s*"
        r"\d+\s*:\s*\d+\s*:\s*\d+\s*:\s*\d+\s*"
        r"studiów\s*"
        r"października\s*"
        r"swoje\s+miejsce\s*"
        r"ograniczona\s*"
        r"studiów",
        "",
        text,
        count=1,
    )

    blocks = re.split(
        r"\n\s*\n",
        text,
    )

    cleaned_blocks = []

    for block in blocks:
        stripped = block.strip()

        if not stripped:
            continue

        normalized = re.sub(
            r"\s+",
            " ",
            stripped,
        ).lower()

        # ---------------------------------------------
        # Countdown / reservation widget
        # ---------------------------------------------
        countdown_markers = [
            "pierwszego",
            "zarezerwuj",
            "liczba miejsc",
        ]

        countdown_hits = sum(
            marker in normalized
            for marker in countdown_markers
        )

        if countdown_hits >= 2:
            continue

        # ---------------------------------------------
        # Cookie / consent banners
        # ---------------------------------------------
        cookie_markers = [
            "cookie",
            "cookies",
            "plików cookie",
            "plików cookies",
        ]

        consent_markers = [
            "akceptuj",
            "zaakceptuj",
            "odrzuć",
            "ustawienia",
            "zgadzam",
            "accept",
            "reject",
            "settings",
            "consent",
        ]

        contains_cookie = any(
            marker in normalized
            for marker in cookie_markers
        )

        contains_consent = any(
            marker in normalized
            for marker in consent_markers
        )

        if contains_cookie and contains_consent:
            continue

        cleaned_blocks.append(stripped)

    return "\n\n".join(cleaned_blocks)


def clean_text_for_rag(text):
    """
    Shared cleanup for both normal markdown content
    and dynamically rendered text.
    """
    if not text:
        return ""

    text = remove_noise_blocks(text)

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    text = dedupe_blocks(text)

    return text.strip()


def clean_html_to_markdown(html):
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    # Remove elements that are not useful for RAG.
    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "nav",
        "footer",
        "form",
    ]):
        tag.decompose()

    # Prefer the main page content when available.
    content = soup.find("main")

    if content is None:
        content = soup.body

    if content is None:
        return ""

    markdown = md(
        str(content),
        heading_style="ATX",
    )

    # Remove markdown images.
    markdown = re.sub(
        r"!\[[^\]]*\]\([^)]+\)",
        "",
        markdown,
    )

    markdown = clean_text_for_rag(
        markdown
    )

    return markdown.strip()