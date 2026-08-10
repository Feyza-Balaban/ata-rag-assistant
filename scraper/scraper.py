import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from cleaner import clean_html_to_markdown
from collections import deque

URL = "https://akademiata.pl"

response = requests.get(URL, timeout=20)

print("Status code:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

print("Page title:", soup.title.string if soup.title else "No title found")

EXCLUDED_PATHS = [
    "/wp-admin",
    "/wp-login",
    "/feed",
    "/search",
    "/tag/",
    "/category/",
    "/aktualnosci/",
]

def should_skip_url(url):
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()

    return any(excluded in path for excluded in EXCLUDED_PATHS)

def normalize_url(url):
    parsed_url = urlparse(url)

    path = parsed_url.path or "/"

    if path != "/":
        path = path.rstrip("/") + "/"

    return f"https://akademiata.pl{path}"

def crawl_site(start_url, max_pages=50):
    visited = set()
    queue = deque([normalize_url(start_url)])
    discovered = set()

    while queue and len(visited) < max_pages:
        current_url = queue.popleft()

        if current_url in visited:
            continue

        print("Crawling:", current_url)

        try:
            page_response = requests.get(current_url, timeout=20)
            page_response.raise_for_status()
        except requests.RequestException as error:
            print("Failed:", current_url, "-", error)
            continue

        visited.add(current_url)

        page_soup = BeautifulSoup(page_response.text, "html.parser")

        for tag in page_soup.find_all("a", href=True):
            absolute_url = urljoin(current_url, tag["href"])
            parsed_url = urlparse(absolute_url)

            if parsed_url.netloc not in ["akademiata.pl", "www.akademiata.pl"]:
                continue

            clean_url = normalize_url(absolute_url)

            if should_skip_url(clean_url):
                continue

            discovered.add(clean_url)

            if clean_url not in visited:
                queue.append(clean_url)

    return visited, discovered

links = set()

for tag in soup.find_all("a", href=True):
    absolute_url = urljoin(URL, tag["href"])
    parsed_url = urlparse(absolute_url)

    if parsed_url.netloc in ["akademiata.pl", "www.akademiata.pl"]:
        clean_url = normalize_url(absolute_url)

    if not should_skip_url(clean_url):
        links.add(clean_url)

print("Internal links found:", len(links))

important_links = [
    link for link in sorted(links)
    if any(keyword in link.lower() for keyword in [
        "informatyka",
        "computer",
        "czesne",
        "tuition",
    ])
]

print("\n--- IMPORTANT RAG LINKS ---")

for link in important_links:
    print(link)

print("Important links found:", len(important_links))

for link in sorted(links)[:20]:
    print(link)

    markdown = clean_html_to_markdown(response.text)

print("\n--- CLEAN MARKDOWN PREVIEW ---\n")
print(markdown[:2000])

pages = []

print("\n--- SCRAPING TEST PAGES ---\n")

for link in sorted(links)[:5]:
    try:
        page_response = requests.get(link, timeout=20)
        page_response.raise_for_status()

        page_soup = BeautifulSoup(page_response.text, "html.parser")

        title = (
            page_soup.title.get_text(strip=True)
            if page_soup.title
            else "Untitled"
        )

        page_markdown = clean_html_to_markdown(page_response.text)

        language = "en" if "/en/" in link else "pl"

        pages.append({
            "url": link,
            "title": title,
            "language": language,
            "markdown": page_markdown,
        })

        print("Scraped:", link)

    except requests.RequestException as error:
        print("Failed:", link, "-", error)

with open("scraper/pages.json", "w", encoding="utf-8") as file:
    json.dump(pages, file, ensure_ascii=False, indent=2)

print("\nSaved pages to scraper/pages.json")

print("\n--- BFS CRAWL TEST ---\n")

visited_pages, discovered_links = crawl_site(URL, max_pages=20)

print("\nVisited pages:", len(visited_pages))
print("Discovered links:", len(discovered_links))


