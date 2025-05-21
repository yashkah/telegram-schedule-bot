import gspread
from oauth2client.service_account import ServiceAccountCredentials

def connect_to_sheet():
    scope = ["https://spreadsheets.google.com/feeds", 
             "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    # Подключаемся к таблице по названию
    sheet = client.open("English Schedule").sheet1
    return sheet

if __name__ == "__main__":
    sheet = connect_to_sheet()
    data = sheet.get_all_records()

    for row in data:
        print(row)
