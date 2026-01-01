import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

st.set_page_config(page_title="E-Vandi Detail Fetcher", page_icon="🚗")

# Styling
st.markdown("""
    <style>
    .main { background-color: #f5ffff; }
    .stButton>button { background-color: #08979c; color: white; border-radius: 20px; width: 100%; font-weight: bold; }
    .report-card { background-color: white; padding: 20px; border-radius: 15px; border: 1px solid #e6eeee; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚗 Vehicle Detail Fetcher")
st.info("Retrieve RTO, Model, and Owner details from CarInfo.")

v_number = st.text_input("Vehicle Number", placeholder="e.g. TN18BK0911").upper().replace(" ", "")

if st.button("Fetch Details"):
    if v_number:
        target_url = f"https://www.carinfo.app/rto-vehicle-registration-detail/rto-details/{v_number}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}

        try:
            with st.spinner('Accessing secure records...'):
                response = requests.get(target_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    all_details = {}

                    # 1. FETCH TOP SUMMARY (Make/Model and Owner)
                    # Based on your HTML, labels are 'label' and values are 'vehicalModel' or 'ownerName'
                    summary_containers = soup.find_all(class_=lambda x: x and 'input_vehical_layout' in x)
                    for container in summary_containers:
                        label_tag = container.find(class_=lambda x: x and 'label' in x)
                        # Find potential value tags for Model or Owner
                        value_tag = container.find(class_=lambda x: x and ('vehicalModel' in x or 'ownerName' in x))
                        
                        if label_tag and value_tag:
                            all_details[label_tag.text.strip()] = value_tag.text.strip()

                    # 2. FETCH RTO TABLE DETAILS
                    table_items = soup.find_all(class_=lambda x: x and 'detailItem' in x)
                    for item in table_items:
                        label_tag = item.find(class_=lambda x: x and 'itemText' in x)
                        value_tag = item.find(class_=lambda x: x and 'itemSubTitle' in x)
                        if label_tag and value_tag:
                            all_details[label_tag.text.strip()] = value_tag.text.strip()

                    if all_details:
                        st.success(f"Results for {v_number}")
                        
                        # --- DISPLAY QUICK VIEW ---
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Make & Model", all_details.get("Make & Model", "Not Found"))
                        with col2:
                            st.metric("Owner", all_details.get("Owner Name", "Protected"))
                        
                        # --- DISPLAY FULL DATA TABLE ---
                        st.markdown("### Full Technical Specifications")
                        df = pd.DataFrame(list(all_details.items()), columns=["Field", "Information"])
                        st.table(df)
                        
                        st.markdown(f"[View Original Source]({target_url})")
                    else:
                        st.error("Data found on page but parser could not extract it. The website layout may have changed slightly.")
                else:
                    st.error(f"Could not reach CarInfo. Status Code: {response.status_code}")
                    
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter a vehicle number.")
