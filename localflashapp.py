import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

st.set_page_config(page_title="CarWale Variant Scraper", layout="wide")
st.title("🚗 CarWale Variant Scraper")

# Default to a live model so you can see it working immediately
url = st.text_input("Enter CarWale Model URL:", "https://www.carwale.com/nissan-cars/magnite/")

def scrape_car_data(target_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        response = requests.get(target_url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None, f"Error: Site returned status {response.status_code}"

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Finding variant rows using standard CarWale classes
        rows = soup.find_all('tr', class_=lambda x: x and 'version-table__tbody-tr' in x)
        
        if not rows:
            return None, "No variant table found. (Note: Upcoming cars like e-Vitara don't have tables yet.)"

        data = []
        for row in rows:
            # 1. Variant Name
            name_tag = row.find('a', class_='o-js')
            variant_name = name_tag.text.strip() if name_tag else "N/A"
            
            # 2. Specifications (Extracted from the 'title' attribute of the info span)
            specs_tag = row.find('span', class_='o-jL')
            specs = specs_tag.get('title') if specs_tag else "N/A"
            
            # 3. On-Road Price
            price_tag = row.find('div', class_='o-eQ') or row.find('span', string=lambda t: t and "Lakh" in t)
            price = price_tag.text.strip() if price_tag else "N/A"
            
            data.append({
                "Variant Name": variant_name,
                "Specifications": specs,
                "On-Road Price": price
            })
            
        return pd.DataFrame(data), None

    except Exception as e:
        return None, f"System Error: {str(e)}"

if st.button("Extract Data"):
    with st.spinner("Fetching variant details..."):
        df, error = scrape_car_data(url)
        
        if error:
            st.error(error)
        else:
            st.success(f"Successfully found {len(df)} variants!")
            st.dataframe(df, use_container_width=True)
            
            # Export to Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Download Excel File", output.getvalue(), "car_variants.xlsx")
