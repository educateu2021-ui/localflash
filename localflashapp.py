import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import time
import random
import os

st.set_page_config(page_title="CarWale Pro Scraper", layout="wide")
st.title("🚗 CarWale Pro: Variants, Mileage & Local Image Saver")

# --- CONFIGURATION ---
# Define your local save path
SAVE_PATH = r"C:\Users\kanna\Pictures\App"

# --- SCRAPING ENGINE ---
def scrape_car_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers, timeout=25)
        if response.status_code != 200:
            return None, None, None, f"Blocked (Status {response.status_code})"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Exterior Image extraction (.png/exterior)
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
            v_name = name_box.get('title', name_box.get_text()).strip()
            specs_tag = row.find('span', class_='o-jL') or row.find('span', class_='o-j3')
            v_specs = specs_tag.get('title', specs_tag.get_text()) if specs_tag else "N/A"
            price_tag = row.find('div', class_='o-eQ') or row.find('span', string=lambda t: t and ("Lakh" in t or "Cr" in t))
            v_price = price_tag.get_text(separator=" ").strip().split("View")[0] if price_tag else "N/A"
            variant_list.append({"Variant Name": v_name, "Specifications": v_specs, "Price": v_price, "Image URL": exterior_img})

        # 3. Mileage Table
        mileage_list = []
        m_section = soup.find('section', attrs={"data-section-id": "mileage-section"})
        if m_section and m_section.find('table'):
            for m_row in m_section.find('table').find_all('tr')[1:]:
                cells = m_row.find_all('td')
                if len(cells) >= 2:
                    mileage_list.append({
                        "Model": url.split('/')[-2].replace('-', ' ').title(),
                        "Powertrain": cells[0].get_text(separator=" ", strip=True),
                        "ARAI Mileage": cells[1].get_text(strip=True),
                        "User Mileage": cells[2].get_text(strip=True) if len(cells) > 2 else "-"
                    })
        return variant_list, mileage_list, exterior_img, None
    except Exception as e:
        return None, None, None, str(e)

def save_image_locally(img_url, car_name):
    if img_url == "N/A" or not img_url.startswith("http"):
        return False
    try:
        # Create directory if it doesn't exist
        if not os.path.exists(SAVE_PATH):
            os.makedirs(SAVE_PATH)
        
        img_data = requests.get(img_url).content
        filename = f"{car_name.replace(' ', '_')}.png"
        file_path = os.path.join(SAVE_PATH, filename)
        
        with open(file_path, 'wb') as handler:
            handler.write(img_data)
        return True
    except:
        return False

# --- UI TABS ---
tab1, tab2 = st.tabs(["🔗 Single Search", "📂 Bulk Build Run"])

with tab1:
    u_input = st.text_input("Paste CarWale Model URL:")
    if st.button("Generate Single Report"):
        v, m, img, err = scrape_car_data(u_input)
        if v:
            if img != "N/A":
                st.image(img, width=400)
                # Auto-save locally if running on personal machine
                car_model_name = u_input.split('/')[-2]
                if save_image_locally(img, car_model_name):
                    st.success(f"Image saved to: {SAVE_PATH}")
            
            v_df, m_df = pd.DataFrame(v), pd.DataFrame(m)
            st.subheader("Variants")
            st.table(v_df[["Variant Name", "Specifications", "Price"]])
            
            # Export
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                v_df.to_excel(writer, sheet_name='Variants', index=False)
                m_df.to_excel(writer, sheet_name='Mileage', index=False)
            st.download_button("📥 Download Single Excel", buf.getvalue(), "single_report.xlsx")
        else: st.error(err)

with tab2:
    f_input = st.file_uploader("Upload Excel Template", type=["xlsx"])
    if f_input:
        df_in = pd.read_excel(f_input)
        c_name = st.selectbox("URL Column:", df_in.columns)
        if st.button("🚀 Start Bulk Build Run"):
            all_v, all_m = [], []
            p_bar = st.progress(0)
            links = df_in[c_name].dropna().tolist()
            for i, link in enumerate(links):
                st.write(f"Scraping {i+1}/{len(links)}: {link}")
                v_r, m_r, img_url, _ = scrape_car_data(link)
                if v_r: 
                    all_v.extend(v_r)
                    # Save Image for each link in bulk
                    car_name = link.split('/')[-2]
                    save_image_locally(img_url, car_name)
                if m_r: all_m.extend(m_r)
                
                time.sleep(random.uniform(3.0, 5.0))
                p_bar.progress((i + 1) / len(links))
            
            if all_v:
                v_res, m_res = pd.DataFrame(all_v), pd.DataFrame(all_m)
                buf_bulk = io.BytesIO()
                with pd.ExcelWriter(buf_bulk, engine='xlsxwriter') as writer:
                    v_res.to_excel(writer, sheet_name='Variants', index=False)
                    m_res.to_excel(writer, sheet_name='Mileage', index=False)
                st.success(f"Bulk run complete. Images saved to {SAVE_PATH}")
                st.download_button("📥 Download Final Bulk Report", buf_bulk.getvalue(), "bulk_report.xlsx")
