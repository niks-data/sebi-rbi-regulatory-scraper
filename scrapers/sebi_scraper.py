import asyncio
import csv
import json
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright
from lxml import html

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE_URL = "https://www.sebi.gov.in"
LIST_URL = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=2&ssid=9&smid=6"

# ─────────────────────────────────────────────
# USER CONFIGURABLE SETTINGS
# Clients can modify these without touching code
# ─────────────────────────────────────────────
CONFIG = {
    "row_xpath": "//table//tr[td]",
    "date_col": 0,
    "title_col": 1,
    "detail_link_xpath": ".//a/@href",
    "pdf_iframe_xpath": "//iframe/@src",
    "max_pages": 5,
    "request_delay": 2,
}

def clean_pdf_url(raw_url):
    """
    Extract actual PDF URL from any format:
    - Full: https://www.sebi.gov.in/web/?file=https://www.sebi.gov.in/sebi_data/...pdf
    - Slug: ../../../web/?file=https://www.sebi.gov.in/sebi_data/...pdf
    - Direct: https://www.sebi.gov.in/sebi_data/...pdf
    """
    if not raw_url:
        return ""

    # Try to extract embedded full URL after ?file=
    match = re.search(r'\?file=(https?://[^\s"\']+)', raw_url)
    if match:
        return match.group(1)

    # If it's already a direct PDF URL
    if raw_url.startswith("http") and ".pdf" in raw_url.lower():
        return raw_url

    # If it's a relative path ending in .pdf, build full URL
    if ".pdf" in raw_url.lower():
        clean = re.sub(r'^[\./]+', '', raw_url)
        return BASE_URL + "/" + clean

    return raw_url

async def get_pdf_url(page, detail_url, config):
    """Visit detail page and extract PDF URL via iframe XPath."""
    try:
        await page.goto(detail_url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(1500)
        content = await page.content()
        tree = html.fromstring(content)
        iframes = tree.xpath(config["pdf_iframe_xpath"])
        if iframes:
            raw = iframes[0].strip()
            return clean_pdf_url(raw)
    except Exception as e:
        print(f"  [!] Could not get PDF from {detail_url}: {e}")
    return ""

async def scrape_sebi_orders(config=CONFIG):
    results = []
    max_pages = config["max_pages"]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        list_page = await browser.new_page()
        detail_page = await browser.new_page()

        print(f"[SEBI] Opening orders listing...")
        await list_page.goto(LIST_URL, wait_until="networkidle", timeout=60000)
        await list_page.wait_for_timeout(2000)

        for page_num in range(1, max_pages + 1):
            print(f"[SEBI] Scraping page {page_num}...")

            content = await list_page.content()
            tree = html.fromstring(content)
            rows = tree.xpath(config["row_xpath"])
            print(f"[SEBI] Found {len(rows)} rows")

            for i, row in enumerate(rows):
                cols = row.xpath(".//td")
                if len(cols) < 2:
                    continue

                date = cols[config["date_col"]].text_content().strip()
                title = cols[config["title_col"]].text_content().strip()

                links = row.xpath(config["detail_link_xpath"])
                detail_url = ""
                pdf_url = ""

                if links:
                    href = links[0]
                    detail_url = BASE_URL + href if href.startswith("/") else href
                    print(f"  [{i+1}/{len(rows)}] Fetching PDF for: {title[:50]}...")
                    pdf_url = await get_pdf_url(detail_page, detail_url, config)
                    await asyncio.sleep(config["request_delay"])

                results.append({
                    "date": date,
                    "title": title,
                    "detail_url": detail_url,
                    "pdf_url": pdf_url,
                    "page_no": page_num,
                    "scraped_at": datetime.now().isoformat()
                })

            # Pagination
            next_btn = list_page.locator("a:has-text('Next')")
            if await next_btn.count() > 0:
                print(f"[SEBI] Moving to page {page_num + 1}...")
                await next_btn.first.click()
                await list_page.wait_for_load_state("networkidle")
                await list_page.wait_for_timeout(2000)
            else:
                print(f"[SEBI] No more pages after page {page_num}.")
                break

        await browser.close()

    return results

def save_results(results, fmt="csv"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if fmt == "csv":
        path = os.path.join(OUTPUT_DIR, f"sebi_orders_{timestamp}.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"[SEBI] Saved {len(results)} records → {path}")
    elif fmt == "json":
        path = os.path.join(OUTPUT_DIR, f"sebi_orders_{timestamp}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"[SEBI] Saved {len(results)} records → {path}")
    return path

if __name__ == "__main__":
    print("[SEBI] Starting scraper...")
    print(f"[SEBI] Config: max_pages={CONFIG['max_pages']}, delay={CONFIG['request_delay']}s")
    results = asyncio.run(scrape_sebi_orders(CONFIG))
    if results:
        print(f"\n[SEBI] Total records: {len(results)}")
        save_results(results, fmt="csv")
        save_results(results, fmt="json")
    else:
        print("[SEBI] No results found.")