import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

st.set_page_config(page_title="CarWale Ultimate Scraper", layout="wide")
st.title("🚜 Pro Bulk CarWale Scraper (2025 Edition)")

# --- POWERFUL SCRAPING ENGINE ---
def get_pro_session():
    session = requests.Session()
    # Retries help handle transient connection issues or slight rate limiting
    retry = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def scrape_variant_data(session, url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    try:
        response = session.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            return None, f"Blocked/Error {response.status_code}"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # We search for rows in BOTH table formats (the previous one and your new one)
        rows = soup.find_all('tr', class_=lambda x: x and ('version-table__tbody-tr' in x or 'o-cp' in x))
        
        if not rows:
            return None, "Upcoming Car (No price table published yet)"

        page_data = []
        for row in rows:
            # --- 1. EXTRACT VARIANT NAME ---
            # Try Format A (Magnite style) then Format B (Thar style)
            name_tag = row.find('a', class_='o-js') or row.find('div', class_='o-eQ')
            variant_name = name_tag.text.strip() if name_tag else "N/A"
            
            # For the new format, the 'title' attribute often holds the full detailed name
            if name_tag and name_tag.has_attr('title') and len(name_tag['title']) > len(variant_name):
                variant_name = name_tag['title']

            # --- 2. EXTRACT SPECIFICATIONS ---
            specs_tag = row.find('span', class_='o-jL')
            specs = specs_tag.get('title') if specs_tag else "N/A"
            
            # If Specs are not in a span, check if they are part of the full name title
            if specs == "N/A" and ',' in variant_name:
                specs = variant_name.split(',', 1)[-1].strip()

            # --- 3. EXTRACT ON-ROAD PRICE ---
            price_tag = row.find('div', class_='o-eQ') or row.find('span', string=lambda t: t and ("Lakh" in t or "Cr" in t))
            # New format specific check
            if not price_tag:
                price_tag = row.find('div', class_=lambda x: x and 'o-g0' in x and 'o-jJ' in x)
            
            price = price_tag.text.strip() if price_tag else "N/A"
            
            if variant_name != "N/A":
                page_data.append({
                    "Car Model": url.split('/')[-2].replace('-', ' ').title(),
                    "Variant Name": variant_name,
                    "Specifications": specs,
                    "On-Road Price": price,
                    "URL": url
                })
        return page_data, None
    except Exception as e:
        return None, f"System Error: {str(e)}"

# --- APP TABS ---
t1, t2 = st.tabs(["🔗 Single URL Search", "📂 Bulk Excel Upload (20+ Links)"])

with t1:
    url_input = st.text_input("Paste CarWale Model Link:", placeholder="e.g., https://www.carwale.com/mahindra-cars/thar/")
    if st.button("Extract Single Car"):
        if url_input:
            s = get_pro_session()
            data, err = scrape_variant_data(s, url_input)
            if data:
                st.write(pd.DataFrame(data))
            else:
                st.error(err)

with t2:
    st.info("Upload an Excel file with a list of URLs to scrape them all at once.")
    file = st.file_uploader("Upload Excel Template", type=["xlsx"])
    if file:
        df_input = pd.read_excel(file)
        col = st.selectbox("Select column with the URLs:", df_input.columns)
        
        if st.button("🚀 Start Bulk Scraping (20+ Links)"):
            urls = df_input[col].dropna().tolist()
            all_data = []
            session = get_pro_session()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, link in enumerate(urls):
                status_text.text(f"Processing {i+1} of {len(urls)}: {link}")
                data, err = scrape_variant_data(session, link)
                
                if data:
                    all_data.extend(data)
                else:
                    st.warning(f"Skipped {link}: {err}")
                
                # Update progress
                progress_bar.progress((i + 1) / len(urls))
                
                # Wait 2.5 seconds to avoid being detected as a bot 
                time.sleep(2.5) 
            
            if all_data:
                final_df = pd.DataFrame(all_data)
                st.success(f"Successfully scraped {len(final_df)} variants from {len(urls)} links!")
                st.dataframe(final_df)
                
                # Combined Excel Export
                out = io.BytesIO()
                with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
                    final_df.to_excel(writer, index=False)
                st.download_button("📥 Download Final Master Data", out.getvalue(), "combined_car_data.xlsx")
            else:
                st.error("No data extracted. Ensure the URLs are correct.")
