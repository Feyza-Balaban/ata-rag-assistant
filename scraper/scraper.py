import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

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

links = set()

for tag in soup.find_all("a", href=True):
    absolute_url = urljoin(URL, tag["href"])
    parsed_url = urlparse(absolute_url)

    if parsed_url.netloc in ["akademiata.pl", "www.akademiata.pl"]:
        clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

    if not should_skip_url(clean_url):
        links.add(clean_url)

print("Internal links found:", len(links))

for link in sorted(links)[:20]:
    print(link)