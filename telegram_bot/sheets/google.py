"""
Google Sheets connection functionality.
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

def connect_to_sheet():
    """Connect to Google Sheets and return worksheet references."""
    scope = ["https://spreadsheets.google.com/feeds", 
             "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    spreadsheet = client.open("English Schedule")

    return {
        "schedule": spreadsheet.worksheet("May 25"),
        "users": spreadsheet.worksheet("Users"),
        "slots": spreadsheet.worksheet("Slots")
    } 