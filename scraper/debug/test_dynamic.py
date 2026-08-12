from playwright.sync_api import sync_playwright

URL = "https://akademiata.pl/oferta/studia-1-stopnia/informatyka/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    print("Opening page...")

    page.goto(
        URL,
        wait_until="networkidle",
        timeout=60000
    )

    print("Page loaded.")

    text = page.locator("body").inner_text()

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    keywords = [
        "PLN",
        "zł",
        "opłat",
        "czesn",
        "cena",
        "mies",
        "semestr",
        "rok",
        "promoc",
    ]

    print("\n--- PRICE CONTEXT ---\n")

    for i, line in enumerate(lines):
        if any(keyword.lower() in line.lower() for keyword in keywords):

            start = max(0, i - 3)
            end = min(len(lines), i + 4)

            print("-----") 

            for context_line in lines[start:end]:
                print(context_line)

    browser.close()