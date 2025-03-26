import streamlit as st
from PIL import Image
import base64

# ======================
# ✅ Header + Logo
# ======================
def get_base64_image(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

logo_base64 = get_base64_image("assets/logo.png")

st.markdown(
    f"""
    <div style="display: flex; align-items: center; width: 100%; padding: 20px 0; border-bottom: 1px solid #555;">
        <img src="data:image/png;base64,{logo_base64}" style="height: 60px; margin-right: 20px;">
        <h1 style="margin: 0; font-size: 2rem;">Faraja Cancer Therapy Booking System</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ======================
# ✅ Sidebar Navigation (Styled)
# ======================
# Inject custom CSS for boxy buttons
st.markdown("""
    <style>
    .sidebar-radio .stRadio > div {
        display: flex;
        flex-direction: column;
    }
    .sidebar-radio .stRadio label {
        background-color: #444;
        color: white;
        padding: 10px 16px;
        margin-bottom: 8px;
        border-radius: 8px;
        cursor: pointer;
        border: 2px solid transparent;
        transition: 0.3s ease;
    }
    .sidebar-radio .stRadio label:hover {
        border-color: #888;
    }
    .sidebar-radio .stRadio input:checked + div > label {
        background-color: #1a73e8;
        border-color: #1a73e8;
    }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 📌 Navigation")
    st.markdown('<div class="sidebar-radio">', unsafe_allow_html=True)
    tab = st.radio(
        "Go to:",
        ["📅 Book Session", "🔁 Manage My Bookings"],
        key="nav_buttons",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ======================
# ✅ Route to Pages
# ======================
if tab == "📅 Book Session":
    from modules.book_session import render_book_session
    render_book_session()

elif tab == "🔁 Manage My Bookings":
    from modules.manage_bookings import render_manage_bookings
    render_manage_bookings()
