import streamlit as st
import pandas as pd
import requests
import os
import zipfile
from io import BytesIO

# --- CONFIGURATION ---
LOCAL_SAVE_PATH = r"C:\Users\kanna\Pictures\App streamlit and git hub app"

st.set_page_config(page_title="Bulk Link Fetcher", page_icon="📦")

st.title("📦 Bulk Link Fetcher")
st.write("Upload an Excel file with a column of URLs to download them all at once.")

# --- UI: FILE UPLOAD ---
uploaded_file = st.file_uploader("Upload Excel or CSV file", type=["xlsx", "csv"])

if uploaded_file:
    # Read the file
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.write("### Preview of Data", df.head())
    
    # Let user select the column containing links
    column_name = st.selectbox("Select the column containing the URLs:", df.columns)
    
    if st.button("Start Bulk Download"):
        links = df[column_name].dropna().tolist()
        
        if not links:
            st.warning("No links found in the selected column.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Temporary storage for the ZIP file
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for i, link in enumerate(links):
                    try:
                        # 1. Fetch File
                        response = requests.get(link, timeout=15)
                        response.raise_for_status()
                        
                        # Get filename
                        filename = link.split("/")[-1].split("?")[0] or f"file_{i}"
                        content = response.content
                        
                        # 2. Save to Local C: Drive
                        if not os.path.exists(LOCAL_SAVE_PATH):
                            os.makedirs(LOCAL_SAVE_PATH)
                        
                        local_file_path = os.path.join(LOCAL_SAVE_PATH, filename)
                        with open(local_file_path, "wb") as f:
                            f.write(content)
                        
                        # 3. Add to ZIP (for the web download)
                        zip_file.writestr(filename, content)
                        
                    except Exception as e:
                        st.error(f"Failed to download {link}: {e}")
                    
                    # Update Progress
                    progress = (i + 1) / len(links)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing: {i+1}/{len(links)}")

            st.success(f"✅ All files processed and saved locally to: {LOCAL_SAVE_PATH}")

            # 4. Provide the All-in-One ZIP Download
            st.divider()
            st.write("### Web Download")
            st.download_button(
                label="📥 Download All Files as ZIP",
                data=zip_buffer.getvalue(),
                file_name="bulk_downloads.zip",
                mime="application/zip"
            )
