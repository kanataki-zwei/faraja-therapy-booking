import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

def connect_to_gsheet():
    """Authenticate and connect to Google Sheets using Streamlit secrets"""
    try:
        # ✅ Load credentials from Streamlit Secrets
        creds_dict = st.secrets["gcp_service_account"]

        # ✅ Authenticate with Google Sheets API
        creds = Credentials.from_service_account_info(creds_dict, scopes=[
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ])

        client = gspread.authorize(creds)

        # ✅ Load Google Sheet ID from Streamlit secrets
        sheet_id = st.secrets["google_sheets"]["sheet_id"]
        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.sheet1  # First sheet (assumed to be "Sessions")

        return client, spreadsheet, sheet

    except Exception as e:
        st.error(f"❌ Failed to connect to Google Sheets: {e}")
        return None, None, None  # Ensure function returns valid values on failure

def get_sessions(sheet):
    """Fetch therapy sessions from Google Sheets and return as a DataFrame"""
    try:
        # ✅ Ensure the sheet object is valid before fetching data
        if not sheet:
            raise ValueError("Google Sheet connection is not established.")

        # ✅ Fetch all records and convert to DataFrame
        data = sheet.get_all_records()
        return pd.DataFrame(data)

    except Exception as e:
        st.error(f"❌ Error fetching session data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on failure
