from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from sheets import connect_to_sheet
from datetime import datetime
import asyncio

from flask import Flask
import threading

# Фейковый веб-сервер для Render
fake_app = Flask(__name__)

@fake_app.route('/')
def home():
    return "Bot is running!"


# Запускаем Flask в отдельном потоке
def run_flask():
    import os
    port = int(os.environ.get("PORT", 10000))  # Render сам подставит переменную PORT
    fake_app.run(host="0.0.0.0", port=port)

# Запуск потока Flask
threading.Thread(target=run_flask).start()


already_notified = set()

# Connect to Google Sheet
sheet = connect_to_sheet()

def save_user_to_users_sheet(name, username, telegram_id, timestamp):
    sheets = connect_to_sheet()
    users_sheet = sheets["users"]
    data = users_sheet.get_all_records()

    existing_ids = [str(row["Telegram ID"]) for row in data]

    if str(telegram_id) not in existing_ids:
        users_sheet.append_row([name, username, telegram_id, timestamp])
        print(f"✅ New user saved: {name} (ID: {telegram_id})")
    else:
        print(f"👀 User already exists: {telegram_id}")


# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "👋 *Hello! I'm your personal lesson assistant bot!*\n\n"
        "Here’s what I can do for you:\n"
        "▫️ /nextlesson — Show your upcoming lesson\n"
        "▫️ /cancel — Cancel your next class (coming soon)\n"
        "▫️ /reschedule — Reschedule your class (coming soon)\n"
        "▫️ /profile — View your profile info (coming soon)\n\n"
        "💡 Just type one of the commands above or send me a message to interact!"
    )
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


# /nextlesson command
async def nextlesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    now = datetime.now()

    sheets = connect_to_sheet()
    schedule_sheet = sheets["schedule"]
    data = schedule_sheet.get_all_records()

    for row in data:
        if str(row["Telegram_ID"]) == user_id:
            try:
                dt = datetime.strptime(f"{row['Date']} {row['Time']}", "%d.%m.%Y %H:%M:%S")
            except ValueError:
                try:
                    dt = datetime.strptime(f"{row['Date']} {row['Time']}", "%d.%m.%Y %H:%M")
                except:
                    continue

            if dt > now:
                message = (
                     f"📅 Your next lesson:\n\n"
                     f"🗓️ Date: {row['Day']}, {row['Date']}\n"
                     f"⏰ Time: {row['Time']}\n"
                     f"📚 Subject: {row['Subject']}"
                )
                await update.message.reply_text(message)
                return

    await update.message.reply_text("You don't have any upcoming lessons 🤷")


# BotFather token here
import os

# Try to load from dotenv if available, otherwise use os.environ directly
try:
    from dotenv import load_dotenv
    load_dotenv()
    TOKEN = os.getenv("BOT_TOKEN")
except ImportError:
    # If dotenv is not available, use os.environ directly
    TOKEN = os.environ["BOT_TOKEN"]


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("nextlesson", nextlesson))

from telegram.ext import MessageHandler, filters

async def log_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message.text

    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = user.username or "-"
    user_id = user.id
    timestamp = datetime.now().strftime("%Y.%m.%d")  

    print(f"💬 Message from {name} (@{username}, ID: {user_id}) at {timestamp}: {message}")

    save_user_to_users_sheet(name, username, user_id, timestamp)

app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), log_message))

import schedule
import time
import threading

async def send_reminders(application):
    now = datetime.now()
    sheets = connect_to_sheet()
    schedule_sheet = sheets["schedule"]
    data = schedule_sheet.get_all_records()


    for row in data:
        print(f"🧪 Checking row for student: {row['Student']} | Date: {row['Date']} | Time: {row['Time']}")
        lesson_key = f"{row['Telegram_ID']}_{row['Date']}_{row['Time']}"

        if lesson_key in already_notified:
            print(f"⚠️ Already notified for: {lesson_key}")
            continue
        try:
            dt = datetime.strptime(f"{row['Date']} {row['Time']}", "%d.%m.%Y %H:%M")
            if dt < now:
                continue

        except:
            print("⚠️ Could not parse datetime.")
            continue

        time_diff = (dt - now).total_seconds() / 60
        print(f"⏳ Time diff with now: {time_diff:.2f} minutes")

        REMINDER_BEFORE_MINUTES = 60

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

import nest_asyncio
nest_asyncio.apply()

print("Bot is starting...")

# Запускаем напоминания
run_schedule(app)

# Запускаем Telegram-бота
async def run_bot():
    await app.run_polling()

asyncio.get_event_loop().run_until_complete(run_bot())
