import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import time

st.set_page_config(page_title="Bulk CarWale Scraper", layout="wide")
st.title("📂 Bulk CarWale Variant Scraper")

# Step 1: Upload Excel File
uploaded_file = st.file_uploader("Upload Excel file with links", type=["xlsx", "csv"])

def scrape_car_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('tr', class_=lambda x: x and 'version-table__tbody-tr' in x)
        
        data = []
        for row in rows:
            name_tag = row.find('a', class_='o-js')
            variant_name = name_tag.text.strip() if name_tag else "N/A"
            
            specs_tag = row.find('span', class_='o-jL')
            specs = specs_tag.get('title') if specs_tag else "N/A"
            
            price_tag = row.find('div', class_='o-eQ') or row.find('span', string=lambda t: t and "Lakh" in t)
            price = price_tag.text.strip() if price_tag else "N/A"
            
            data.append({
                "Source URL": url,
                "Variant Name": variant_name,
                "Specifications": specs,
                "On-Road Price": price
            })
        return data
    except:
        return None

if uploaded_file:
    # Read the file
    if uploaded_file.name.endswith('.csv'):
        input_df = pd.read_csv(uploaded_file)
    else:
        input_df = pd.read_excel(uploaded_file)
    
    st.write("Preview of uploaded file:")
    st.dataframe(input_df.head())
    
    # Step 2: Select the column with links
    column_with_links = st.selectbox("Select the column that contains the links:", input_df.columns)
    
    if st.button("🚀 Start Bulk Scraping"):
        links = input_df[column_with_links].dropna().tolist()
        all_results = []
        progress_bar = st.progress(0)
        
        for i, link in enumerate(links):
            st.write(f"Scraping: {link}")
            result = scrape_car_data(link)
            if result:
                all_results.extend(result)
            
            # Progress update
            progress_bar.progress((i + 1) / len(links))
            # Small delay to avoid being blocked
            time.sleep(1) 
        
        if all_results:
            final_df = pd.DataFrame(all_results)
            st.success(f"Done! Extracted {len(final_df)} variants from {len(links)} links.")
            st.dataframe(final_df)
            
            # Step 3: Download Combined Results
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, index=False, sheet_name='All_Variants')
            st.download_button("📥 Download Combined Excel", output.getvalue(), "bulk_car_variants.xlsx")
        else:
            st.error("No data could be extracted. Check your links.")
