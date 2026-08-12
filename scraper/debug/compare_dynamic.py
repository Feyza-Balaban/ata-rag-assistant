import requests

from dynamic_scraper import get_dynamic_content


TEST_URLS = [
    "https://akademiata.pl/oferta/studia-1-stopnia/informatyka/",
    "https://akademiata.pl/oferta/studia-1-stopnia/wroclaw-informatyka/",
    "https://akademiata.pl/oferta/studia-1-stopnia/ai-i-automatyzacja/",
    "https://akademiata.pl/kalkulator-czesnego/",
    "https://uczelnia.akademiata.pl/student/wazne-dokumenty/",
    "https://uczelnia.akademiata.pl/uczelnia/erasmus/",
]


PRICE_MARKERS = [
    "zł",
    "PLN",
    "zł/m-c",
]


CONTENT_MARKERS = {
    "https://uczelnia.akademiata.pl/student/wazne-dokumenty/": [
        "Ważne dokumenty",
        "Regulaminy",
        "Regulamin studiów (obowiązuje od 1.10.2025 r.)",
        "Regulamin dyplomowania (obowiązuje od 6.10.2025 r.)",
        "Formularz druku zgłoszenia pracy dyplomowej",
    ],
    "https://uczelnia.akademiata.pl/uczelnia/erasmus/": [
        "ERASMUS",
        "Koordynatorzy",
        "dr Marta Drozdowska, prof. ATA",
        "marta.drozdowska@akademiata.pl",
        "paulina.waz@akademiata.pl",
    ],
}


def find_markers(text):
    text_lower = text.lower()

    return [
        marker
        for marker in PRICE_MARKERS
        if marker.lower() in text_lower
    ]


def find_content_markers(url, text):
    expected_markers = CONTENT_MARKERS.get(url, [])
    text_lower = text.lower()

    return [
        marker
        for marker in expected_markers
        if marker.lower() in text_lower
    ]


for url in TEST_URLS:
    print("\n" + "=" * 70)
    print("URL:", url)

    static_text = ""

    # --------------------------------------------------
    # requests / static HTML
    # --------------------------------------------------
    try:
        response = requests.get(
            url,
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0 ATA-RAG-Scraper/1.0"
            },
        )

        response.raise_for_status()

        static_text = response.text

        static_price_markers = find_markers(
            static_text
        )

        static_content_markers = find_content_markers(
            url,
            static_text,
        )

        print("requests status:", response.status_code)
        print("requests markers:", static_price_markers)
        print(
            "requests contains 890:",
            "890" in static_text,
        )
        print(
            "requests content markers:",
            static_content_markers,
        )
        print(
            "requests length:",
            len(static_text),
        )

    except Exception as error:
        print("requests ERROR:", error)

    # --------------------------------------------------
    # Playwright / rendered content
    # --------------------------------------------------
    try:
        _, dynamic_text = get_dynamic_content(url)

        dynamic_price_markers = find_markers(
            dynamic_text
        )

        dynamic_content_markers = find_content_markers(
            url,
            dynamic_text,
        )

        print(
            "playwright markers:",
            dynamic_price_markers,
        )
        print(
            "playwright contains 890:",
            "890" in dynamic_text,
        )
        print(
            "playwright content markers:",
            dynamic_content_markers,
        )
        print(
            "playwright text length:",
            len(dynamic_text),
        )

    except Exception as error:
        print("playwright ERROR:", error)