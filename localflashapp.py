import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# --- Page Config ---
st.set_page_config(page_title="Vehicle Detail Scraper", page_icon="🚗")
st.title("🚗 Vehicle Info Extractor")
st.write("Enter a vehicle number to fetch details from the portal.")

# --- Selenium Setup ---
def get_driver():
    options = Options()
    options.add_argument("--headless")  # Run without opening a browser window
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

# --- Scraping Logic ---
def fetch_vehicle_details(v_number):
    driver = get_driver()
    # Replace with the actual URL of the insurance portal
    TARGET_URL = "https://www.example-insurance-site.com" 
    
    try:
        driver.get(TARGET_URL)
        wait = WebDriverWait(driver, 15)

        # 1. Locate the input field and type the number
        input_field = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "carRegistrationNumber")))
        input_field.send_keys(v_number)

        # 2. Click the 'Check Details' button
        submit_btn = driver.find_element(By.ID, "btnSubmit")
        submit_btn.click()

        # 3. Wait for the result div to appear (Step 9 in your HTML)
        # We wait for the 'MakeModel' span to have text
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "carDetailsFetched")))
        
        # 4. Extract the data
        make_model = driver.find_element(By.CLASS_NAME, "MakeModel").text
        fuel_type = driver.find_element(By.CLASS_NAME, "fuel").text
        
        return {
            "Status": "Success",
            "Vehicle": make_model,
            "Fuel": fuel_type
        }

    except Exception as e:
        return {"Status": "Error", "Message": str(e)}
    finally:
        driver.quit()

# --- Streamlit UI ---
veh_num = st.text_input("Enter Vehicle Number (e.g., DL1AB1234)", placeholder="MH01AB1234")

if st.button("Search Vehicle"):
    if veh_num:
        with st.spinner('Fetching details from the portal...'):
            result = fetch_vehicle_details(veh_num)
            
            if result["Status"] == "Success":
                st.success("Vehicle Found!")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Make & Model", result["Vehicle"])
                with col2:
                    st.metric("Fuel Type", result["Fuel"])
                
                # Visual display of the found data
                st.info(f"The system identified this vehicle as a **{result['Vehicle']}** running on **{result['Fuel']}**.")
            else:
                st.error(f"Could not find details. Error: {result['Message']}")
    else:
        st.warning("Please enter a valid vehicle number.")
