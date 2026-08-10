import re

from bs4 import BeautifulSoup
from markdownify import markdownify as md


def clean_html_to_markdown(html):
    soup = BeautifulSoup(html, "html.parser")

    # Remove elements that are not useful for RAG
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

    # Prefer the main page content when available
    content = soup.find("main")

    if content is None:
        content = soup.body

    if content is None:
        return ""

    markdown = md(
        str(content),
        heading_style="ATX",
    )

        # Remove markdown images
    markdown = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", markdown)

    # Remove excessive empty lines
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)

    return markdown.strip()