import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO
import urllib.parse

st.set_page_config(page_title="E-Vandi Detail Fetcher", page_icon="🚗", layout="wide")

# Styling
st.markdown("""
    <style>
    .main { background-color: #f5ffff; }
    .stButton>button { background-color: #08979c; color: white; border-radius: 20px; width: 100%; font-weight: bold; }
    .stTable { background-color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Helper function for Excel
def to_excel(df_rto, df_engine):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_rto.to_excel(writer, index=False, sheet_name='RTO_Details')
        if not df_engine.empty:
            df_engine.to_excel(writer, index=False, sheet_name='Engine_Specs')
    return output.getvalue()

# --- NEW: Scraper for Engine Specs (No API) ---
def scrape_engine_specs(model_name):
    """Searches CarTrade for the model and extracts specs."""
    try:
        # Search query for the specific model
        search_url = f"https://www.cartrade.com/search?q={urllib.parse.quote(model_name + ' specs')}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        search_res = requests.get(search_url, headers=headers)
        search_soup = BeautifulSoup(search_res.content, 'html.parser')
        
        # Try to find the first result link
        link_tag = search_soup.find('a', href=True, class_=lambda x: x and 'title' in x.lower())
        if not link_tag:
            return None
        
        target_url = "https://www.cartrade.com" + link_tag['href']
        spec_res = requests.get(target_url, headers=headers)
        spec_soup = BeautifulSoup(spec_res.content, 'html.parser')
        
        specs = {}
        # CarTrade usually uses tables with class 'specs-table' or 'table'
        tables = spec_soup.find_all('table')
        for table in tables:
            for row in table.find_all('tr'):
                cols = row.find_all(['td', 'th'])
                if len(cols) == 2:
                    key = cols[0].text.strip()
                    val = cols[1].text.strip()
                    specs[key] = val
        
        return specs
    except Exception as e:
        return None

st.title("🚗 Vehicle & Engine Detail Fetcher")
v_number = st.text_input("Vehicle Number", placeholder="e.g. TN18BK0911").upper().replace(" ", "")

if st.button("Fetch Details"):
    if v_number:
        target_url = f"https://www.carinfo.app/rto-vehicle-registration-detail/rto-details/{v_number}"
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            with st.spinner('Accessing records...'):
                response = requests.get(target_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    all_details = {}
                    found_model = ""

                    # 1. Fetch RTO Data
                    summary_containers = soup.find_all(class_=lambda x: x and 'input_vehical_layout' in x)
                    for container in summary_containers:
                        label = container.find(class_=lambda x: x and 'label' in x)
                        value = container.find(class_=lambda x: x and ('vehicalModel' in x or 'ownerName' in x))
                        if label and value:
                            all_details[label.text.strip()] = value.text.strip()
                            if "Model" in label.text: found_model = value.text.strip()

                    # 2. Scrape Engine Data using the found model name
                    engine_details = {}
                    if found_model:
                        with st.spinner(f'Searching specs for {found_model}...'):
                            engine_details = scrape_engine_specs(found_model)

                    # Display Results
                    if all_details:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("📋 RTO Details")
                            df_rto = pd.DataFrame(list(all_details.items()), columns=["Field", "Info"])
                            st.table(df_rto)
                        
                        df_engine = pd.DataFrame()
                        with col2:
                            st.subheader("⚙️ Engine Specs")
                            if engine_details:
                                df_engine = pd.DataFrame(list(engine_details.items()), columns=["Spec", "Value"])
                                st.table(df_engine.head(15)) # Show top 15 specs
                            else:
                                st.warning("Technical specs table not found on target page.")

                        # Excel Export
                        excel_data = to_excel(df_rto, df_engine)
                        st.sidebar.download_button(
                            label="Download Combined Excel",
                            data=excel_data,
                            file_name=f"Vehicle_Report_{v_number}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.error(f"Error {response.status_code}")
        except Exception as e:
            st.error(f"Error: {e}")
