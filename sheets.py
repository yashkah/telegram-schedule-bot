import gspread
from oauth2client.service_account import ServiceAccountCredentials

def connect_to_sheet():
    scope = ["https://spreadsheets.google.com/feeds", 
             "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    # Открываем таблицу по названию
    spreadsheet = client.open("English Schedule")

    return {
        "schedule": spreadsheet.worksheet("May 25"),  # Название листа с занятиями
        "users": spreadsheet.worksheet("Users")         # Название листа для студентов
    }
