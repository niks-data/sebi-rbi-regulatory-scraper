import requests
import os
from datetime import datetime
from lxml import html

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE_URL = "https://www.rbi.org.in/Scripts/"
LIST_URL = "https://www.rbi.org.in/Scripts/NotificationUser.aspx"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

def scrape_rbi_notifications_lite(max_pages=1):
    results = []
    current_date = ""

    print(f"[RBI] Scraping notifications...")
    try:
        response = requests.get(LIST_URL, headers=HEADERS, timeout=30)
        tree = html.fromstring(response.content)
        rows = tree.xpath("//table//tr[td]")
        print(f"[RBI] Found {len(rows)} rows")

        for row in rows:
            cols = row.xpath(".//td")
            links = row.xpath(".//a/@href")

            if len(cols) == 1 and len(links) == 0:
                current_date = cols[0].text_content().strip()
                continue

            if len(cols) == 2 and len(links) >= 1:
                title = cols[0].text_content().strip()
                size = cols[1].text_content().strip()
                detail_link = links[0]
                detail_url = BASE_URL + detail_link if not detail_link.startswith("http") else detail_link
                pdf_url = links[1] if len(links) >= 2 else ""

                results.append({
                    "date": current_date,
                    "title": title,
                    "size": size,
                    "detail_url": detail_url,
                    "pdf_url": pdf_url,
                    "scraped_at": datetime.now().isoformat()
                })

    except Exception as e:
        print(f"[RBI] Error: {e}")

    return results

if __name__ == "__main__":
    results = scrape_rbi_notifications_lite()
    print(f"Total: {len(results)}")