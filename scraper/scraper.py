import json
import time
import re
import urllib.robotparser as robotparser
from collections import deque
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from cleaner import clean_html_to_markdown
from dynamic_scraper import get_dynamic_content
from config import (
    START_URLS,
    ALLOWED_DOMAINS,
    EXCLUDED_PATHS,
    CRAWL_DELAY_SECONDS,
    USER_AGENT,
    DYNAMIC_PATTERNS,
)


def should_skip_url(url):
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()
    return any(
        excluded in path
        for excluded in EXCLUDED_PATHS
    )


def normalize_url(url):
    parsed_url = urlparse(url)
    path = parsed_url.path or "/"
    if path != "/":
        path = path.rstrip("/") + "/"
    scheme = parsed_url.scheme or "https"
    return (
        f"{scheme}://"
        f"{parsed_url.netloc}"
        f"{path}"
    )


def needs_dynamic_scraping(url):
    path = urlparse(url).path
    return any(
        re.match(pattern, path)
        for pattern in DYNAMIC_PATTERNS
    )


def detect_language(url):
    path = urlparse(url).path.lower()
    if path.startswith("/en/"):
        return "en"
    if path.startswith("/uk/"):
        return "uk"
    if path.startswith("/ru/"):
        return "ru"
    return "pl"


def load_robot_parsers(domains):
    """Load robots.txt once per domain instead of re-fetching it every time."""
    parsers = {}
    for domain in domains:
        rp = robotparser.RobotFileParser()
        rp.set_url(f"https://{domain}/robots.txt")
        try:
            rp.read()
        except Exception:
            rp = None
        parsers[domain] = rp
    return parsers


def is_allowed_by_robots(url, robot_parsers):
    domain = urlparse(url).netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    rp = robot_parsers.get(domain)
    if rp is None:
        return True
    try:
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        return True


def crawl_site(start_urls, max_pages=50):
    visited = set()
    pdf_urls = set()
    errors = []

    robot_parsers = load_robot_parsers(ALLOWED_DOMAINS)

    normalized_starts = [
        normalize_url(url)
        for url in start_urls
    ]

    queued = set(normalized_starts)
    queue = deque(normalized_starts)

    pages = []

    while queue and len(visited) < max_pages:
        current_url = queue.popleft()
        queued.discard(current_url)

        if current_url in visited:
            continue

        if not is_allowed_by_robots(current_url, robot_parsers):
            print(
                "Skipped (robots.txt disallows):",
                current_url,
            )
            continue

        print(
            f"[{len(visited) + 1}/{max_pages}] Crawling:",
            current_url,
        )

        try:
            if needs_dynamic_scraping(current_url):
                print("  -> Using Playwright")
                try:
                    html, dynamic_text = get_dynamic_content(
                        current_url
                    )
                except Exception as first_error:
                    print(
                        "  -> First attempt failed, retrying once:",
                        first_error,
                    )
                    try:
                        html, dynamic_text = get_dynamic_content(
                            current_url
                        )
                    except Exception as second_error:
                        # Pricing widget never produced a real price
                        # (likely genuinely unset for this program).
                        # Fall back to the static page so we don't
                        # lose the page's other content entirely.
                        print(
                            "  -> Second attempt also failed, "
                            "falling back to static HTML:",
                            second_error,
                        )
                        response = requests.get(
                            current_url,
                            timeout=20,
                            headers={
                                "User-Agent": USER_AGENT,
                            },
                        )
                        response.raise_for_status()
                        html = response.text
                        dynamic_text = None

                if dynamic_text is not None:
                    print("\n--- DYNAMIC TEXT CHECK ---")
                    print(
                        "Length:",
                        len(dynamic_text),
                    )
                    print(
                        "Contains 890:",
                        "890" in dynamic_text,
                    )
                    print(
                        "Contains PLN:",
                        "PLN" in dynamic_text,
                    )
                    print("--- END CHECK ---\n")
                else:
                    print(
                        "  -> No dynamic text "
                        "(fell back to static HTML)"
                    )
            else:
                response = requests.get(
                    current_url,
                    timeout=20,
                    headers={
                        "User-Agent": USER_AGENT,
                    },
                )
                response.raise_for_status()
                html = response.text
                dynamic_text = None
        except Exception as error:
            print(
                "Failed:",
                current_url,
                "-",
                error,
            )
            errors.append({
                "url": current_url,
                "error": str(error),
            })
            time.sleep(CRAWL_DELAY_SECONDS)
            continue

        visited.add(current_url)

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        title = (
            soup.title.get_text(strip=True)
            if soup.title
            else "Untitled"
        )

        markdown = clean_html_to_markdown(
            html
        )

        if dynamic_text:
            dynamic_text = dynamic_text.strip()
            if dynamic_text:
                markdown = (
                    markdown
                    + "\n\n"
                    + (
                        "## Pricing information "
                        "(loaded via JS)\n\n"
                    )
                    + dynamic_text
                )

        if markdown:
            pages.append({
                "url": current_url,
                "title": title,
                "language": detect_language(
                    current_url
                ),
                "markdown": markdown,
            })

        # Discover more links on this page and queue the in-scope ones.
        for tag in soup.find_all(
            "a",
            href=True,
        ):
            absolute_url = urljoin(
                current_url,
                tag["href"],
            )

            parsed_url = urlparse(
                absolute_url
            )

            domain = parsed_url.netloc.lower()

            if domain.startswith("www."):
                domain = domain[4:]

            if domain not in ALLOWED_DOMAINS:
                continue

            # Collect PDF links separately instead of trying to crawl
            # them as HTML pages; PDF text extraction is a separate step.
            if parsed_url.path.lower().endswith(".pdf"):
                pdf_urls.add(absolute_url.split("#")[0])
                continue

            clean_url = normalize_url(
                absolute_url
            )

            if should_skip_url(clean_url):
                continue

            if (
                clean_url not in visited
                and clean_url not in queued
            ):
                queue.append(clean_url)
                queued.add(clean_url)

        # Politeness delay between requests.
        time.sleep(CRAWL_DELAY_SECONDS)

    return pages, sorted(pdf_urls), errors


def save_pages(pages):
    output_path = "scraper/pages.json"
    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            pages,
            file,
            ensure_ascii=False,
            indent=2,
        )
    print(
        f"\nSaved {len(pages)} pages "
        f"to {output_path}"
    )


def save_pdfs(pdf_urls):
    output_path = "scraper/pdfs.json"
    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            pdf_urls,
            file,
            ensure_ascii=False,
            indent=2,
        )
    print(
        f"Saved {len(pdf_urls)} PDF URLs "
        f"to {output_path}"
    )


def save_errors(errors):
    output_path = "scraper/output/errors.jsonl"
    import os
    os.makedirs("scraper/output", exist_ok=True)
    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        for error_record in errors:
            file.write(
                json.dumps(
                    error_record,
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(
        f"Saved {len(errors)} errors "
        f"to {output_path}"
    )


if __name__ == "__main__":
    print("Starting ATA crawler...")
    print("Start websites:")
    for url in START_URLS:
        print(" -", url)

    pages, pdf_urls, errors = crawl_site(
        START_URLS,
        max_pages=200,
    )
    save_pages(pages)
    save_pdfs(pdf_urls)
    save_errors(errors)

    print("\nCrawler finished.")