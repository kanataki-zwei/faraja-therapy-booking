import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Config
sheet_id = "1VpvxpRZOkLprum6D7F_ozYO26l20Y0GgVqkOktzEaQU"
json_key_file = "credentials/google_sheets_creds.json"

def connect_to_gsheet(sheet_id, json_key_file):
    """Authenticate and connect to Google Sheets"""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(json_key_file, scopes=scope)
    client = gspread.authorize(creds)
    
    # ✅ Open the full Spreadsheet (not just one sheet)
    spreadsheet = client.open_by_key(sheet_id)
    sheet = spreadsheet.sheet1  # First sheet (assumed to be "Sessions")

    return client, spreadsheet, sheet  # Return full spreadsheet object

def get_sessions(sheet):
    """Fetch therapy sessions from Google Sheets and return as a DataFrame"""
    data = sheet.get_all_records()
    return pd.DataFrame(data)


