import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import time

st.set_page_config(page_title="CarWale Scraper Pro", layout="wide")
st.title("🚗 CarWale Variant Scraper (Link & Excel)")

def scrape_car_data(url):
    """Core scraping function to extract Variant, Specs, and Price."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # Standard CarWale table row class
        rows = soup.find_all('tr', class_=lambda x: x and 'version-table__tbody-tr' in x)
        
        data = []
        for row in rows:
            # Extract Variant Name
            name_tag = row.find('a', class_='o-js')
            variant_name = name_tag.text.strip() if name_tag else "N/A"
            
            # Extract Specs from 'title' attribute
            specs_tag = row.find('span', class_='o-jL')
            specs = specs_tag.get('title') if specs_tag else "N/A"
            
            # Extract Price
            price_tag = row.find('div', class_='o-eQ') or row.find('span', string=lambda t: t and "Lakh" in t)
            price = price_tag.text.strip() if price_tag else "N/A"
            
            data.append({
                "Source URL": url,
                "Variant Name": variant_name,
                "Specifications": specs,
                "On-Road Price": price
            })
        return data
    except Exception:
        return None

# Interface with two options
tab1, tab2 = st.tabs(["🔗 Single Link Search", "📁 Bulk Excel Upload"])

with tab1:
    st.subheader("Quick Search")
    single_url = st.text_input("Paste CarWale URL:", "https://www.carwale.com/nissan-cars/magnite/")
    if st.button("Scrape Single Link"):
        with st.spinner("Fetching..."):
            res = scrape_car_data(single_url)
            if res:
                df_single = pd.DataFrame(res)
                st.dataframe(df_single, use_container_width=True)
                # Excel Export
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_single.to_excel(writer, index=False)
                st.download_button("Download Excel", output.getvalue(), "single_car.xlsx")
            else:
                st.warning("No data found. Note: e-Vitara is upcoming and has no price table yet.")

with tab2:
    st.subheader("Bulk Search from Excel")
    uploaded_file = st.file_uploader("Upload Excel/CSV with link column", type=["xlsx", "csv"])
    
    if uploaded_file:
        input_df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        st.write("File Preview:", input_df.head(2))
        col_name = st.selectbox("Select the column with URLs:", input_df.columns)
        
        if st.button("Start Bulk Scrape"):
            links = input_df[col_name].dropna().tolist()
            bulk_results = []
            progress = st.progress(0)
            
            for i, link in enumerate(links):
                st.write(f"Processing: {link}")
                data = scrape_car_data(link)
                if data:
                    bulk_results.extend(data)
                progress.progress((i + 1) / len(links))
                time.sleep(1) # Prevent blocking
            
            if bulk_results:
                df_bulk = pd.DataFrame(bulk_results)
                st.success(f"Found {len(df_bulk)} total variants!")
                st.dataframe(df_bulk)
                # Bulk Export
                output_bulk = io.BytesIO()
                with pd.ExcelWriter(output_bulk, engine='xlsxwriter') as writer:
                    df_bulk.to_excel(writer, index=False)
                st.download_button("Download Final Master File", output_bulk.getvalue(), "bulk_cars.xlsx")
