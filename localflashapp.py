import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

st.set_page_config(page_title="CarWale Ultimate Scraper", layout="wide")
st.title("🚗 CarWale Pro: Variant, Mileage & Image Scraper")

# --- POWERFUL SCRAPING ENGINE ---
def get_pro_session():
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def scrape_full_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    session = get_pro_session()
    try:
        response = session.get(url, headers=headers, timeout=25)
        if response.status_code != 200:
            return None, None, None, f"Blocked (Status {response.status_code})"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. IMAGE EXTRACTION (.png/exterior)
        exterior_img = "N/A"
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src') or img.get('data-src') or img.get('srcset', '').split(' ')[0]
            alt = img.get('alt', '').lower()
            if src and ('.png' in src.lower() or 'exterior' in src.lower() or 'exterior' in alt):
                exterior_img = src
                break

        # 2. VARIANT TABLE EXTRACTION
        variant_list = []
        rows = soup.find_all('tr', class_=lambda x: x and ('version-table' in x or 'o-cp' in x or 'o-kY' in x))
        for row in rows:
            name_box = row.find('div', attrs={"line": "2"}) or row.find('a', class_='o-js')
            if not name_box: continue
            
            title_text = name_box.get('title', '').strip()
            display_text = name_box.get_text().strip()
            variant_name = title_text if len(title_text) > len(display_text) else display_text

            specs_tag = row.find('span', class_='o-jL') or row.find('span', class_='o-j3')
            specs = specs_tag.get('title') if (specs_tag and specs_tag.has_attr('title')) else "N/A"
            
            price_tag = row.find('div', class_='o-eQ') or row.find('span', string=lambda t: t and ("Lakh" in t or "Cr" in t))
            price = price_tag.get_text(separator=" ").strip().split("View")[0] if price_tag else "N/A"

            if variant_name:
                variant_list.append({
                    "Exterior Image": exterior_img,
                    "Variant Name": variant_name,
                    "Specifications": specs,
                    "On-Road Price": price,
                    "URL": url
                })

        # 3. MILEAGE EXTRACTION
        mileage_sum = "N/A"
        mileage_table = []
        mil_sec = soup.find('section', attrs={"data-section-id": "mileage-section"})
        if mil_sec:
            sub = mil_sec.find('p', attrs={"data-skin": "subtitle"})
            if sub: mileage_sum = sub.get_text(strip=True)
            
            m_tab = mil_sec.find('table')
            if m_tab:
                for m_row in m_tab.find_all('tr')[1:]: # Skip Header
                    m_cells = m_row.find_all('td')
                    if len(m_cells) >= 2:
                        mileage_table.append({
                            "Powertrain": m_cells[0].get_text(separator=" ", strip=True),
                            "ARAI Mileage": m_cells[1].get_text(strip=True),
                            "User Reported": m_cells[2].get_text(strip=True) if len(m_cells) > 2 else "-"
                        })

        return variant_list, mileage_sum, mileage_table, None
    except Exception as e:
        return None, None, None, str(e)

# --- APP UI ---
tab1, tab2 = st.tabs(["🔗 Single URL", "📂 Bulk Excel Export"])

with tab1:
    user_url = st.text_input("Paste CarWale Model URL:")
    if st.button("Generate Report"):
        v_data, m_sum, m_tab, err = scrape_full_data(user_url)
        if err: st.error(err)
        elif v_data:
            st.success(f"Extracted {len(v_data)} Variants")
            if v_data[0]["Exterior Image"] != "N/A":
                st.image(v_data[0]["Exterior Image"], width=400)
            
            res_df = pd.DataFrame(v_data)
            st.table(res_df[["Variant Name", "Specifications", "On-Road Price"]])
            
            st.subheader("⛽ Mileage Section")
            st.info(m_sum)
            if m_tab: st.table(pd.DataFrame(m_tab))

            # EXPORT BUTTON IN SINGLE TAB
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                res_df.to_excel(writer, index=False)
            st.download_button("📥 Download Single Car Data", buf.getvalue(), "single_car_data.xlsx")

with tab2:
    excel_file = st.file_uploader("Upload Excel with URL column", type=["xlsx"])
    if excel_file:
        in_df = pd.read_excel(excel_file)
        url_col = st.selectbox("Select URL Column:", in_df.columns)
        
        if st.button("🚀 Run Bulk Processing"):
            bulk_results = []
            links = in_df[url_col].dropna().tolist()
            prog = st.progress(0)
            
            for i, link in enumerate(links):
                st.write(f"Scraping {i+1}/{len(links)}: {link}")
                v_res, _, _, _ = scrape_full_data(link)
                if v_res: bulk_results.extend(v_res)
                
                # CRITICAL: Wait 3 seconds to ensure 20+ links process without block
                time.sleep(3) 
                prog.progress((i + 1) / len(links))
            
            if bulk_results:
                final_df = pd.DataFrame(bulk_results)
                st.dataframe(final_df)
                
                # EXPORT BUTTON IN BULK TAB
                buf_bulk = io.BytesIO()
                with pd.ExcelWriter(buf_bulk, engine='xlsxwriter') as writer:
                    final_df.to_excel(writer, index=False)
                st.download_button("📥 Download Combined Excel", buf_bulk.getvalue(), "bulk_report.xlsx")
