"""
Reminder functionality for English lessons.
"""

import asyncio
import schedule
import threading
import time
from datetime import datetime, timedelta
import pytz
from telegram.ext import Application

from telegram_bot.sheets.google import connect_to_sheet

async def send_reminders(app: Application):
    """Send reminders for upcoming lessons."""
    print("🔔 Checking for lessons to remind...")
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    sheets = connect_to_sheet()
    schedule_sheet = sheets["schedule"]
    data = schedule_sheet.get_all_records()

    for row in data:
        try:
            dt = datetime.strptime(f"{row['Date']} {row['Time']}", "%d.%m.%Y %H:%M")
            dt = pytz.timezone('Europe/Warsaw').localize(dt)
            
            # Check if lesson is in 1 hour
            if now + timedelta(hours=1) <= dt < now + timedelta(hours=1, minutes=5):
                user_id = row["Telegram_ID"]
                message = (
                    f"⏰ *Reminder:* Your lesson is in 1 hour!\n\n"
                    f"🗓️ *Date:* {row['Date']}\n"
                    f"🕒 *Time:* {row['Time']}\n"
                    f"📚 *Subject:* {row['Subject']}"
                )
                
                try:
                    await app.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode="Markdown"
                    )
                    print(f"✅ Sent reminder to user {user_id} for lesson at {row['Time']}")
                except Exception as e:
                    print(f"❌ Failed to send reminder to user {user_id}: {e}")
                    
        except ValueError as e:
            print(f"⚠️ Invalid date/time format in row: {e}")
            continue

def run_schedule(app: Application):
    """Run the reminder schedule using a thread-based scheduler."""
    def loop():
        while True:
            schedule.run_pending()
            time.sleep(1)

    def task():
        schedule.every(1).minutes.do(lambda: asyncio.run(send_reminders(app)))
        threading.Thread(target=loop, daemon=True).start()

    print("📅 Reminder scheduler started.")
    task() 