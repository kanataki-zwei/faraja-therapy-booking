import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import json

def connect_to_gsheet():
    """Authenticate and connect to Google Sheets using Streamlit secrets"""
    # Load credentials from Streamlit Secrets
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(json.loads(json.dumps(creds_dict)), scopes=[
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ])
    
    client = gspread.authorize(creds)

    # Load Google Sheet ID from secrets
    sheet_id = st.secrets["google_sheets"]["sheet_id"]
    spreadsheet = client.open_by_key(sheet_id)
    sheet = spreadsheet.sheet1  # First sheet (assumed to be "Sessions")

    return client, spreadsheet, sheet

def get_sessions(sheet):
    """Fetch therapy sessions from Google Sheets and return as a DataFrame"""
    data = sheet.get_all_records()
    return pd.DataFrame(data)
