import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO
import google.generativeai as genai
import json

st.set_page_config(page_title="E-Vandi Detail Fetcher Pro", page_icon="🚗", layout="wide")

# --- Styling ---
st.markdown("""
    <style>
    .main { background-color: #f5ffff; }
    .stButton>button { background-color: #08979c; color: white; border-radius: 20px; width: 100%; font-weight: bold; }
    .stTable { background-color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar Configuration ---
st.sidebar.title("⚙️ Settings")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
st.sidebar.info("Get a key at [Google AI Studio](https://aistudio.google.com/)")

# --- Helper Functions ---
def to_excel(df_rto, df_engine):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_rto.to_excel(writer, index=False, sheet_name='RTO_Details')
        if not df_engine.empty:
            df_engine.to_excel(writer, index=False, sheet_name='Engine_Specs')
    return output.getvalue()

def fetch_engine_specs(make_model):
    if not api_key:
        return None
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Search and provide the technical engine specifications for the vehicle: {make_model}. 
    Provide the output ONLY as a valid JSON object with the following keys:
    "Engine Type", "Displacement", "Power", "Torque", "Fuel Type", "Transmission", "Technology", "Emission", "Mileage", "Drivetrain".
    If a value is unknown, use "N/A".
    """
    
    try:
        response = model.generate_content(prompt)
        # Clean the response text to extract only JSON
        json_str = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(json_str)
    except Exception as e:
        st.error(f"AI Search Error: {e}")
        return None

# --- Main App ---
st.title("🚗 E-Vandi: Vehicle & Engine Detail Fetcher")
st.info("Retrieve RTO details and AI-powered Engine Specifications.")

v_number = st.text_input("Vehicle Number", placeholder="e.g. TN18BK0911").upper().replace(" ", "")

if st.button("Fetch Complete Details"):
    if v_number:
        target_url = f"https://www.carinfo.app/rto-vehicle-registration-detail/rto-details/{v_number}"
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            with st.spinner('🔍 Accessing RTO records and searching engine specs...'):
                response = requests.get(target_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    all_details = {}
                    make_model_val = ""

                    # 1. FETCH RTO DETAILS
                    summary_containers = soup.find_all(class_=lambda x: x and 'input_vehical_layout' in x)
                    for container in summary_containers:
                        label_tag = container.find(class_=lambda x: x and 'label' in x)
                        value_tag = container.find(class_=lambda x: x and ('vehicalModel' in x or 'ownerName' in x))
                        if label_tag and value_tag:
                            val = value_tag.text.strip()
                            all_details[label_tag.text.strip()] = val
                            if "Model" in label_tag.text: make_model_val = val

                    table_items = soup.find_all(class_=lambda x: x and 'detailItem' in x)
                    for item in table_items:
                        label_tag = item.find(class_=lambda x: x and 'itemText' in x)
                        value_tag = item.find(class_=lambda x: x and 'itemSubTitle' in x)
                        if label_tag and value_tag:
                            all_details[label_tag.text.strip()] = value_tag.text.strip()

                    if all_details:
                        st.success(f"✅ Data retrieved for {v_number}")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("📋 RTO & Owner Details")
                            df_rto = pd.DataFrame(list(all_details.items()), columns=["Field", "Information"])
                            st.table(df_rto)

                        # 2. AI ENGINE SEARCH
                        df_engine = pd.DataFrame()
                        if make_model_val:
                            specs = fetch_engine_specs(make_model_val)
                            if specs:
                                with col2:
                                    st.subheader(f"⚙️ Engine Specs: {make_model_val}")
                                    df_engine = pd.DataFrame(list(specs.items()), columns=["Specification", "Value"])
                                    st.table(df_engine)
                            else:
                                st.warning("Engine specs could not be retrieved. Check your API Key.")

                        # --- DOWNLOAD SECTION ---
                        excel_data = to_excel(df_rto, df_engine)
                        st.sidebar.markdown("---")
                        st.sidebar.subheader("📥 Export Data")
                        st.sidebar.download_button(
                            label="Download Combined Excel Report",
                            data=excel_data,
                            file_name=f"E-Vandi_{v_number}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.error("No details found for this vehicle.")
                else:
                    st.error(f"Website unreachable (Status {response.status_code})")
        except Exception as e:
            st.error(f"Process Error: {e}")
    else:
        st.warning("Please enter a vehicle number.")
