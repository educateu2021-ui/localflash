import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

st.set_page_config(page_title="E-Vandi Vehicle Fetcher", page_icon="🚗")

# Custom CSS to match your branding
st.markdown("""
    <style>
    .main { background-color: #f5ffff; }
    .stButton>button { background-color: #08979c; color: white; border-radius: 20px; width: 100%; }
    </style>
    """, unsafe_import_headers=True)

st.title("🚗 Vehicle Detail Fetcher")
st.info("Enter the vehicle number to retrieve RTO details.")

# User Input
v_number = st.text_input("Vehicle Number", placeholder="e.g. TN18BK0911").upper().replace(" ", "")

if st.button("Fetch Details"):
    if v_number:
        # Based on your HTML, the site routes directly to this URL
        target_url = f"https://www.carinfo.app/rto-vehicle-registration-detail/rto-details/{v_number}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

        try:
            with st.spinner('Fetching from CarInfo...'):
                response = requests.get(target_url, headers=headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Finding the detail containers based on the CSS classes in your HTML
                    # Specifically looking for: expand_component_detailItem__V43eh
                    details = {}
                    items = soup.find_all(class_=lambda x: x and 'detailItem' in x)
                    
                    for item in items:
                        # Extract Label (e.g., Owner Name)
                        label_tag = item.find(class_=lambda x: x and 'itemText' in x)
                        # Extract Value (e.g., John Doe)
                        value_tag = item.find(class_=lambda x: x and 'itemSubTitle' in x)
                        
                        if label_tag and value_tag:
                            details[label_tag.text.strip()] = value_tag.text.strip()

                    if details:
                        st.success(f"Results for {v_number}")
                        
                        # Displaying in a clean table format
                        df = pd.DataFrame(list(details.items()), columns=["Field", "Information"])
                        st.table(df)
                        
                        st.markdown(f"[View Original Source]({target_url})")
                    else:
                        st.error("Could not find specific details. The vehicle might not be in the database or the site is blocking the request.")
                else:
                    st.error(f"Site unreachable (Status: {response.status_code})")
                    
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a vehicle number.")

st.sidebar.markdown("### Instructions")
st.sidebar.write("1. Enter Plate Number.")
st.sidebar.write("2. Click Fetch.")
st.sidebar.write("3. Details are parsed from the public RTO registry via CarInfo.")
