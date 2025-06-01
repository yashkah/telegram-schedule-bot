"""
Utility functions for the Telegram bot.
"""

from telegram_bot.sheets.google import connect_to_sheet
import os
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import ContextTypes

# Get admin ID from environment variable
ADMIN_ID = os.getenv("ADMIN_ID")

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

async def notify_admin_command_usage(
    context: ContextTypes.DEFAULT_TYPE,
    update: Update,
    command: str
) -> None:
    """
    Notify admin about command usage.
    
    Args:
        context: The context object
        update: The update object containing user info
        command: The command that was used
    """
    if not ADMIN_ID:
        print("⚠️ ADMIN_ID not set in environment variables")
        return
        
    user = update.effective_user
    warsaw_tz = pytz.timezone('Europe/Warsaw')
    timestamp = datetime.now(warsaw_tz).strftime("%d.%m.%Y %H:%M:%S")
    
    message = (
        f"🔔 *Command Used*\n\n"
        f"👤 *User:* {user.first_name}"
        f"{f' (@{user.username})' if user.username else ''}\n"
        f"🆔 *Telegram ID:* `{user.id}`\n"
        f"📝 *Command:* `/{command}`\n"
        f"⏰ *Time:* {timestamp}"
    )
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=message,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"❌ Failed to send admin notification: {e}") 