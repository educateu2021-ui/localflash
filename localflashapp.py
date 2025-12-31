import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import time
import random

st.set_page_config(page_title="CarWale Ultimate Scraper", layout="wide")
st.title("🚗 CarWale Pro Scraper & Reporter")

# --- CENTRAL SCRAPING ENGINE ---
def scrape_car_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=25)
        if response.status_code != 200:
            return None, None, None, f"Status {response.status_code}: Blocked."
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Exterior Image / .png detection
        exterior_img = "N/A"
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src') or img.get('data-src') or img.get('srcset', '').split(' ')[0]
            if src and ('.png' in src.lower() or 'exterior' in src.lower()):
                exterior_img = src
                break

        # 2. Variant Table Extraction
        v_rows = soup.find_all('tr', class_=lambda x: x and ('version-table' in x or 'o-cp' in x or 'o-kY' in x))
        variant_list = []
        for row in v_rows:
            name_box = row.find('div', attrs={"line": "2"}) or row.find('a', class_='o-js')
            if not name_box: continue
            
            variant_name = name_box.get('title', name_box.get_text()).strip()
            specs_tag = row.find('span', class_='o-jL') or row.find('span', class_='o-j3')
            specs = specs_tag.get('title', specs_tag.get_text()) if specs_tag else "N/A"
            price_tag = row.find('div', class_='o-eQ') or row.find('span', string=lambda t: t and ("Lakh" in t or "Cr" in t))
            price = price_tag.get_text(separator=" ").strip().split("View")[0] if price_tag else "N/A"
            
            variant_list.append({
                "Variant Name": variant_name, "Specifications": specs, "Price": price, "Image URL": exterior_img
            })

        # 3. Mileage Section Extraction
        mileage_list = []
        m_section = soup.find('section', attrs={"data-section-id": "mileage-section"})
        if m_section:
            m_table = m_section.find('table')
            if m_table:
                for m_row in m_table.find_all('tr')[1:]: # Skip header
                    cells = m_row.find_all('td')
                    if len(cells) >= 2:
                        mileage_list.append({
                            "Powertrain": cells[0].get_text(separator=" ", strip=True),
                            "ARAI Mileage": cells[1].get_text(strip=True),
                            "User Mileage": cells[2].get_text(strip=True) if len(cells) > 2 else "-"
                        })

        return variant_list, mileage_list, exterior_img, None
    except Exception as e:
        return None, None, None, str(e)

# --- UI TABS ---
tab1, tab2 = st.tabs(["🔗 Single Search", "📂 Bulk Build Run"])

with tab1:
    u_input = st.text_input("Paste CarWale Model URL:")
    if st.button("Generate Single Report"):
        v, m, img, err = scrape_car_data(u_input)
        if v:
            st.image(img, width=400) if img != "N/A" else st.info("No PNG image detected.")
            v_df = pd.DataFrame(v)
            m_df = pd.DataFrame(m)
            st.table(v_df)
            
            # Export for Single Search
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                v_df.to_excel(writer, sheet_name='Variants', index=False)
                m_df.to_excel(writer, sheet_name='Mileage', index=False)
            st.download_button("📥 Export Single Report", buf.getvalue(), "single_car_report.xlsx")
        else: st.error(err)

with tab2:
    f_input = st.file_uploader("Upload Excel Template", type=["xlsx"])
    if f_input:
        df_in = pd.read_excel(f_input)
        c_name = st.selectbox("URL Column:", df_in.columns)
        if st.button("🚀 Start Bulk Build Run (20+ Links)"):
            all_v, all_m = [], []
            p = st.progress(0)
            links = df_in[c_name].dropna().tolist()
            for i, link in enumerate(links):
                st.write(f"Scraping: {link}")
                v_r, m_r, _, _ = scrape_car_data(link)
                if v_r: all_v.extend(v_r)
                if m_r: all_m.extend(m_r)
                time.sleep(random.uniform(2.5, 4.0)) # Critical delay
                p.progress((i + 1) / len(links))
            
            if all_v:
                v_final, m_final = pd.DataFrame(all_v), pd.DataFrame(all_m)
                buf_bulk = io.BytesIO()
                with pd.ExcelWriter(buf_bulk, engine='xlsxwriter') as writer:
                    v_final.to_excel(writer, sheet_name='Variants', index=False)
                    m_final.to_excel(writer, sheet_name='Mileage', index=False)
                st.download_button("📥 Download Final Bulk Report", buf_bulk.getvalue(), "bulk_car_data.xlsx")
