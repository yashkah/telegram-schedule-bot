"""
Reminder functionality for scheduled lessons.
"""

import asyncio
import schedule
import threading
import time
from datetime import datetime

from telegram_bot.sheets.google import connect_to_sheet

# Store already notified lessons
already_notified = set()

async def send_reminders(application):
    """Send lesson reminders to users."""
    now = datetime.now()
    sheets = connect_to_sheet()
    schedule_sheet = sheets["schedule"]
    data = schedule_sheet.get_all_records()

    REMINDER_BEFORE_MINUTES = 60

    for row in data:
        print(
            f"🧪 Checking row for student: {row['Student']} | Date: {row['Date']} | Time: {row['Time']}"
        )
        lesson_key = f"{row['Telegram_ID']}_{row['Date']}_{row['Time']}"

        if lesson_key in already_notified:
            print(f"⚠️ Already notified for: {lesson_key}")
            continue

        try:
            dt = datetime.strptime(f"{row['Date']} {row['Time']}", "%d.%m.%Y %H:%M")
            if dt < now:
                continue
        except ValueError:
            print("⚠️ Could not parse datetime.")
            continue

        time_diff = (dt - now).total_seconds() / 60
        print(f"⏳ Time diff with now: {time_diff:.2f} minutes")

        if REMINDER_BEFORE_MINUTES - 0.5 <= time_diff <= REMINDER_BEFORE_MINUTES + 0.5:
            print(f"✅ Sending reminder to: {row['Student']}")
            user_id = int(row["Telegram_ID"])
            message = (
                f"⏰ Reminder: Your lesson starts in 1 hour!\n\n"
                f"📅 Date: {row['Day']}, {row['Date']}\n"
                f"⏰ Time: {row['Time']}\n"
                f"📚 Subject: {row['Subject']}"
            )

            try:
                await application.bot.send_message(chat_id=user_id, text=message)
                already_notified.add(lesson_key)
            except Exception as e:
                print(f"❌ Failed to send message to {user_id}: {e}")


def run_schedule(application):
    """Run scheduled reminder checks."""

    async def task():
        await send_reminders(application)

    def loop():
        schedule.every(1).minutes.do(lambda: asyncio.run(task()))
        while True:
            schedule.run_pending() 
            time.sleep(1)

    thread = threading.Thread(target=loop)
    thread.daemon = True
    thread.start() 