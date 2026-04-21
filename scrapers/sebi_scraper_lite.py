import requests
import os
import time
from datetime import datetime
from lxml import html

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE_URL = "https://www.sebi.gov.in"
LIST_URL = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=2&ssid=9&smid=6"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.sebi.gov.in",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def scrape_sebi_orders_lite(max_pages=3):
    results = []

    for page_num in range(1, max_pages + 1):
        print(f"[SEBI] Scraping page {page_num}...")
        # SEBI uses page index starting from 0 for page 2 onwards
        if page_num == 1:
            url = LIST_URL
        else:
            url = f"{BASE_URL}/sebiweb/home/HomeAction.do?doListing=yes&sid=2&ssid=9&smid=6&pageno={page_num - 1}"

        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            tree = html.fromstring(response.content)
            rows = tree.xpath("//table//tr[td]")
            print(f"[SEBI] Found {len(rows)} rows on page {page_num}")

            if not rows:
                print(f"[SEBI] No rows found, stopping.")
                break

            for row in rows:
                cols = row.xpath(".//td")
                if len(cols) < 2:
                    continue
                date = cols[0].text_content().strip()
                title = cols[1].text_content().strip()
                links = row.xpath(".//a/@href")
                detail_url = ""
                if links:
                    href = links[0]
                    detail_url = BASE_URL + href if href.startswith("/") else href

                results.append({
                    "date": date,
                    "title": title,
                    "detail_url": detail_url,
                    "page_no": page_num,
                    "scraped_at": datetime.now().isoformat()
                })

            time.sleep(1)

        except Exception as e:
            print(f"[SEBI] Error on page {page_num}: {e}")
            break

    return results

if __name__ == "__main__":
    results = scrape_sebi_orders_lite(max_pages=3)
    print(f"Total: {len(results)}")