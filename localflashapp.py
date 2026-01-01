import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# --- Page Configuration ---
st.set_page_config(page_title="Vehicle Detail Finder", page_icon="🚗")

st.title("🚗 Vehicle Details Extractor")
st.markdown("Enter your vehicle number to fetch details from PolicyBazaar.")

# --- Selenium Driver Setup ---
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    # User agent helps bypass simple bot detection
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

# --- Scraping Function ---
def fetch_vehicle_data(v_number):
    driver = get_driver()
    url = "https://www.policybazaar.com/rto/vehicle-owner-details/"
    
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 20)

        # 1. Type Vehicle Number
        input_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.carRegistrationNumber")))
        input_field.clear()
        input_field.send_keys(v_number)
        
        # 2. Click Submit
        submit_btn = driver.find_element(By.ID, "btnSubmit")
        submit_btn.click()

        # 3. Wait for the result section to load (Step 9 in your HTML)
        # We wait for the 'MakeModel' class to appear
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "MakeModel")))
        
        # 4. Extract Details
        make_model = driver.find_element(By.CLASS_NAME, "MakeModel").text
        fuel_type = driver.find_element(By.CLASS_NAME, "fuel").text
        
        return {
            "status": "success",
            "make_model": make_model,
            "fuel": fuel_type
        }

    except Exception as e:
        # Check if we were blocked by Cloudflare
        if "cloudflare" in driver.page_source.lower():
            return {"status": "error", "message": "Blocked by Cloudflare/Bot Detection."}
        return {"status": "error", "message": str(e)}
    finally:
        driver.quit()

# --- UI Logic ---
v_input = st.text_input("Vehicle Number", placeholder="e.g. DL1AB1234").upper().replace(" ", "")

if st.button("Check Details"):
    if v_input:
        with st.spinner("Fetching details from PolicyBazaar..."):
            result = fetch_vehicle_data(v_input)
            
            if result["status"] == "success":
                st.success("Details Found!")
                col1, col2 = st.columns(2)
                col1.metric("Manufacturer/Model", result["make_model"])
                col2.metric("Fuel Type", result["fuel"])
            else:
                st.error(f"Error: {result['message']}")
                st.info("Note: The website might be blocking the automated request. Try again later.")
    else:
        st.warning("Please enter a vehicle number.")
