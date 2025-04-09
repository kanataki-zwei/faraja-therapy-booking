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
    <div style="display: flex; align-items: center; flex-wrap: wrap; justify-content: center; gap: 20px; width: 100%; padding: 20px 0; border-bottom: 1px solid #e0e0e0;">
        <img src="data:image/png;base64,{logo_base64}" style="height: 60px;">
        <h1 style="margin: 0; font-size: 2.2rem; color: #1697D4;">Faraja Cancer Therapy Booking System</h1>
    </div>
    """,
    unsafe_allow_html=True
)


# ======================
# Sidebar Navigation (Styled)
# ======================
# Inject custom CSS for boxy buttons
st.markdown("""
    <style>
    /* Base Layout */
    body {
        font-family: 'Segoe UI', sans-serif;
        background-color: #ffffff;
    }

    .main {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
    }

    /* Headers */
    h1, h2, h3, h4 {
        color: #1697D4;  /* Faraja Blue */
    }

    /* Sidebar Radio Buttons */
    .sidebar-radio .stRadio > div {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .sidebar-radio .stRadio label {
        background-color: #ffffff;
        color: #1697D4;
        padding: 12px 18px;
        border-radius: 10px;
        border: 2px solid #1697D4;
        font-weight: 600;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    .sidebar-radio .stRadio label:hover {
        background-color: #e1f2fa;
        border-color: #127fb2;
    }

    .sidebar-radio .stRadio input:checked + div > label {
        background-color: #1697D4;
        color: white;
        border-color: #1697D4;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    }

    /* Buttons */
    .stButton > button {
        background-color: #1697D4;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-size: 1rem;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease-in-out;
        cursor: pointer;
    }

    .stButton > button:hover {
        background-color: #127fb2;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.08);
        transform: translateY(-2px);
    }


    /* Input Fields */
    .stTextInput>div>div>input,
    .stDateInput>div>input {
        border-radius: 8px;
        border: 1px solid #ccc;
        padding: 6px;
    }

    /* Footer */
    hr {
        border: none;
        border-top: 1px solid #eee;
    }

    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        h1 {
            font-size: 1.5rem !important;
        }
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

# ======================
# Footer
# ======================
st.markdown(
    """
    <hr style="margin-top: 2rem;"/>
    <div style="text-align: center; font-size: 0.85rem; color: #888;">
        © 2025 Faraja Cancer Support. All rights reserved.
    </div>
    """,
    unsafe_allow_html=True
)

