import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

st.set_page_config(page_title="CarWale Scraper", page_icon="🚗")
st.title("🚗 CarWale Variant Scraper")

# User input for the URL
url = st.text_input("Enter CarWale URL:", "https://www.carwale.com/maruti-suzuki-cars/e-vitara/")

def scrape_car_variants(target_url):
    # Mimic a real browser to bypass basic anti-bot measures
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    
    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None, f"Failed (Status Code: {response.status_code})."

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Target the variant table rows using classes from your provided snippets
        rows = soup.find_all('tr', class_=lambda x: x and 'version-table__tbody-tr' in x)
        
        if not rows:
            # Fallback if specific classes aren't found
            rows = soup.find_all('tr')[1:] 

        car_data = []
        for row in rows:
            # Extract data from columns
            name_cell = row.find('a', class_='o-js') or row.find('td')
            price_cell = row.find('div', class_='o-eQ') or row.select_one('td:nth-of-type(2)')
            
            if name_cell and price_cell:
                car_data.append({
                    "Variant": name_cell.text.strip(),
                    "Price": price_cell.text.strip()
                })
        
        return pd.DataFrame(car_data), None

    except Exception as e:
        return None, str(e)

if st.button("Start Extraction"):
    with st.spinner("Accessing CarWale..."):
        df, err = scrape_car_variants(url)
        if err:
            st.error(f"Error: {err}")
        elif df is not None and not df.empty:
            st.success(f"Extracted {len(df)} variants!")
            st.table(df)
            
            # Export to Excel utility
            towrite = io.BytesIO()
            df.to_excel(towrite, index=False, engine='xlsxwriter')
            st.download_button(label="📥 Download Excel", data=towrite.getvalue(), file_name="variants.xlsx")
