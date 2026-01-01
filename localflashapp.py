import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# --- BROWSER SETUP FOR STREAMLIT CLOUD ---
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

st.set_page_config(page_title="E-Vandi Data Logger", page_icon="🚗")

st.title("🚗 E-Vandi | AckoDrive Automation")
st.markdown("Enter the registration number to automate fetching and splitting data.")

# --- USER INPUT ---
v_number = st.text_input("Enter Vehicle Number", placeholder="TN 18 BK 0911").upper()

if st.button("Automate Fetch & Save"):
    if v_number:
        driver = get_driver()
        try:
            with st.spinner('Opening AckoDrive and entering details...'):
                driver.get("https://ackodrive.com/used/car-valuation/")
                
                # 1. Find the input box and type the number
                # Acko uses a generic input or a specific ID for the form
                wait = WebDriverWait(driver, 10)
                input_field = wait.until(EC.presence_of_element_located((By.TAG_NAME, "input")))
                input_field.send_keys(v_number)
                
                # 2. Click the 'Check' or 'Next' button
                # Finding button by text since IDs change
                button = driver.find_element(By.XPATH, "//button[contains(text(), 'Check') or contains(text(), 'Next')]")
                button.click()

                # 3. Wait for the result elements to appear
                # Using the classes you provided in your HTML snippet
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "styles__Title-sc-c73839da-5")))
                
                # 4. Extract Data
                title = driver.find_element(By.CLASS_NAME, "styles__Title-sc-c73839da-5").text
                reg_no = driver.find_element(By.CLASS_NAME, "styles__RegNo-sc-c73839da-6").text
                img_url = driver.find_element(By.CLASS_NAME, "styles__ImageData-sc-c73839da-4").get_attribute("src")
                other_data = driver.find_element(By.CLASS_NAME, "styles__OtherData-sc-c73839da-14").text
                
                # 5. Split 'Other Data' (e.g., VXI • petrol • 2022)
                parts = other_data.split("•")
                variant = parts[0].strip() if len(parts) > 0 else "N/A"
                fuel = parts[1].strip() if len(parts) > 1 else "N/A"
                year = parts[2].strip() if len(parts) > 2 else "N/A"

                # --- DISPLAY OUTPUT ---
                st.success("Data Extracted Successfully!")
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(img_url, caption="Vehicle Preview", use_column_width=True)
                
                with col2:
                    results = {
                        "Field": ["Title", "Reg No", "Variant", "Fuel Type", "Year"],
                        "Information": [title, reg_no, variant, fuel, year]
                    }
                    df = pd.DataFrame(results)
                    st.table(df)

                # --- DOWNLOAD EXCEL ---
                excel_df = pd.DataFrame([{
                    "Title": title, "RegNo": reg_no, "Variant": variant, "Fuel": fuel, "Year": year, "Image": img_url
                }])
                
                st.download_button(
                    label="📥 Download Excel Report",
                    data=excel_df.to_csv(index=False).encode('utf-8'),
                    file_name=f"Acko_Report_{v_number}.csv",
                    mime="text/csv",
                )

        except Exception as e:
            st.error(f"Error: Could not find results. {e}")
        finally:
            driver.quit()
    else:
        st.warning("Please enter a registration number.")
