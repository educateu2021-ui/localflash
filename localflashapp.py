import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="E-Vandi Detail Fetcher", page_icon="🚗")

# Styling
st.markdown("""
    <style>
    .main { background-color: #f5ffff; }
    .stButton>button { background-color: #08979c; color: white; border-radius: 20px; width: 100%; font-weight: bold; }
    .stTable { background-color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚗 Vehicle Detail Fetcher")
st.info("Retrieve RTO, Model, and Owner details from CarInfo.")

v_number = st.text_input("Vehicle Number", placeholder="e.g. TN18BK0911").upper().replace(" ", "")

# Helper function to convert dataframe to excel for download
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Vehicle_Report')
    processed_data = output.getvalue()
    return processed_data

if st.button("Fetch Details"):
    if v_number:
        target_url = f"https://www.carinfo.app/rto-vehicle-registration-detail/rto-details/{v_number}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}

        try:
            with st.spinner('Accessing records...'):
                response = requests.get(target_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    all_details = {}

                    # 1. FETCH TOP SUMMARY (Make/Model and Owner)
                    # We ensure these go into the 'all_details' dictionary first
                    summary_containers = soup.find_all(class_=lambda x: x and 'input_vehical_layout' in x)
                    for container in summary_containers:
                        label_tag = container.find(class_=lambda x: x and 'label' in x)
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
                        
                        # Prepare DataFrame
                        df = pd.DataFrame(list(all_details.items()), columns=["Field", "Information"])
                        
                        # --- DISPLAY RESULTS ---
                        st.markdown("### Technical Specifications & Ownership")
                        st.table(df)
                        
                        # --- EXCEL DOWNLOAD SECTION ---
                        excel_data = to_excel(df)
                        st.sidebar.markdown("### 📥 Download Center")
                        st.sidebar.download_button(
                            label="Download Excel Report",
                            data=excel_data,
                            file_name=f"Vehicle_Report_{v_number}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
                        st.markdown(f"[View Original Source]({target_url})")
                    else:
                        st.error("Could not parse details. The layout might have changed.")
                else:
                    st.error(f"Could not reach CarInfo. Status Code: {response.status_code}")
                    
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter a vehicle number.")
