import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import time

st.set_page_config(page_title="CarWale Ultimate Scraper", layout="wide")
st.title("🚗 CarWale Variant Scraper")

# --- SCRAPING FUNCTION ---
def scrape_car_data(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('tr', class_=lambda x: x and 'version-table__tbody-tr' in x)
        
        data = []
        for row in rows:
            name_tag = row.find('a', class_='o-js')
            specs_tag = row.find('span', class_='o-jL')
            price_tag = row.find('div', class_='o-eQ') or row.find('span', string=lambda t: t and "Lakh" in t)
            
            if name_tag:
                data.append({
                    "Source URL": url,
                    "Variant Name": name_tag.text.strip(),
                    "Specifications": specs_tag.get('title') if specs_tag else "N/A",
                    "On-Road Price": price_tag.text.strip() if price_tag else "N/A"
                })
        return data
    except: return None

# --- UI LAYOUT ---
tab1, tab2 = st.tabs(["🔗 Single Link Search", "📂 Bulk Excel Upload"])

# TAB 1: SINGLE LINK
with tab1:
    st.subheader("Quick Search")
    single_url = st.text_input("Paste a CarWale URL here:")
    if st.button("Search Link"):
        if single_url:
            res = scrape_car_data(single_url)
            if res:
                df_single = pd.DataFrame(res)
                st.table(df_single)
            else:
                st.warning("No data found or car is 'Upcoming'.")
        else:
            st.error("Please paste a link first.")

# TAB 2: BULK EXCEL
with tab2:
    st.subheader("Bulk Processing")
    uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])
    
    if uploaded_file:
        input_df = pd.read_excel(uploaded_file)
        st.write("File Preview:", input_df.head(2))
        col_name = st.selectbox("Select column with URLs:", input_df.columns)
        
        if st.button("🚀 Start Bulk Scraping"):
            links = input_df[col_name].dropna().tolist()
            bulk_results = []
            progress = st.progress(0)
            
            for i, link in enumerate(links):
                st.write(f"Processing: {link}")
                data = scrape_car_data(link)
                if data: bulk_results.extend(data)
                progress.progress((i + 1) / len(links))
                time.sleep(1) # Small delay to stay safe
            
            if bulk_results:
                final_df = pd.DataFrame(bulk_results)
                st.success("Scraping Complete!")
                st.dataframe(final_df)
                
                # Download Combined Results
                out = io.BytesIO()
                with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
                    final_df.to_excel(writer, index=False)
                st.download_button("📥 Download Master Excel", out.getvalue(), "bulk_variants.xlsx")
