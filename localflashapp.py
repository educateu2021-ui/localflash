import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import time

st.set_page_config(page_title="Robust Car & Mileage Scraper", layout="wide")
st.title("🚗 Robust CarWale Variant, Image & Mileage Scraper")

def scrape_car_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            return None, None, None, f"Blocked (Error {response.status_code})"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- 1. ROBUST IMAGE EXTRACTION ---
        image_url = "No Image Found"
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src', '') or img.get('data-src', '')
            if 'exterior' in src.lower() or 'cw/ec' in src.lower():
                image_url = src
                break

        # --- 2. ROBUST VARIANT TABLE EXTRACTION ---
        variant_data = []
        tables = soup.find_all('table')
        for table in tables:
            if "Variants" in table.text or "On-Road Price" in table.text:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2: continue
                    col1 = cells[0]
                    variant_name = col1.find('a').text.strip() if col1.find('a') else col1.get_text(separator=" ", strip=True).split("\n")[0]
                    specs_tag = col1.find('span', title=True)
                    specs = specs_tag['title'] if specs_tag else "N/A"
                    col2 = cells[1]
                    price = col2.get_text(separator=" ", strip=True).split("View")[0]
                    
                    if any(x in price for x in ["Lakh", "Cr", "Rs."]):
                        variant_data.append({
                            "Brand/Model": url.split('/')[-2].replace('-', ' ').title(),
                            "Variant Name": variant_name,
                            "Specifications": specs,
                            "On-Road Price": price,
                            "Image Link": image_url
                        })
                break 

        # --- 3. MILEAGE SECTION EXTRACTION ---
        mileage_summary = "Mileage info not found."
        mileage_table_data = []
        
        # Find the specific mileage section container
        mileage_section = soup.find('section', attrs={"data-section-id": "mileage-section"})
        if mileage_section:
            # Extract the summary paragraph (Subtitle)
            subtitle = mileage_section.find('p', attrs={"data-skin": "subtitle"})
            if subtitle:
                mileage_summary = subtitle.get_text(strip=True)
            
            # Extract the detailed table inside this section
            m_table = mileage_section.find('table')
            if m_table:
                m_rows = m_table.find_all('tr')
                for row in m_rows:
                    m_cells = row.find_all('td')
                    if len(m_cells) >= 2:
                        powertrain = m_cells[0].get_text(separator=" ", strip=True)
                        arai_val = m_cells[1].get_text(strip=True)
                        user_val = m_cells[2].get_text(strip=True) if len(m_cells) > 2 else "-"
                        mileage_table_data.append({
                            "Powertrain": powertrain,
                            "ARAI Mileage": arai_val,
                            "User Reported Mileage": user_val
                        })

        return variant_data, mileage_summary, mileage_table_data, None

    except Exception as e:
        return None, None, None, f"Error: {str(e)}"

# --- UI ---
tab1, tab2 = st.tabs(["🔗 Single URL", "📂 Bulk Excel Upload"])

with tab1:
    u = st.text_input("Paste CarWale Link:")
    if st.button("Scrape Data"):
        v_data, m_sum, m_table, e = scrape_car_data(u)
        if e:
            st.error(e)
        else:
            # Layout with columns for Image and Pricing
            col_img, col_info = st.columns([1, 2])
            with col_img:
                if v_data and v_data[0]["Image Link"] != "No Image Found":
                    st.image(v_data[0]["Image Link"], use_column_width=True)
            with col_info:
                if v_data:
                    st.subheader("Variant Pricing & Specs")
                    st.dataframe(pd.DataFrame(v_data), use_container_width=True)

            # Mileage Section
            st.divider()
            st.subheader("⛽ Mileage Insights")
            st.info(m_sum)
            if m_table:
                st.write("Detailed Mileage Breakdown:")
                st.table(pd.DataFrame(m_table))

with tab2:
    f = st.file_uploader("Upload Excel", type=["xlsx"])
    if f:
        df_in = pd.read_excel(f)
        c = st.selectbox("Link Column:", df_in.columns)
        if st.button("🚀 Bulk Run"):
            all_res = []
            p = st.progress(0)
            urls = df_in[c].dropna().tolist()
            for i, link in enumerate(urls):
                v_res, _, _, _ = scrape_car_data(link)
                if v_res: all_res.extend(v_res)
                time.sleep(2.5) 
                p.progress((i+1)/len(urls))
            
            if all_res:
                final = pd.DataFrame(all_res)
                st.dataframe(final)
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                    final.to_excel(writer, index=False)
                st.download_button("Download Pricing Data", buf.getvalue(), "car_data.xlsx")
