import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

def connect_to_gsheet():
    """Authenticate and connect to Google Sheets using Streamlit secrets"""
    try:
        # Load credentials from Streamlit Secrets (already a dict)
        creds_dict = st.secrets["gcp_service_account"]

        # ✅ Remove json.dumps()—not needed!
        creds = Credentials.from_service_account_info(creds_dict, scopes=[
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ])

        client = gspread.authorize(creds)

        # Load Google Sheet ID from secrets
        sheet_id = st.secrets["google_sheets"]["sheet_id"]
        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.sheet1  # First sheet (assumed to be "Sessions")

        return client, spreadsheet, sheet
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {e}")
        return None, None, None
