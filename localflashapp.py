import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import time
from urllib.parse import urljoin

st.set_page_config(page_title="Robust Car Scraper", layout="wide")
st.title("🚗 Robust CarWale Variant & Image Scraper")

def scrape_car_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            return None, f"Blocked (Error {response.status_code})"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- 1. ROBUST IMAGE EXTRACTION ---
        # Instead of specific classes, we look for the main image in the top section
        # CarWale images usually have 'exterior' in the URL or are inside a 'section' tag
        image_url = "No Image Found"
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src', '') or img.get('data-src', '')
            # Robust check: look for high-res images that likely represent the car
            if 'exterior' in src.lower() or 'cw/ec' in src.lower():
                image_url = src
                break

        # --- 2. ROBUST TABLE EXTRACTION ---
        # We look for ANY table that contains the word "Variants" or "On-Road Price"
        rows = []
        tables = soup.find_all('table')
        for table in tables:
            if "Variants" in table.text or "Price" in table.text:
                rows = table.find_all('tr')
                break
        
        if not rows:
            # Fallback to the class-based search if the generic table search fails
            rows = soup.find_all('tr', class_=lambda x: x and ('version-table' in x or 'o-cp' in x))

        if not rows:
            return None, "Upcoming Car or Table Not Found"

        page_data = []
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2: continue # Skip empty or header-only rows
            
            # Column 1: Variant & Specs
            col1 = cells[0]
            # Get the boldest/main text for the Name
            variant_name = col1.find('a').text.strip() if col1.find('a') else col1.get_text(separator=" ", strip=True).split("\n")[0]
            
            # Specs are often in a 'span' with a title or just smaller text
            specs_tag = col1.find('span', title=True)
            specs = specs_tag['title'] if specs_tag else "N/A"
            
            # Column 2: Price
            col2 = cells[1]
            price = col2.get_text(separator=" ", strip=True).split("View")[0] # Clean "View Price Breakup"
            
            if "Lakh" in price or "Cr" in price or "Rs." in price:
                page_data.append({
                    "Brand/Model": url.split('/')[-2].replace('-', ' ').title(),
                    "Variant Name": variant_name,
                    "Specifications": specs,
                    "On-Road Price": price,
                    "Image Link": image_url
                })
        
        return page_data, None
    except Exception as e:
        return None, f"Error: {str(e)}"

# --- UI (Link & Excel) ---
tab1, tab2 = st.tabs(["🔗 Single URL", "📂 Bulk Excel (20+ Links)"])

with tab1:
    u = st.text_input("Paste CarWale Link:")
    if st.button("Scrape"):
        d, e = scrape_car_data(u)
        if d: 
            st.dataframe(pd.DataFrame(d))
            if d[0]["Image Link"] != "No Image Found":
                st.image(d[0]["Image Link"], width=400)
        else: st.error(e)

with tab2:
    f = st.file_uploader("Upload Excel", type=["xlsx"])
    if f:
        df_in = pd.read_excel(f)
        c = st.selectbox("Link Column:", df_in.columns)
        if st.button("🚀 Bulk Run"):
            all_res = []
            p = st.progress(0)
            urls = df_in[c].dropna().tolist()
            for i, link in enumerate(urls):
                res, _ = scrape_car_data(link)
                if res: all_res.extend(res)
                time.sleep(2.5) # Anti-block delay
                p.progress((i+1)/len(urls))
            
            if all_res:
                final = pd.DataFrame(all_res)
                st.dataframe(final)
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                    final.to_excel(writer, index=False)
                st.download_button("Download Data", buf.getvalue(), "car_data.xlsx")
