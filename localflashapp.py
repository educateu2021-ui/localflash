import pandas as pd
import io
import time
from urllib.parse import urljoin

st.set_page_config(page_title="Robust Car Scraper", layout="wide")
st.title("🚗 Robust CarWale Variant & Image Scraper")
st.set_page_config(page_title="Ultimate Car Scraper", layout="wide")
st.title("🚗 Multi-Format Car Variant Scraper")

def scrape_car_data(url):
headers = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
}
try:
response = requests.get(url, headers=headers, timeout=20)
@@ -21,97 +19,89 @@ def scrape_car_data(url):

soup = BeautifulSoup(response.text, 'html.parser')

        # --- 1. ROBUST IMAGE EXTRACTION ---
        # Instead of specific classes, we look for the main image in the top section
        # CarWale images usually have 'exterior' in the URL or are inside a 'section' tag
        image_url = "No Image Found"
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src', '') or img.get('data-src', '')
            # Robust check: look for high-res images that likely represent the car
            if 'exterior' in src.lower() or 'cw/ec' in src.lower():
                image_url = src
                break

        # --- 2. ROBUST TABLE EXTRACTION ---
        # We look for ANY table that contains the word "Variants" or "On-Road Price"
        rows = []
        tables = soup.find_all('table')
        for table in tables:
            if "Variants" in table.text or "Price" in table.text:
                rows = table.find_all('tr')
                break
        # Robust Row detection: looks for standard CarWale row patterns
        rows = soup.find_all('tr', class_=lambda x: x and ('version-table' in x or 'o-cp' in x or 'o-kY' in x))

if not rows:
            # Fallback to the class-based search if the generic table search fails
            rows = soup.find_all('tr', class_=lambda x: x and ('version-table' in x or 'o-cp' in x))

        if not rows:
            return None, "Upcoming Car or Table Not Found"
            return None, "Table structure not detected for this car."

page_data = []
for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2: continue # Skip empty or header-only rows
            # --- 1. VARIANT NAME & SPECS ---
            # Targeting the 'line="2"' pattern from your latest snippet
            variant_container = row.find('div', attrs={"line": "2"}) or row.find('a', class_='o-js')

            # Column 1: Variant & Specs
            col1 = cells[0]
            # Get the boldest/main text for the Name
            variant_name = col1.find('a').text.strip() if col1.find('a') else col1.get_text(separator=" ", strip=True).split("\n")[0]
            if not variant_container:
                continue

            # Full title usually contains the most detail
            full_title = variant_container.get('title', '').strip()
            variant_name = variant_container.get_text().strip()

            # Specs are often in a 'span' with a title or just smaller text
            specs_tag = col1.find('span', title=True)
            specs = specs_tag['title'] if specs_tag else "N/A"
            # Use the longer string as the variant name for better detail
            final_name = full_title if len(full_title) > len(variant_name) else variant_name

            # Extract Specs
            specs_tag = row.find('span', class_='o-jL')
            specs = specs_tag.get('title') if specs_tag else "N/A"

            # Column 2: Price
            col2 = cells[1]
            price = col2.get_text(separator=" ", strip=True).split("View")[0] # Clean "View Price Breakup"
            # If specs are missing but comma-separated in the name (common in Thar/Magnite)
            if specs == "N/A" and "," in final_name:
                specs = final_name.split(",", 1)[1].strip()

            # --- 2. ON-ROAD PRICE ---
            # Targeting the specific nested span/div for price
            price_tag = row.find('div', class_='o-eQ') or row.find('span', string=lambda t: t and "Lakh" in t)
            price = price_tag.get_text().strip() if price_tag else "N/A"

            if "Lakh" in price or "Cr" in price or "Rs." in price:
            # Clean up price (remove 'View Price' text)
            price = price.split("View")[0].strip()

            if final_name:
page_data.append({
                    "Brand/Model": url.split('/')[-2].replace('-', ' ').title(),
                    "Variant Name": variant_name,
                    "Variant Name": final_name,
"Specifications": specs,
"On-Road Price": price,
                    "Image Link": image_url
                    "URL": url
})

return page_data, None
except Exception as e:
        return None, f"Error: {str(e)}"
        return None, str(e)

# --- UI (Link & Excel) ---
tab1, tab2 = st.tabs(["🔗 Single URL", "📂 Bulk Excel (20+ Links)"])
# --- APP TABS ---
t1, t2 = st.tabs(["🔗 Single URL", "📂 Bulk Excel Upload"])

with tab1:
    u = st.text_input("Paste CarWale Link:")
    if st.button("Scrape"):
with t1:
    u = st.text_input("Paste CarWale Model Link:")
    if st.button("Extract Data"):
d, e = scrape_car_data(u)
        if d: 
            st.dataframe(pd.DataFrame(d))
            if d[0]["Image Link"] != "No Image Found":
                st.image(d[0]["Image Link"], width=400)
        else: st.error(e)
        if d:
            st.success(f"Found {len(d)} variants!")
            st.table(pd.DataFrame(d))
        else:
            st.error(e)

with tab2:
    f = st.file_uploader("Upload Excel", type=["xlsx"])
with t2:
    f = st.file_uploader("Upload Excel with URL list", type=["xlsx"])
if f:
df_in = pd.read_excel(f)
        c = st.selectbox("Link Column:", df_in.columns)
        if st.button("🚀 Bulk Run"):
            all_res = []
            p = st.progress(0)
        c = st.selectbox("Select URL Column:", df_in.columns)
        if st.button("🚀 Bulk Scrape All"):
            results = []
            progress = st.progress(0)
urls = df_in[c].dropna().tolist()
for i, link in enumerate(urls):
                st.write(f"Scraping: {link}")
res, _ = scrape_car_data(link)
                if res: all_res.extend(res)
                time.sleep(2.5) # Anti-block delay
                p.progress((i+1)/len(urls))
                if res: results.extend(res)
                time.sleep(2.5) # Prevent blocking
                progress.progress((i+1)/len(urls))

            if all_res:
                final = pd.DataFrame(all_res)
            if results:
                final = pd.DataFrame(results)
st.dataframe(final)
buf = io.BytesIO()
with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
final.to_excel(writer, index=False)
                st.download_button("Download Data", buf.getvalue(), "car_data.xlsx")
                st.download_button("📥 Download Combined Results", buf.getvalue(), "bulk_car_data.xlsx")
