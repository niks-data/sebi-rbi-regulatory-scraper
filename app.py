import asyncio
import threading
import pandas as pd
import streamlit as st
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'scrapers'))

from sebi_scraper import scrape_sebi_orders
from rbi_scraper import scrape_rbi_notifications

def run_in_thread(func, config):
    container = []
    errors = []
    def thread_target():
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            data = loop.run_until_complete(func(config))
            container.extend(data)
        except Exception as e:
            import traceback
            errors.append(traceback.format_exc())
        finally:
            loop.close()
    t = threading.Thread(target=thread_target)
    t.start()
    t.join()
    if errors:
        st.error(errors[0])
    return container

st.set_page_config(page_title="SEBI / RBI Regulatory Scraper", layout="wide")
st.title("🏛️ SEBI / RBI Regulatory Scraper")
st.caption("Scrapes enforcement orders and notifications from SEBI and RBI official portals.")

tab1, tab2 = st.tabs(["SEBI Orders", "RBI Notifications"])

with tab1:
    st.subheader("SEBI Enforcement Orders")
    max_pages_sebi = st.slider("Max pages to scrape", 1, 20, 1, key="sebi_pages")
    delay_sebi = st.slider("Delay between requests (sec)", 1, 5, 2, key="sebi_delay")

    if st.button("Run SEBI Scraper"):
        config = {
            "row_xpath": "//table//tr[td]",
            "date_col": 0,
            "title_col": 1,
            "detail_link_xpath": ".//a/@href",
            "pdf_iframe_xpath": "//iframe/@src",
            "max_pages": max_pages_sebi,
            "request_delay": delay_sebi,
        }
        with st.spinner("Scraping SEBI orders..."):
            results = run_in_thread(scrape_sebi_orders, config)
        if results:
            df = pd.DataFrame(results)
            st.success(f"✅ {len(results)} records scraped")
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV", csv, "sebi_orders.csv", "text/csv")
        else:
            st.error("No results found.")

with tab2:
    st.subheader("RBI Notifications")
    max_pages_rbi = st.slider("Max pages to scrape", 1, 10, 1, key="rbi_pages")
    delay_rbi = st.slider("Delay between requests (sec)", 1, 5, 2, key="rbi_delay")

    if st.button("Run RBI Scraper"):
        config = {
            "row_xpath": "//table//tr[td]",
            "max_pages": max_pages_rbi,
            "request_delay": delay_rbi,
        }
        with st.spinner("Scraping RBI notifications..."):
            results = run_in_thread(scrape_rbi_notifications, config)
        if results:
            df = pd.DataFrame(results)
            st.success(f"✅ {len(results)} records scraped")
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV", csv, "rbi_notifications.csv", "text/csv")
        else:
            st.error("No results found.")