import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import time

st.set_page_config(page_title="CarWale Ultimate Scraper", layout="wide")
st.title("🚗 CarWale Pro Scraper & Reporter")

# --- CENTRAL SCRAPING FUNCTION ---
def scrape_robust_data(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200: return None, f"Blocked (Error {response.status_code})"
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Robust Row & Image detection
        rows = soup.find_all('tr', class_=lambda x: x and ('version-table' in x or 'o-cp' in x or 'o-kY' in x))
        
        exterior_img = "N/A"
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or ""
            if 'exterior' in src.lower() or '.png' in src.lower():
                exterior_img = src
                break

        page_data = []
        for row in rows:
            name_box = row.find('div', attrs={"line": "2"}) or row.find('a', class_='o-js')
            if not name_box: continue
            
            variant_name = name_box.get('title') or name_box.get_text().strip()
            specs = row.find('span', class_='o-jL').get('title') if row.find('span', class_='o-jL') else "N/A"
            price_tag = row.find('div', class_='o-eQ') or row.find('span', string=lambda t: t and "Lakh" in t)
            price = price_tag.get_text().strip().split("View")[0] if price_tag else "N/A"

            page_data.append({
                "Exterior Image": exterior_img,
                "Variant Name": variant_name,
                "Specifications": specs,
                "On-Road Price": price,
                "Source": url
            })
        return page_data, None
    except Exception as e: return None, str(e)

# --- UI TABS ---
tab1, tab2 = st.tabs(["🔗 Single URL Search", "📂 Bulk Excel Export"])

with tab1:
    user_url = st.text_input("Paste CarWale Model Link:")
    if st.button("Generate Single Report"):
        data, err = scrape_robust_data(user_url)
        if data:
            st.success(f"Found {len(data)} Variants!")
            df_single = pd.DataFrame(data)
            st.table(df_single[["Variant Name", "Specifications", "On-Road Price"]])
            
            # --- DOWNLOAD BUTTON FOR SINGLE SEARCH ---
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                df_single.to_excel(writer, index=False)
            st.download_button("📥 Download Single Link Data", buf.getvalue(), "single_car_report.xlsx")
        else: st.error(err)

with tab2:
    excel_file = st.file_uploader("Upload Excel with URL list", type=["xlsx"])
    if excel_file:
        input_df = pd.read_excel(excel_file)
        url_col = st.selectbox("Select URL Column:", input_df.columns)
        if st.button("🚀 Start Bulk Run"):
            results = []
            urls = input_df[url_col].dropna().tolist()
            prog = st.progress(0)
            for i, link in enumerate(urls):
                st.write(f"Scraping {i+1}/{len(urls)}")
                res, _ = scrape_robust_data(link)
                if res: results.extend(res)
                time.sleep(2.5)
                prog.progress((i+1)/len(urls))
            
            if results:
                final_df = pd.DataFrame(results)
                st.dataframe(final_df)
                buf_bulk = io.BytesIO()
                with pd.ExcelWriter(buf_bulk, engine='xlsxwriter') as writer:
                    final_df.to_excel(writer, index=False)
                st.download_button("📥 Download Bulk Report", buf_bulk.getvalue(), "bulk_car_report.xlsx")
