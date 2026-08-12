"""
ATA RAG Scraper - central configuration
"""

START_URLS = [
    "https://akademiata.pl/",
    "https://uczelnia.akademiata.pl/",
    "https://akademiata.pl/oferta/studia-1-stopnia/informatyka/",
]

ALLOWED_DOMAINS = [
    "akademiata.pl",
    "uczelnia.akademiata.pl",
]

EXCLUDED_PATHS = [
    "/wp-admin",
    "/wp-login",
    "/feed",
    "/search",
    "/tag/",
    "/category/",
    "/aktualnosci/",
]

CRAWL_DELAY_SECONDS = 0.5
USER_AGENT = "Mozilla/5.0 ATA-RAG-Scraper/1.0"

# URL path patterns that require JavaScript rendering (Playwright) because
# the tuition/pricing widget on these pages loads its data client-side.
# See scraper/debug/compare_dynamic.py and poll_probe.py for how these
# were determined.
DYNAMIC_PATTERNS = [
    r"^/oferta/studia-1-stopnia/[^/]+/$",
    r"^/oferta/studia-2-stopnia/[^/]+/$",
    r"^/studia-podyplomowe/[^/]+/$",
    r"^/studia-mba/[^/]+/$",
    r"^/kalkulator-czesnego/$",
    r"^/en/offer/bachelor/[^/]+/$",
    r"^/en/offer/master/[^/]+/$",
]