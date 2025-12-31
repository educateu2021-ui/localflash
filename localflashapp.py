import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

# Page Configuration
st.set_page_config(page_title="CarWale Variant Scraper", layout="wide")

st.title("🚗 CarWale Variant Table Scraper")
st.write("Enter the URL of a CarWale model page to extract all variant prices and specifications.")

# Input URL
default_url = "https://www.carwale.com/maruti-suzuki-cars/e-vitara/"
url = st.text_input("Paste CarWale URL here:", default_url)

def scrape_car_data(target_url):
    # Important: Real browsers headers to avoid 403 Forbidden error
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        response = requests.get(target_url, headers=headers)
        if response.status_code != 200:
            st.error(f"Failed to fetch page. Status code: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # CarWale uses 'tr' with specific class for variant rows
        rows = soup.find_all('tr', class_=lambda x: x and 'version-table__tbody-tr' in x)
        
        if not rows:
            # Fallback for some pages that use different structures
            rows = soup.select("table.version-table tbody tr")

        variant_list = []
        
        for row in rows:
            # Extracting Name
            name_tag = row.find('a', class_='o-js') or row.find('div', class_='o-eO')
            name = name_tag.text.strip() if name_tag else "N/A"
            
            # Extracting Specs (Mileage, Engine, Transmission)
            specs_tag = row.find('span', class_='o-jL')
            specs = specs_tag.get('title') if specs_tag else "N/A"
            
            # Extracting Price
            price_tag = row.find('div', class_='o-eQ') or row.find('span', string=lambda t: "Lakh" in t or "Cr" in t)
            price = price_tag.text.strip() if price_tag else "Price not listed"

            variant_list.append({
                "Variant Name": name,
                "Specifications": specs,
                "On-Road Price": price
            })
            
        return pd.DataFrame(variant_list)

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

if st.button("Start Scraping"):
    with st.spinner("Fetching data from CarWale..."):
        df = scrape_car_data(url)
        
        if df is not None and not df.empty:
            st.success(f"Found {len(df)} variants!")
            
            # Display Data
            st.dataframe(df, use_container_width=True)
            
            # Download Options
            col1, col2 = st.columns(2)
            
            # CSV Download
            csv = df.to_csv(index=False).encode('utf-8')
            col1.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name="car_variants.csv",
                mime="text/csv",
            )
            
            # Excel Download
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Variants')
            
            col2.download_button(
                label="📥 Download as Excel",
                data=buffer.getvalue(),
                file_name="car_variants.xlsx",
                mime="application/vnd.ms-excel",
            )
        else:
            st.warning("No variant data found. Note: For upcoming cars like e-Vitara, price tables might not be published yet.")
