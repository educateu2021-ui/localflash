import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# --- Page Setup ---
st.set_page_config(page_title="PB Vehicle Scraper", page_icon="🚗")
st.title("🚗 PolicyBazaar Vehicle Scraper")

@st.cache_resource
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # This line is the FIX: It tells the manager to look for CHROMIUM (Streamlit's default)
    return webdriver.Chrome(
        service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
        options=options
    )

def fetch_details(veh_num):
    driver = get_driver()
    url = "https://www.policybazaar.com/rto/vehicle-owner-details/"
    
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        
        # 1. Wait for and fill the input field
        input_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.carRegistrationNumber")))
        input_box.clear()
        input_box.send_keys(veh_num)
        
        # 2. Click Check Details
        btn = driver.find_element(By.ID, "btnSubmit")
        btn.click()
        
        # 3. Wait for the result screen to load
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "carDetailsFetched")))
        
        # 4. Extract Data
        make_model = driver.find_element(By.CLASS_NAME, "MakeModel").text
        fuel = driver.find_element(By.CLASS_NAME, "fuel").text
        
        return {"success": True, "make": make_model, "fuel": fuel}
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- UI Interface ---
v_number = st.text_input("Enter Vehicle Number", placeholder="DL1AB1234").upper()

if st.button("Fetch Data"):
    if v_number:
        with st.spinner("Searching..."):
            res = fetch_details(v_number)
            if res["success"]:
                st.success(f"Found: {res['make']}")
                st.info(f"Fuel Type: {res['fuel']}")
            else:
                st.error("Could not find details. The site might be blocking the request.")
    else:
        st.warning("Please enter a number.")
