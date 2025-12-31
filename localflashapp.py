import streamlit as st
import requests
import os
from io import BytesIO

# --- CONFIGURATION ---
# Your specific local folder
LOCAL_SAVE_PATH = r"C:\Users\kanna\Pictures\App streamlit and git hub app"

st.set_page_config(page_title="Link Fetcher", page_icon="📥")

st.title("📥 Link Fetcher & Saver")
st.info(f"Local Save Directory: `{LOCAL_SAVE_PATH}`")

# --- FUNCTIONS ---
def download_file(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        filename = url.split("/")[-1].split("?")[0] or "downloaded_file"
        return response.content, filename
    except Exception as e:
        st.error(f"Error fetching the link: {e}")
        return None, None

# --- UI ---
url = st.text_input("Enter the file URL:", placeholder="https://example.com/image.jpg")

if url:
    if st.button("Process Link"):
        content, file_name = download_file(url)
        
        if content:
            # 1. Attempt Local Save (Works on your PC)
            try:
                if not os.path.exists(LOCAL_SAVE_PATH):
                    os.makedirs(LOCAL_SAVE_PATH)
                
                full_path = os.path.join(LOCAL_SAVE_PATH, file_name)
                with open(full_path, "wb") as f:
                    f.write(content)
                st.success(f"✅ Saved locally to: {full_path}")
            except Exception as e:
                st.warning("Could not save to C: drive (Likely running on the Web/Cloud).")

            # 2. Web Download (Works everywhere)
            st.write("---")
            st.write("Click below to save to your browser's download folder:")
            st.download_button(
                label="💾 Download to Computer",
                data=content,
                file_name=file_name,
                mime="application/octet-stream"
            )

# --- INSTRUCTIONS FOR GITHUB ---
with st.sidebar:
    st.header("Deployment Checklist")
    st.markdown("""
    1. **GitHub:** Push this `app.py`.
    2. **Requirements:** Create `requirements.txt` with:
       ```
       streamlit
       requests
       ```
    3. **Connect:** Link this repo to [share.streamlit.io](https://share.streamlit.io).
    """)
