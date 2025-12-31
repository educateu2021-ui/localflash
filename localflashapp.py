import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

st.set_page_config(page_title="CarWale Scraper", page_icon="🚗")

st.title("🚗 CarWale Variant Scraper")

# The URL you provided
url = st.text_input("CarWale URL:", "https://www.carwale.com/maruti-suzuki-cars/e-vitara/")

def scrape_data(target_url):
    # Enhanced headers to mimic a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/"
    }
    
    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None, f"Status Code: {response.status_code}. (Site blocked the request)"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Note: e-Vitara is 'Upcoming' - it might not have the full table yet
        # This looks for the most common variant table structure on CarWale
        rows = soup.find_all('tr', class_=lambda x: x and 'version-table__tbody-tr' in x)
        
        if not rows:
            return None, "No variant table found. Note: For upcoming cars, the price table is often not yet published."

        data = []
        for row in rows:
            name = row.find('a').text.strip() if row.find('a') else "N/A"
            price = row.find('span', class_=lambda x: x and 'o-c' in x).text.strip() if row.find('span') else "N/A"
            data.append({"Variant": name, "Price": price})
            
        return pd.DataFrame(data), None
    except Exception as e:
        return None, str(e)

if st.button("Scrape Now"):
    with st.spinner("Fetching..."):
        df, error = scrape_data(url)
        if error:
            st.error(error)
        else:
            st.dataframe(df)
            # Export to Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("Download Excel", output.getvalue(), "variants.xlsx")
