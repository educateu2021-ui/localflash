import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# --- Page Config ---
st.set_page_config(page_title="CarInfo Vehicle Search", page_icon="🏎️")
st.title("🏎️ CarInfo Vehicle Detail Scraper")

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Bypass bot detection headers
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # STREAMLIT CLOUD SPECIFIC PATHS
    # These paths are created by the packages.txt file
    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    
    return webdriver.Chrome(service=service, options=options)

def search_car_info(veh_num):
    driver = get_driver()
    url = "https://www.carinfo.app/rto-vehicle-registration-detail"
    
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)

        # 1. Find the input field
        # CarInfo uses a specific input for registration
        search_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'Enter Vehicle Number')]")))
        search_input.send_keys(veh_num)
        
        # 2. Click the search button (usually a magnifying glass or 'Search')
        search_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Search')] | //span[contains(@class, 'search')]")
        search_btn.click()
        
        # 3. Wait for results to load
        # We look for common labels like 'Owner Name' or 'Model'
        wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Owner')] | //*[contains(text(), 'Model')]")))
        
        # 4. Scrape the data found on page
        # This is a generic extraction of all 'key-value' pairs found in result cards
        results = {}
        info_cards = driver.find_elements(By.CSS_SELECTOR, "div[class*='Details'], div[class*='Card']")
        
        for card in info_cards:
            text = card.text
            if ":" in text:
                lines = text.split('\n')
                for line in lines:
                    if ":" in line:
                        parts = line.split(":", 1)
                        results[parts[0].strip()] = parts[1].strip()

        if not results:
            # Fallback: Just grab the whole page text if specific cards aren't found
            return {"status": "success", "raw_data": driver.find_element(By.TAG_NAME, "body").text[:500]}

        return {"status": "success", "data": results}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        driver.quit()

# --- Streamlit UI ---
veh_no = st.text_input("Enter Vehicle Number", placeholder="e.g. MH01AB1234").upper().replace(" ", "")

if st.button("Get Details"):
    if veh_no:
        with st.spinner("Accessing CarInfo.app..."):
            result = search_car_info(veh_no)
            
            if result["status"] == "success":
                st.success("Details Extracted!")
                if "data" in result:
                    # Display as a clean table
                    st.table(result["data"])
                else:
                    st.write(result["raw_data"])
            else:
                st.error(f"Error: {result['message']}")
                st.info("Tip: CarInfo often uses Captchas. If this fails, the site is blocking automated access.")
    else:
        st.warning("Please enter a vehicle number.")
