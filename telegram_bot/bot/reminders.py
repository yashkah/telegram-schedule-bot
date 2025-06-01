"""
Reminder functionality for scheduled lessons.
"""

import asyncio
import schedule
import threading
import time
from datetime import datetime, timedelta
import pytz

from telegram_bot.sheets.google import connect_to_sheet

# Store already notified lessons
already_notified = set()

async def send_reminders(application):
    """Send lesson reminders to users."""
    now = datetime.now(pytz.timezone('Europe/Moscow'))
    print(f"\n🔄 Running reminder check at {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    try:
        sheets = connect_to_sheet()
        schedule_sheet = sheets["schedule"]
        data = schedule_sheet.get_all_records()
        print(f"📊 Found {len(data)} total lessons in schedule")
    except Exception as e:
        print(f"❌ Failed to connect to Google Sheets: {e}")
        return

    REMINDER_BEFORE_MINUTES = 60

    # Add a test lesson 62 minutes from now for validation
    test_time = now + timedelta(minutes=62)
    test_lesson = {
        "Student": "TEST_USER",
        "Telegram_ID": "6878992518",  # Your admin ID
        "Date": test_time.strftime("%d.%m.%Y"),
        "Time": test_time.strftime("%H:%M"),
        "Day": test_time.strftime("%A"),
        "Subject": "TEST LESSON",
    }
    data.append(test_lesson)
    print("🧪 Added test lesson for validation")

    for row in data:
        try:
            student = row.get('Student', 'Unknown')
            telegram_id = row.get('Telegram_ID', 'Unknown')
            date = row.get('Date', '')
            time = row.get('Time', '')
            
            print(f"\n👤 Checking lesson for: {student} (ID: {telegram_id})")
            print(f"📅 Lesson date/time: {date} {time}")
            
            lesson_key = f"{telegram_id}_{date}_{time}"
            
            if lesson_key in already_notified:
                print(f"⚠️ Already notified for lesson: {lesson_key}")
                continue

            try:
                dt = datetime.strptime(f"{date} {time}", "%d.%m.%Y %H:%M")
                dt = pytz.timezone('Europe/Moscow').localize(dt)
                print(f"✅ Successfully parsed datetime: {dt}")
            except ValueError as e:
                print(f"❌ Failed to parse datetime: {e}")
                continue

            if dt < now:
                print("⏭️ Lesson is in the past, skipping")
                continue

            time_diff = (dt - now).total_seconds() / 60
            print(f"⏳ Time until lesson: {time_diff:.2f} minutes")

            # Check if lesson is within the reminder window
            if REMINDER_BEFORE_MINUTES - 0.5 <= time_diff <= REMINDER_BEFORE_MINUTES + 0.5:
                print(f"🎯 Lesson matches reminder window!")
                user_id = int(telegram_id)
                message = (
                    f"⏰ Reminder: Your lesson starts in 1 hour!\n\n"
                    f"📅 Date: {row.get('Day', '')}, {date}\n"
                    f"⏰ Time: {time}\n"
                    f"📚 Subject: {row.get('Subject', 'English')}"
                )

                try:
                    await application.bot.send_message(chat_id=user_id, text=message)
                    already_notified.add(lesson_key)
                    print(f"✅ Successfully sent reminder to {student}")
                except Exception as e:
                    print(f"❌ Failed to send message to {user_id}: {e}")
            else:
                print("⏭️ Lesson not in reminder window, skipping")

        except Exception as e:
            print(f"❌ Error processing row: {e}")
            continue

def run_schedule(application):
    """Run scheduled reminder checks."""
    print("🚀 Starting reminder scheduler...")

    async def task():
        await send_reminders(application)

    def loop():
        print("⚡ Reminder thread started")
        schedule.every(1).minutes.do(lambda: asyncio.run(task()))
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                print(f"❌ Error in reminder loop: {e}")
                time.sleep(5)  # Wait before retrying

    thread = threading.Thread(target=loop)
    thread.daemon = True
    thread.start()
    print("✅ Reminder scheduler is running") 