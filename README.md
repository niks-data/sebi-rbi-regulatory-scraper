# SEBI / RBI Regulatory Scraper

Automated pipeline that scrapes SEBI enforcement orders and RBI circulars from official government portals and outputs clean, structured data — ready for analysis, alerting, or downstream pipelines.

## What it does
- Scrapes SEBI enforcement orders (dates, entities, violations, penalties)
- Scrapes RBI circulars (circular number, date, subject, PDF link)
- Handles JS-rendered pages via Playwright
- Extracts and parses data using lxml + XPath
- Outputs to JSON, CSV, or Google Sheets

## Tech stack
- `Python 3.11` `Playwright` `lxml` `XPath` `Pandas`

## Project structure
sebi-rbi-regulatory-scraper/
├── scrapers/
│   ├── sebi_scraper.py       # SEBI enforcement orders
│   └── rbi_scraper.py        # RBI circulars
├── output/
│   ├── sebi_orders.csv
│   └── rbi_circulars.csv
├── app.py                    # Streamlit demo
├── requirements.txt
└── README.md

## Sample output

| Date | Entity | Violation | Penalty (₹) |
|------|--------|-----------|-------------|
| 2024-01-15 | XYZ Securities Ltd | Insider trading | 25,00,000 |
| 2024-02-03 | ABC Brokers | Disclosure violation | 5,00,000 |

## Live demo
🔗 [Live Demo](https://sebi-rbi-scraper.streamlit.app)

## Use cases
- Compliance monitoring for law firms and financial analysts
- Regulatory alert systems
- Financial research pipelines
