from playwright.sync_api import sync_playwright

from cleaner import clean_text_for_rag


PRICE_SELECTOR = "#kalkulator-content"


def get_dynamic_content(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(service_workers="block")
        page = context.new_page()

        interesting_responses = []

        def handle_response(response):
            response_url = response.url.lower()
            keywords = [
                "price", "pricing", "tuition", "fee", "fees",
                "czes", "opl", "calculator", "kalkulator", "ajax", "api",
            ]
            if any(keyword in response_url for keyword in keywords):
                print("  -> RESPONSE:", response.status, response.url)
                interesting_responses.append(response.url)

        page.on("response", handle_response)

        try:
            print("  -> Opening dynamic page...")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            price_locator = page.locator(PRICE_SELECTOR)

            price_locator.wait_for(state="attached", timeout=30000)

            print("  -> Scrolling price widget into view...")
            price_locator.scroll_into_view_if_needed(timeout=10000)

            # Wait until the widget has a REAL price, not the empty
            # placeholder state and not the raw JSON i18n blob.
            page.wait_for_function(
                """
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
                """,
                arg=PRICE_SELECTOR,
                timeout=30000,
            )

            page.wait_for_timeout(500)

            print("\n--- INTERESTING NETWORK RESPONSES ---")
            for response_url in interesting_responses:
                print(response_url)
            print("--- END NETWORK RESPONSES ---\n")

            html = page.content()

            if price_locator.count() > 0:
                print("  -> Using price selector:", PRICE_SELECTOR)
                text = price_locator.first.inner_text()
            else:
                print("  -> Price selector not found.")
                print("  -> Falling back to body text.")
                text = page.locator("body").inner_text()

            text = clean_text_for_rag(text)

            return html, text

        finally:
            browser.close()