import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

st.set_page_config(page_title="CarWale Pro Scraper", layout="wide")
st.title("🚗 CarWale Variant Scraper")

# Target URL
target_url = st.text_input("Enter CarWale URL:", "https://www.carwale.com/nissan-cars/magnite/")

def scrape_car_data(url):
    # These headers are "Real Browser" signatures to avoid being blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return None, f"Blocked by Website (Error {response.status_code})"

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the variant rows using the HTML structure you provided earlier
        rows = soup.find_all('tr', class_=lambda x: x and 'version-table__tbody-tr' in x)
        
        # If the class-based search fails, try a generic table search
        if not rows:
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')[1:] # Skip header row

        results = []
        for row in rows:
            # Finding Name
            name_tag = row.find('a') or row.find('div', line="2")
            name = name_tag.text.strip() if name_tag else "N/A"
            
            # Finding Price
            price_tag = row.find('span', string=lambda t: t and ("Lakh" in t or "Cr" in t))
            price = price_tag.text.strip() if price_tag else "N/A"
            
            if name != "N/A":
                results.append({"Variant": name, "Price": price})
        
        if not results:
            return None, "No data found on this page. Check if the URL is correct."
            
        return pd.DataFrame(results), None

    except Exception as e:
        return None, f"System Error: {str(e)}"

if st.button("🚀 Extract Table Now"):
    with st.spinner("Bypassing security and fetching data..."):
        df, error = scrape_car_data(target_url)
        
        if error:
            st.error(error)
            st.info("Tip: If you see 'Blocked', the website has detected the scraper. Try again in 5 minutes.")
        else:
            st.success(f"Found {len(df)} variants!")
            st.dataframe(df, use_container_width=True)
            
            # Excel Download logic
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Download as Excel", buffer.getvalue(), "car_data.xlsx")
