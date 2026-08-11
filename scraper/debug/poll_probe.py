"""
FAZ 2C debug - poll_probe.py

Amac: yeni wait_for_function kosulumuzun TAM OLARAK ne zaman true
donduugunu ve o anki metnin ne oldugunu yakalamak. Ayrica kosul true
olduktan 500ms ve 1500ms sonra metin degisiyor mu (flicker var mi)
onu da kontrol ediyoruz.

Calistirma:
    python scraper/poll_probe.py
"""
from playwright.sync_api import sync_playwright

URL = "https://akademiata.pl/oferta/studia-1-stopnia/informatyka/"
SELECTOR = "#kalkulator-content"

CONDITION_JS = """
(selector) => {
    const element = document.querySelector(selector);
    if (!element) {
        return false;
    }
    const text = element.innerText || "";
    const hasRealPrice = /zł\\/m-c|\\d{3,5}\\s*(zł|PLN)/i.test(text);
    const isEmptyState = text.includes("Cennik w przygotowaniu");
    const isRawJson = text.includes('"ctaMore"');
    return hasRealPrice && !isEmptyState && !isRawJson;
}
"""


def snapshot(page, label):
    locator = page.locator(SELECTOR)
    if locator.count() == 0:
        print(f"  [{label}] element not in DOM")
        return
    try:
        text = locator.first.inner_text()
    except Exception as e:
        text = f"[ERROR: {e}]"
    has_890 = "890" in text
    has_placeholder = "Cennik w przygotowaniu" in text
    has_json = '"ctaMore"' in text
    preview = text[:200].replace("\n", " | ")
    print(f"  [{label}] len={len(text)} 890={has_890} placeholder={has_placeholder} json={has_json}")
    print(f"      preview: {preview}...")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Opening {URL} ...")
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)

        price_locator = page.locator(SELECTOR)
        price_locator.wait_for(state="attached", timeout=30000)

        print("Scrolling into view...")
        price_locator.scroll_into_view_if_needed(timeout=10000)

        print("Polling condition every 300ms until true (max 25s)...")
        import time
        start = time.time()
        became_true_at = None
        while time.time() - start < 25:
            result = page.evaluate(CONDITION_JS, SELECTOR)
            elapsed = round((time.time() - start) * 1000)
            if result:
                became_true_at = elapsed
                print(f"\n>>> Condition became TRUE at t={elapsed}ms")
                snapshot(page, f"AT TRUE (t={elapsed}ms)")
                break
            page.wait_for_timeout(300)

        if became_true_at is None:
            print("\n>>> Condition NEVER became true within 25s")
            snapshot(page, "FINAL STATE (25s)")
        else:
            page.wait_for_timeout(500)
            snapshot(page, f"+500ms after true")
            page.wait_for_timeout(1000)
            snapshot(page, f"+1500ms after true")
            page.wait_for_timeout(2000)
            snapshot(page, f"+3500ms after true")

        browser.close()


if __name__ == "__main__":
    main()