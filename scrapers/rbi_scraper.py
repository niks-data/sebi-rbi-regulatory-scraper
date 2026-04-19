import asyncio
import csv
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright
from lxml import html

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE_URL = "https://www.rbi.org.in/Scripts/"
LIST_URL = "https://www.rbi.org.in/Scripts/NotificationUser.aspx"

# ─────────────────────────────────────────────
# USER CONFIGURABLE SETTINGS
# ─────────────────────────────────────────────
CONFIG = {
    "row_xpath": "//table//tr[td]",
    "max_pages": 5,
    "request_delay": 2,
}

async def scrape_rbi_notifications(config=CONFIG):
    results = []
    max_pages = config["max_pages"]
    current_date = ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"[RBI] Opening notifications page...")
        await page.goto(LIST_URL, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(2000)

        for page_num in range(1, max_pages + 1):
            print(f"[RBI] Scraping page {page_num}...")

            content = await page.content()
            tree = html.fromstring(content)
            rows = tree.xpath(config["row_xpath"])
            print(f"[RBI] Found {len(rows)} rows")

            for row in rows:
                cols = row.xpath(".//td")
                links = row.xpath(".//a/@href")

                # Date header row
                if len(cols) == 1 and len(links) == 0:
                    current_date = cols[0].text_content().strip()
                    continue

                # Notification row
                if len(cols) == 2 and len(links) >= 1:
                    title = cols[0].text_content().strip()
                    size = cols[1].text_content().strip()

                    # Detail URL
                    detail_link = links[0]
                    if detail_link.startswith("http"):
                        detail_url = detail_link
                    else:
                        detail_url = BASE_URL + detail_link

                    # Direct PDF URL (second link)
                    pdf_url = links[1] if len(links) >= 2 else ""

                    results.append({
                        "date": current_date,
                        "title": title,
                        "size": size,
                        "detail_url": detail_url,
                        "pdf_url": pdf_url,
                        "page_no": page_num,
                        "scraped_at": datetime.now().isoformat()
                    })

            # Pagination — RBI uses a different pattern, look for next page link
            next_btn = page.locator("a:has-text('Next')")
            count = await next_btn.count()
            if count > 0:
                print(f"[RBI] Moving to page {page_num + 1}...")
                await next_btn.first.click()
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(config["request_delay"] * 1000)
            else:
                print(f"[RBI] No more pages after page {page_num}.")
                break

        await browser.close()

    return results

def save_results(results, fmt="csv"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if fmt == "csv":
        path = os.path.join(OUTPUT_DIR, f"rbi_notifications_{timestamp}.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"[RBI] Saved {len(results)} records → {path}")
    elif fmt == "json":
        path = os.path.join(OUTPUT_DIR, f"rbi_notifications_{timestamp}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"[RBI] Saved {len(results)} records → {path}")
    return path

if __name__ == "__main__":
    print("[RBI] Starting scraper...")
    print(f"[RBI] Config: max_pages={CONFIG['max_pages']}, delay={CONFIG['request_delay']}s")
    results = asyncio.run(scrape_rbi_notifications(CONFIG))
    if results:
        print(f"\n[RBI] Total records: {len(results)}")
        save_results(results, fmt="csv")
        save_results(results, fmt="json")
    else:
        print("[RBI] No results found.")