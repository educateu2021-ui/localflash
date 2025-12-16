import streamlit as st
import time

# --- 1. CONFIGURATION & STATE ---
st.set_page_config(
    page_title="LocalFlash - Thevaiyur South",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize Session State for Mock Data & Interactions
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'category_filter' not in st.session_state:
    st.session_state.category_filter = "All"
if 'claimed_deals' not in st.session_state:
    st.session_state.claimed_deals = []

# Mock Database of Deals
deals_data = [
    {
        "id": 1,
        "name": "Siva Vegetables",
        "category": "Grocery",
        "icon": "🥬",
        "rating": "4.2",
        "count": "145",
        "location": "Near Old Temple, North St",
        "distance": "0.2 km",
        "badge_text": "Live Offer",
        "badge_color": "orange",
        "offer_title": "Tomatoes @ ₹15/kg",
        "offer_sub": "₹40",
        "offer_desc": "Stock clearance • Ends 8:00 PM",
        "action_btn": "CLAIM",
        "whatsapp": "9876543210",
        "verified": True
    },
    {
        "id": 2,
        "name": "Kumar Plumbing Works",
        "category": "Repair",
        "icon": "🚿",
        "rating": "4.8",
        "count": "52",
        "location": "Service Road, Opp. Bus Stand",
        "distance": "0.8 km",
        "badge_text": "Available Now",
        "badge_color": "blue",
        "offer_title": "Instant Visit (No Wait)",
        "offer_sub": "",
        "offer_desc": "Technician free for next 1 hour",
        "action_btn": "BOOK",
        "whatsapp": "9876543210",
        "verified": False
    },
    {
        "id": 3,
        "name": "Glow Ladies Salon",
        "category": "Salon",
        "icon": "💅",
        "rating": "New",
        "count": "4",
        "location": "Main Bazaar",
        "distance": "0.1 km",
        "badge_text": "Empty Seats",
        "badge_color": "purple",
        "offer_title": "50% Off Facial",
        "offer_sub": "",
        "offer_desc": "Only until 5:00 PM today",
        "action_btn": "BOOK",
        "whatsapp": "9876543210",
        "verified": True
    }
]

# --- 2. CUSTOM CSS (Replicating the Design) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;900&display=swap');
    
    /* General App Styling */
    .stApp {
        background-color: #f0f2f5;
        font-family: 'Roboto', sans-serif;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom Colors */
    :root {
        --jd-blue: #0076d7;
        --jd-orange: #FF6B35;
        --jd-slate: #333333;
    }

    /* Flash Animation for Badges */
    @keyframes flash {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    .flash-dot {
        height: 8px;
        width: 8px;
        background-color: currentColor;
        border-radius: 50%;
        display: inline-block;
        animation: flash 1.5s infinite;
        margin-right: 4px;
    }

    /* Card Styling */
    .jd-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    
    /* Header Styling */
    .custom-header {
        background: white;
        padding: 10px;
        border-bottom: 1px solid #eee;
        position: sticky;
        top: 0;
        z-index: 100;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* Category Grid Styling */
    .cat-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        margin-bottom: 10px;
    }
    .cat-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        margin-bottom: 4px;
    }
    .cat-label {
        font-size: 11px;
        color: #374151;
        font-weight: 500;
    }
    
    /* Offer Box */
    .offer-box {
        padding: 8px;
        border-radius: 4px;
        margin: 8px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .orange-box { background-color: #fff7ed; border: 1px solid #ffedd5; }
    .blue-box { background-color: #eff6ff; border: 1px solid #dbeafe; }
    .purple-box { background-color: #faf5ff; border: 1px solid #f3e8ff; }

    /* Bottom Nav (Simulated Visual) */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background: white;
        border-top: 1px solid #e5e7eb;
        display: flex;
        justify-content: space-around;
        padding: 8px 0;
        z-index: 999;
    }
    
    /* Utility */
    .text-xs { font-size: 12px; }
    .font-bold { font-weight: 700; }
    .stButton button {
        width: 100%;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. HEADER SECTION ---
# Custom HTML Header to match the "LF" Logo
st.markdown("""
<div class="custom-header">
    <div style="display:flex; gap:8px; align-items:center;">
        <div style="background:#FF6B35; color:white; font-weight:900; padding:2px 6px; border-radius:4px; transform: skewX(-12deg);">LF</div>
        <div>
            <div style="font-weight:bold; color:#333; line-height:1.1;">LocalFlash</div>
            <div style="font-size:11px; color:#666;">📍 Thevaiyur South ▼</div>
        </div>
    </div>
    <div style="display:flex; gap:8px; align-items:center;">
        <span style="font-size:10px; border:1px solid #ccc; padding:2px 4px; border-radius:4px; color:#666;">EN/TA</span>
        <span style="font-size:20px; color:#666;">👤</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Search Bar (Functional)
search_col1, search_col2 = st.columns([4, 1])
with search_col1:
    search_input = st.text_input("Search", placeholder="Search 'Plumber' or '50% Off'...", label_visibility="collapsed")
with search_col2:
    if st.button("GO", type="primary"):
        st.session_state.search_query = search_input

# --- 4. CATEGORIES SECTION ---
st.markdown("<br>", unsafe_allow_html=True)
with st.container():
    st.markdown('<div style="background:white; padding:15px; border-radius:8px; box-shadow:0 1px 2px rgba(0,0,0,0.1);">', unsafe_allow_html=True)
    
    # Grid of Categories (Functional filtering)
    cat_cols = st.columns(4)
    categories = [
        ("Food", "utensils", "🍽️", "#eff6ff", "#2563eb"),
        ("Grocery", "basket", "🧺", "#fff7ed", "#ea580c"),
        ("Salon", "scissors", "✂️", "#faf5ff", "#9333ea"),
        ("Repair", "hammer", "🔨", "#f0fdf4", "#16a34a"),
    ]
    
    for i, (name, icon_name, emoji, bg, color) in enumerate(categories):
        with cat_cols[i]:
            if st.button(f"{emoji}\n{name}", key=f"cat_{name}", help=f"Filter by {name}"):
                st.session_state.category_filter = name

    cat_cols_2 = st.columns(4)
    categories_2 = [
        ("Electric", "plug", "🔌", "#fefce8", "#ca8a04"),
        ("Tailor", "shirt", "👕", "#fef2f2", "#dc2626"),
        ("Water", "droplet", "💧", "#ecfeff", "#0891b2"),
        ("More", "dots", "⋯", "#f3f4f6", "#4b5563"),
    ]

    for i, (name, icon_name, emoji, bg, color) in enumerate(categories_2):
        with cat_cols_2[i]:
            if st.button(f"{emoji}\n{name}", key=f"cat_{name}", help=f"Filter by {name}"):
                if name == "More":
                    st.session_state.category_filter = "All" # Reset
                else:
                    st.session_state.category_filter = name
                    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. DEALS FEED SECTION ---
st.markdown("""
    <div style="margin-top:20px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:13px; font-weight:bold; color:#6b7280; text-transform:uppercase; letter-spacing:0.5px;">Nearby Flash Deals</span>
        <span style="font-size:11px; color:#FF6B35;">""" + 
        (f"Filtering: {st.session_state.category_filter}" if st.session_state.category_filter != "All" else "Showing All") + 
        """</span>
    </div>
""", unsafe_allow_html=True)

# Filter Logic
filtered_deals = [
    d for d in deals_data 
    if (st.session_state.category_filter == "All" or d['category'] == st.session_state.category_filter)
    and (st.session_state.search_query.lower() in d['name'].lower() or st.session_state.search_query.lower() in d['offer_title'].lower() or st.session_state.search_query == "")
]

if not filtered_deals:
    st.info("No deals found for your search filters.")

# Render Cards
for deal in filtered_deals:
    # Card Container
    with st.container():
        # Using HTML for the complex layout parts to ensure design fidelity
        st.markdown(f"""
        <div class="jd-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <div style="display:flex; gap:12px;">
                    <div style="width:56px; height:56px; background:#e5e7eb; border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:24px;">
                        {deal['icon']}
                    </div>
                    <div>
                        <div style="font-weight:bold; color:#1f2937; display:flex; align-items:center; gap:4px;">
                            {deal['name']}
                            {'<span style="color:#3b82f6;">✓</span>' if deal['verified'] else ''}
                        </div>
                        <div style="display:flex; align-items:center; gap:4px; margin-bottom:2px;">
                            <span style="background:{'#16a34a' if deal['rating'] != 'New' else '#9ca3af'}; color:white; font-size:10px; font-weight:bold; padding:1px 4px; border-radius:2px;">{deal['rating']}</span>
                            <span style="font-size:11px; color:#6b7280;">({deal['count']} Ratings)</span>
                        </div>
                        <div style="font-size:11px; color:#6b7280;">{deal['location']}</div>
                    </div>
                </div>
                <div style="font-size:11px; color:#9ca3af; font-family:monospace;">{deal['distance']}</div>
            </div>
            
            <div class="offer-box {deal['badge_color']}-box">
                <div>
                    <div style="font-size:11px; font-weight:bold; color:{deal['badge_color']}; text-transform:uppercase; margin-bottom:2px;">
                        <span class="flash-dot" style="color:{deal['badge_color'] if deal['badge_color'] != 'orange' else '#ea580c'}"></span> {deal['badge_text']}
                    </div>
                    <div style="font-size:14px; font-weight:bold; color:#1f2937;">
                        {deal['offer_title']} 
                        <span style="text-decoration:line-through; color:#9ca3af; font-size:11px;">{deal['offer_sub']}</span>
                    </div>
                    <div style="font-size:10px; color:#6b7280;">{deal['offer_desc']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action Buttons (Native Streamlit for Functionality)
        # We place these immediately after the HTML block to simulate being "inside" the card
        c1, c2, c3 = st.columns([1, 1, 1])
        
        with c1:
            st.link_button("💬 WhatsApp", f"https://wa.me/{deal['whatsapp']}", use_container_width=True)
        with c2:
            st.link_button("📞 Call Now", f"tel:{deal['whatsapp']}", use_container_width=True)
        with c3:
            # Logic to handle claiming
            is_claimed = deal['id'] in st.session_state.claimed_deals
            
            if is_claimed:
                st.button("✅ Done", key=f"done_{deal['id']}", disabled=True, use_container_width=True)
            else:
                if st.button(deal['action_btn'], key=f"act_{deal['id']}", type="primary", use_container_width=True):
                    st.session_state.claimed_deals.append(deal['id'])
                    st.toast(f"Success! {deal['action_btn']} confirmed for {deal['name']}", icon="🎉")
                    time.sleep(0.5)
                    st.rerun()

# --- 6. BOTTOM NAVIGATION (Visual Replica) ---
st.markdown("""
<div class="bottom-nav">
    <div style="text-align:center; color:#0076d7; width:20%;">
        <div style="font-size:20px;">🏠</div>
        <div style="font-size:10px; font-weight:bold;">Home</div>
    </div>
    <div style="text-align:center; color:#6b7280; width:20%;">
        <div style="font-size:20px;">▦</div>
        <div style="font-size:10px; font-weight:500;">Cats</div>
    </div>
    <div style="position:relative; top:-25px; width:20%; display:flex; justify-content:center;">
        <div style="background:#FF6B35; color:white; width:48px; height:48px; border-radius:50%; display:flex; flex-direction:column; align-items:center; justify-content:center; box-shadow:0 4px 6px rgba(0,0,0,0.1); border:4px solid #f0f2f5;">
            <div style="font-size:20px; line-height:1;">+</div>
            <div style="font-size:7px; font-weight:bold; text-transform:uppercase;">Post</div>
        </div>
    </div>
    <div style="text-align:center; color:#6b7280; width:20%;">
        <div style="font-size:20px;">🔔</div>
        <div style="font-size:10px; font-weight:500;">Alerts</div>
    </div>
    <div style="text-align:center; color:#6b7280; width:20%;">
        <div style="font-size:20px;">👤</div>
        <div style="font-size:10px; font-weight:500;">Account</div>
    </div>
</div>
<div style="height:60px;"></div> """, unsafe_allow_html=True)
