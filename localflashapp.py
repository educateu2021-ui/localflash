import streamlit as st
import requests
import os
from pathlib import Path

# Set the target local folder path
SAVE_PATH = r"C:\Users\kanna\Pictures\App streamlit and git hub app"

def download_file(url, folder):
    # Create the directory if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)
        st.info(f"Created new directory: {folder}")

    try:
        # Get the filename from the URL
        filename = url.split("/")[-1].split("?")[0]
        if not filename:
            filename = "downloaded_file"
        
        full_path = os.path.join(folder, filename)

        # Fetch the content
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Write to local folder
        with open(full_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True, full_path
    except Exception as e:
        return False, str(e)

# Streamlit UI
st.title("🔗 Link Fetcher & Local Saver")
st.write(f"Files will be saved to: `{SAVE_PATH}`")

url_input = st.text_input("Paste the link (URL) here:", placeholder="https://example.com/image.jpg")

if st.button("Download and Save Local"):
    if url_input:
        with st.spinner("Fetching and saving..."):
            success, result = download_file(url_input, SAVE_PATH)
            
            if success:
                st.success(f"✅ Success! Saved to: {result}")
            else:
                st.error(f"❌ Error: {result}")
    else:
        st.warning("Please enter a valid URL.")
