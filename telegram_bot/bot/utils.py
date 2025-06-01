"""
Utility functions for the Telegram bot.
"""

from telegram_bot.sheets.google import connect_to_sheet

def save_user_to_users_sheet(name, username, telegram_id, timestamp):
    """Save new user info to Users worksheet."""
    sheets = connect_to_sheet()
    users_sheet = sheets["users"]
    data = users_sheet.get_all_records()

    existing_ids = [str(row["Telegram ID"]) for row in data]

    if str(telegram_id) not in existing_ids:
        users_sheet.append_row([name, username, telegram_id, timestamp, "", "", ""])
        print(f"✅ New user saved: {name} (ID: {telegram_id})")
    else:
        print(f"👀 User already exists: {telegram_id}") 