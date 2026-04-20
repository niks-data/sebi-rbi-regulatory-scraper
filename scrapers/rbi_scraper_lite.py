import pandas as pd
import streamlit as st
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'scrapers'))

from sebi_scraper_lite import scrape_sebi_orders_lite
from rbi_scraper_lite import scrape_rbi_notifications_lite

st.set_page_config(page_title="SEBI / RBI Regulatory Scraper", layout="wide")
st.title("🏛️ SEBI / RBI Regulatory Scraper")
st.caption("Scrapes enforcement orders and notifications from SEBI and RBI official portals.")

tab1, tab2 = st.tabs(["SEBI Orders", "RBI Notifications"])

with tab1:
    st.subheader("SEBI Enforcement Orders")
    max_pages_sebi = st.slider("Max pages to scrape", 1, 20, 3, key="sebi_pages")

    if st.button("Run SEBI Scraper"):
        with st.spinner("Scraping SEBI orders..."):
            results = scrape_sebi_orders_lite(max_pages_sebi)
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

    if st.button("Run RBI Scraper"):
        with st.spinner("Scraping RBI notifications..."):
            results = scrape_rbi_notifications_lite()
        if results:
            df = pd.DataFrame(results)
            st.success(f"✅ {len(results)} records scraped")
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV", csv, "rbi_notifications.csv", "text/csv")
        else:
            st.error("No results found.")