import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Set page config as the very first command
st.set_page_config(page_title="E-Vandi Vehicle Detail Fetcher", page_icon="🚗")

# Custom CSS for styling
st.markdown("""
    <style>
    .main { background-color: #f5ffff; }
    .stButton>button { 
        background-color: #08979c; 
        color: white; 
        border-radius: 20px; 
        width: 100%; 
        font-weight: bold;
    }
    .stTable { background-color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚗 Vehicle Detail Fetcher")
st.info("Enter the vehicle number to retrieve full RTO and model details.")

# User Input - normalization to uppercase and no spaces
v_number = st.text_input("Vehicle Number", placeholder="e.g. TN18BK0911").upper().replace(" ", "")

if st.button("Fetch Details"):
    if v_number:
        target_url = f"https://www.carinfo.app/rto-vehicle-registration-detail/rto-details/{v_number}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

        try:
            with st.spinner('Accessing secure RTO records...'):
                response = requests.get(target_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Store all found details in a dictionary
                    details = {}
                    
                    # Logic to find detail items: CarInfo uses specific classes like 'detailItem' 
                    # for labels (itemText) and values (itemSubTitle)
                    items = soup.find_all(class_=lambda x: x and 'detailItem' in x)
                    
                    for item in items:
                        label_tag = item.find(class_=lambda x: x and 'itemText' in x)
                        value_tag = item.find(class_=lambda x: x and 'itemSubTitle' in x)
                        
                        if label_tag and value_tag:
                            label = label_tag.text.strip()
                            value = value_tag.text.strip()
                            details[label] = value

                    if details:
                        st.success(f"Full Details for {v_number}")
                        
                        # Use a DataFrame to organize the data for a better UI experience
                        df = pd.DataFrame(list(details.items()), columns=["Field", "Information"])
                        
                        # Highlighting specific fields the user requested
                        important_fields = ["Make & Model", "Registration Date", "Fuel Type", "Vehicle Class"]
                        
                        # Displaying results
                        st.table(df)
                        
                        # Quick summary view for Make/Year if they exist in the results
                        make_model = details.get("Make & Model", "N/A")
                        reg_year = details.get("Registration Date", "N/A")
                        
                        st.markdown(f"**Quick View:**")
                        st.write(f"🔹 **Make/Model:** {make_model}")
                        st.write(f"🔹 **Reg. Date/Year:** {reg_year}")
                        
                        st.markdown(f"---")
                        st.markdown(f"[View Original Source]({target_url})")
                    else:
                        st.error("Vehicle records not found or data structure has changed. Please check the number.")
                else:
                    st.error(f"Unable to connect to service. Error Code: {response.status_code}")
                    
        except Exception as e:
            st.error(f"A technical error occurred: {e}")
    else:
        st.warning("Please enter a valid vehicle registration number.")

st.sidebar.markdown("### User Guide")
st.sidebar.write("1. Input your Plate Number (e.g., TN01AB1234).")
st.sidebar.write("2. Press 'Fetch Details'.")
st.sidebar.write("3. The app parses public RTO data to show Owner, Model, and Registration year.")
