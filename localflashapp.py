import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import time

st.set_page_config(page_title="Ultimate Car Scraper", layout="wide")
st.title("🚗 Multi-Format Car Variant Scraper")

def scrape_car_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            return None, f"Blocked (Error {response.status_code})"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Robust Row detection: looks for standard CarWale row patterns
        rows = soup.find_all('tr', class_=lambda x: x and ('version-table' in x or 'o-cp' in x or 'o-kY' in x))
        
        if not rows:
            return None, "Table structure not detected for this car."

        page_data = []
        for row in rows:
            # --- 1. VARIANT NAME & SPECS ---
            # Targeting the 'line="2"' pattern from your latest snippet
            variant_container = row.find('div', attrs={"line": "2"}) or row.find('a', class_='o-js')
            
            if not variant_container:
                continue

            # Full title usually contains the most detail
            full_title = variant_container.get('title', '').strip()
            variant_name = variant_container.get_text().strip()
            
            # Use the longer string as the variant name for better detail
            final_name = full_title if len(full_title) > len(variant_name) else variant_name

            # Extract Specs
            specs_tag = row.find('span', class_='o-jL')
            specs = specs_tag.get('title') if specs_tag else "N/A"
            
            # If specs are missing but comma-separated in the name (common in Thar/Magnite)
            if specs == "N/A" and "," in final_name:
                specs = final_name.split(",", 1)[1].strip()

            # --- 2. ON-ROAD PRICE ---
            # Targeting the specific nested span/div for price
            price_tag = row.find('div', class_='o-eQ') or row.find('span', string=lambda t: t and "Lakh" in t)
            price = price_tag.get_text().strip() if price_tag else "N/A"
            
            # Clean up price (remove 'View Price' text)
            price = price.split("View")[0].strip()

            if final_name:
                page_data.append({
                    "Variant Name": final_name,
                    "Specifications": specs,
                    "On-Road Price": price,
                    "URL": url
                })
        
        return page_data, None
    except Exception as e:
        return None, str(e)

# --- APP TABS ---
t1, t2 = st.tabs(["🔗 Single URL", "📂 Bulk Excel Upload"])

with t1:
    u = st.text_input("Paste CarWale Model Link:")
    if st.button("Extract Data"):
        d, e = scrape_car_data(u)
        if d:
            st.success(f"Found {len(d)} variants!")
            st.table(pd.DataFrame(d))
        else:
            st.error(e)

with t2:
    f = st.file_uploader("Upload Excel with URL list", type=["xlsx"])
    if f:
        df_in = pd.read_excel(f)
        c = st.selectbox("Select URL Column:", df_in.columns)
        if st.button("🚀 Bulk Scrape All"):
            results = []
            progress = st.progress(0)
            urls = df_in[c].dropna().tolist()
            for i, link in enumerate(urls):
                st.write(f"Scraping: {link}")
                res, _ = scrape_car_data(link)
                if res: results.extend(res)
                time.sleep(2.5) # Prevent blocking
                progress.progress((i+1)/len(urls))
            
            if results:
                final = pd.DataFrame(results)
                st.dataframe(final)
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                    final.to_excel(writer, index=False)
                st.download_button("📥 Download Combined Results", buf.getvalue(), "bulk_car_data.xlsx")
