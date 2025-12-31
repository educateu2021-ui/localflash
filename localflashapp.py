import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import time

st.set_page_config(page_title="Ultimate Car Scraper", layout="wide")
st.title("🚗 Robust Variant & Spec Scraper")

def scrape_car_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            return None, f"Blocked (Status {response.status_code})"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the main car image link
        img_tag = soup.find('img', class_=lambda x: x and 'o-iD' in x)
        car_image = img_tag.get('src') if img_tag else "N/A"

        # Locate all potential table rows
        rows = soup.find_all('tr', class_=lambda x: x and ('version-table' in x or 'o-cp' in x or 'o-kY' in x))
        
        if not rows:
            return None, "No variants found. (Check if car is 'Upcoming')"

        page_data = []
        for row in rows:
            # 1. EXTRACT VARIANT NAME
            # Looks for 'line=2' attribute or standard link tags
            name_container = row.find('div', attrs={"line": "2"}) or row.find('a', class_='o-js')
            if not name_container: continue
            
            full_title = name_container.get('title', '').strip()
            text_name = name_container.get_text().strip()
            variant_name = full_title if len(full_title) > len(text_name) else text_name

            # 2. EXTRACT SPECIFICATIONS
            # CarWale often hides engine/mileage specs in a span title or as secondary text
            specs_tag = row.find('span', class_='o-jL') or row.find('span', class_='o-j3')
            specs = specs_tag.get('title') if (specs_tag and specs_tag.has_attr('title')) else "N/A"
            
            # Fallback: If specs are N/A, check if they are part of the full_title (comma separated)
            if specs == "N/A" and "," in full_title:
                specs = full_title.split(",", 1)[-1].strip()
            elif specs == "N/A" and specs_tag:
                specs = specs_tag.get_text().strip()

            # 3. EXTRACT ON-ROAD PRICE
            price_tag = row.find('div', class_='o-eQ') or row.find('span', string=lambda t: t and ("Lakh" in t or "Cr" in t))
            price = price_tag.get_text(separator=" ").strip().split("View")[0] if price_tag else "N/A"

            if variant_name:
                page_data.append({
                    "Variant Name": variant_name,
                    "Specifications": specs,
                    "On-Road Price": price,
                    "Image Link": car_image,
                    "Model URL": url
                })
        
        return page_data, None
    except Exception as e:
        return None, str(e)

# --- USER INTERFACE ---
tab1, tab2 = st.tabs(["🔗 Paste Link", "📂 Upload Excel List"])

with tab1:
    url_input = st.text_input("CarWale Model URL:")
    if st.button("Extract Table"):
        data, err = scrape_car_data(url_input)
        if data:
            st.success(f"Found {len(data)} variants!")
            st.table(pd.DataFrame(data)) # Display table in output
        else: st.error(err)

with tab2:
    excel_file = st.file_uploader("Upload Excel Template", type=["xlsx"])
    if excel_file:
        input_df = pd.read_excel(excel_file)
        url_col = st.selectbox("Select URL Column:", input_df.columns)
        
        if st.button("🚀 Run Bulk Export"):
            bulk_data = []
            urls = input_df[url_col].dropna().tolist()
            progress = st.progress(0)
            
            for i, link in enumerate(urls):
                st.write(f"Scraping {i+1}/{len(urls)}: {link}")
                res, _ = scrape_car_data(link)
                if res: bulk_data.extend(res)
                time.sleep(2.5) # Avoid rate limits
                progress.progress((i + 1) / len(urls))
            
            if bulk_data:
                final_df = pd.DataFrame(bulk_data)
                st.dataframe(final_df)
                
                # Excel Export logic
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    final_df.to_excel(writer, index=False)
                st.download_button("📥 Download Full Export", buffer.getvalue(), "car_specifications.xlsx")
