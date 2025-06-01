"""
Reminder functionality for English lessons.
"""

import asyncio
import schedule
import threading
import time
from datetime import datetime, timedelta
import pytz
from dateutil import parser
from telegram.ext import Application

from telegram_bot.sheets.google import connect_to_sheet

async def send_reminders(app: Application):
    """Send reminders for upcoming lessons."""
    print("🔔 Checking for lessons to remind...")
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    sheets = connect_to_sheet()
    schedule_sheet = sheets["schedule"]
    data = schedule_sheet.get_all_records()

    required_fields = ["Date", "Time", "Student", "Subject", "Duration", "Telegram_ID"]
    last_error = None
    error_count = 0

    for row in data:
        # Validation: skip if any required field is missing or empty
        if not all(str(row.get(field, "")).strip() for field in required_fields):
            print(f"⚠️ Skipping lesson with missing fields: {row}")
            continue

        date = row.get("Date", "").strip()
        time_ = row.get("Time", "").strip()
        if date and time_:
            try:
                lesson_datetime = parser.parse(f"{date} {time_}", dayfirst=True)
                lesson_datetime = pytz.timezone('Europe/Warsaw').localize(lesson_datetime)
            except (ValueError, TypeError) as e:
                error_msg = f"⚠️ Could not parse date/time: '{date} {time_}' — {e}"
                if error_msg == last_error:
                    error_count += 1
                else:
                    if error_count > 1:
                        print(f"(Previous error repeated {error_count} times)")
                    print(error_msg)
                    last_error = error_msg
                    error_count = 1
                continue
        else:
            print(f"⚠️ Missing date or time in row: Date='{date}' Time='{time_}'")
            continue

        # Check if lesson is in 1 hour
        if now + timedelta(hours=1) <= lesson_datetime < now + timedelta(hours=1, minutes=5):
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

# def run_schedule(app: Application):
#     """Run the reminder schedule using a thread-based scheduler."""
#     def loop():
#         while True:
#             schedule.run_pending()
#             time.sleep(1)
#
#     def task():
#         schedule.every(1).minutes.do(lambda: asyncio.run(send_reminders(app)))
#         threading.Thread(target=loop, daemon=True).start()
#
#     print("📅 Reminder scheduler started.")
#     task() 