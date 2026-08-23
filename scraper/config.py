"""
ATA RAG Scraper - central configuration
"""

# Each language is crawled separately, with its own budget, so that a
# single BFS crawl dominated by Polish pages doesn't starve the other
# languages of their max_pages allowance.
LANGUAGE_START_URLS = {
    "pl": [
        "https://akademiata.pl/",
        "https://uczelnia.akademiata.pl/",
        "https://akademiata.pl/oferta/studia-1-stopnia/informatyka/",
    ],
    "en": ["https://akademiata.pl/en/"],
    "uk": ["https://akademiata.pl/uk/"],
    "ru": ["https://akademiata.pl/ru/"],
}

MAX_PAGES_PER_LANGUAGE = 150

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
# Covers all 4 languages - the original version only covered pl/en and
# silently missed uk/ru pricing data.
DYNAMIC_PATTERNS = [
    r"^/oferta/studia-1-stopnia/[^/]+/$",
    r"^/oferta/studia-2-stopnia/[^/]+/$",
    r"^/studia-podyplomowe/[^/]+/$",
    r"^/studia-mba/[^/]+/$",
    r"^/kalkulator-czesnego/$",
    r"^/en/offer/bachelor/[^/]+/$",
    r"^/en/offer/master/[^/]+/$",
    r"^/en/tuition-calculator/$",
    r"^/uk/propozyciya/bakalavrat/[^/]+/$",
    r"^/uk/propozyciya/mahistratura/[^/]+/$",
    r"^/uk/kalkulator-czesnego/$",
    r"^/ru/predlozhenie/bakalavriat/[^/]+/$",
    r"^/ru/predlozhenie/magistratura/[^/]+/$",
    r"^/ru/kalkulator-czesnego/$",
]