# merged_clean_scraper.py
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import os

def clean_filename(url: str) -> str:
    """Converts URL to a safe filename format."""
    name = url.replace("\\", "_").replace("/", "_").replace(".", "-").replace(":", "").replace("?", "_")
    if not name.lower().endswith(".html"):
        name += ".html"
    return name

# def auto_handle_modals(page):
#     """Try to auto-handle location or cookie modals if detected."""
#     try:
#         # Common selectors seen on food websites
#         possible_buttons = [``
#             "button:has-text('Allow')",
#             "button:has-text('Accept')",
#             "button:has-text('OK')",
#             "button:has-text('Select')",
#             "button:has-text('Continue')",
#             "button:has-text('Close')",
#             "button:has-text('Got it')",
#             ".modal button",
#             ".popup button"
#         ]
#         for selector in possible_buttons:
#             buttons = page.query_selector_all(selector)
#             if buttons:
#                 for b in buttons:
#                     try:
#                         b.click(timeout=1000)
#                     except Exception:
#                         pass
#     except Exception:
#         pass

def save_clean_html(url: str, output_file: str, timeout: int = 60000):
    """Fetch page using Playwright (robust JS rendering) and clean HTML with BeautifulSoup."""
    try:
        with sync_playwright() as p:
            # Headless browser
            browser = p.chromium.launch(headless=True, args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
            ])

            # Realistic context
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
                java_script_enabled=True,
            )

            # Hide webdriver flag
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => false});"
            )

            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            # auto_handle_modals(page)

            # Get outer HTML and clean, and remove CSS and inline styles
            cleaned_html = page.evaluate("""
                    () => {
                        // Remove CSS files and <style> tags
                        document.querySelectorAll('style, link[rel="stylesheet"], link[type="text/css"]').forEach(n => n.remove());

                        // Remove inline style attributes
                        const all = document.querySelectorAll('*');
                        all.forEach(el => {
                            if (el.hasAttribute('style')) el.removeAttribute('style');
                        });

                        return document.documentElement.outerHTML;
                    }
                """)
            soup = BeautifulSoup(cleaned_html, "html.parser")
            pretty_html = soup.prettify()

            # Save to file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(pretty_html)

            print(f"✅ Clean HTML saved to: {output_file}")

            page.close()
            context.close()
            browser.close()

    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")

def scrape_links_from_file(file_path: str):
    """Reads links from file and scrapes HTML for each link using robust save_clean_html."""
    folder_name = os.path.splitext(os.path.basename(file_path))[0]
    output_dir = os.path.join("OutputCleanHTML", folder_name)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n📂 Output directory: {output_dir}")

    # Read all URLs
    with open(file_path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        print("❌ No URLs found in the file.")
        return

    for url in urls:
        print(f"\n🌐 Scraping: {url}")
        filename = clean_filename(url)
        save_path = os.path.join(output_dir, filename)
        save_clean_html(url, save_path)

if __name__ == "__main__":
    file_path = r"Links\honda_test.txt"
    scrape_links_from_file(file_path)
