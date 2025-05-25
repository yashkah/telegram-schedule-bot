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
        users_sheet.append_row([name, username, telegram_id, timestamp, "", "", ""])
        print(f"✅ New user saved: {name} (ID: {telegram_id})")
    else:
        print(f"👀 User already exists: {telegram_id}")


# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "👋 *Hello! I'm your personal lesson assistant bot!*\n\n"
        "Here’s what I can do for you:\n"
        "▫️ /nextlesson — Show your upcoming lesson\n"
        "▫️ /cancel — Cancel your next class\n"
        "▫️ /reschedule — Reschedule your class to a different time\n"
        "▫️ /profile — View your profile info\n"
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

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    now = datetime.now()

    sheets = connect_to_sheet()
    schedule_sheet = sheets["schedule"]
    data = schedule_sheet.get_all_records()

    for index, row in enumerate(data, start=2):  # начинаем с 2, т.к. первая строка — заголовок
        if str(row["Telegram_ID"]) == user_id:
            try:
                dt = datetime.strptime(f"{row['Date']} {row['Time']}", "%d.%m.%Y %H:%M")
            except:
                continue

            if dt > now:
                # Удаляем строку в Google Sheets
                schedule_sheet.delete_rows(index)
                await update.message.reply_text(
                    f"❌ Your lesson on {row['Date']} at {row['Time']} has been *cancelled*.",
                    parse_mode='Markdown'
                )
                return

    await update.message.reply_text("📭 You don’t have any upcoming lessons to cancel.")

from telegram.ext import ConversationHandler, MessageHandler, filters

RESCHEDULE_SELECT = range(1)

# Сохраняем слоты в память на время выбора
user_slot_options = {}

async def reschedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    sheets = connect_to_sheet()
    slots_sheet = sheets["slots"]
    schedule_sheet = sheets["schedule"]

    # Получаем ближайший урок
    data = schedule_sheet.get_all_records()
    now = datetime.now()
    upcoming_lesson_row = None
    for index, row in enumerate(data, start=2):
        if str(row["Telegram_ID"]) == user_id:
            try:
                dt = datetime.strptime(f"{row['Date']} {row['Time']}", "%d.%m.%Y %H:%M")
                if dt > now:
                    upcoming_lesson_row = (index, row)
                    break
            except:
                continue

    if not upcoming_lesson_row:
        await update.message.reply_text("❌ You don’t have any upcoming lessons to reschedule.")
        return ConversationHandler.END

    # Получаем свободные слоты
    slots_data = slots_sheet.get_all_records()
    available = []
    for slot in slots_data:
        if slot["Booked"].strip().upper() != "TRUE":
            try:
                dt = datetime.strptime(f"{slot['Date']} {slot['Time']}", "%d.%m.%Y %H:%M")
                if dt > now:
                    available.append(slot)
            except:
                continue

    if not available:
        await update.message.reply_text("📭 No available time slots right now.")
        return ConversationHandler.END

    # Показываем 5 первых слотов
    top_slots = available[:5]
    user_slot_options[user_id] = top_slots  # сохраняем для обработки выбора

    message = "🕒 Choose a new time slot by number:\n\n"
    for i, slot in enumerate(top_slots, start=1):
        message += f"{i}. {slot['Date']} at {slot['Time']}\n"

    await update.message.reply_text(message)
    return RESCHEDULE_SELECT


async def reschedule_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_input = update.message.text.strip()

    if user_id not in user_slot_options:
        await update.message.reply_text("⚠️ Session expired. Please try /reschedule again.")
        return ConversationHandler.END

    try:
        choice = int(user_input)
        selected_slot = user_slot_options[user_id][choice - 1]
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid choice. Please enter a number from the list.")
        return RESCHEDULE_SELECT

    sheets = connect_to_sheet()
    slots_sheet = sheets["slots"]
    schedule_sheet = sheets["schedule"]

    # 1. Удаляем старый урок
    data = schedule_sheet.get_all_records()
    for index, row in enumerate(data, start=2):
        if str(row["Telegram_ID"]) == user_id:
            try:
                dt = datetime.strptime(f"{row['Date']} {row['Time']}", "%d.%m.%Y %H:%M")
                if dt > datetime.now():
                    schedule_sheet.delete_rows(index)
                    break
            except:
                continue

    # 2. Добавляем новый урок в расписание
    user = update.effective_user
    schedule_sheet.append_row([
        user.first_name,
        selected_slot["Date"],
        selected_slot["Time"],
        "Rescheduled",
        "",  # Subject (можно позже уточнить)
        "",  # Comments
        "",  # Homework
        selected_slot["Date"],  # Day (можно переписать)
        user_id
    ])

    # 3. Обновляем слот как забронированный
    slots_data = slots_sheet.get_all_records()
    for index, slot in enumerate(slots_data, start=2):
        if slot["Date"] == selected_slot["Date"] and slot["Time"] == selected_slot["Time"]:
            slots_sheet.update(f"C{index}", "TRUE")  # Booked
            slots_sheet.update(f"D{index}", user.first_name)  # Student
            slots_sheet.update(f"E{index}", user_id)  # Telegram_ID
            break

    await update.message.reply_text(
        f"✅ Your lesson was rescheduled to:\n🗓️ {selected_slot['Date']} ⏰ {selected_slot['Time']}"
    )

    user_slot_options.pop(user_id, None)  # очистка
    return ConversationHandler.END


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    sheets = connect_to_sheet()
    users_sheet = sheets["users"]
    data = users_sheet.get_all_records()

    for row in data:
        if str(row["Telegram ID"]) == user_id:
            level = row.get("Level", "Not set")
            experience = row.get("Experience", "Not set")
            goal = row.get("Goal", "Not set")

            message = (
                f"👤 *Your Profile:*\n\n"
                f"📛 Name: {row['Name']}\n"
                f"💬 Username: @{row['Username']}\n"
                f"🆔 Telegram ID: {row['Telegram ID']}\n"
                f"🧠 Level: {level}\n"
                f"📈 Experience: {experience}\n"
                f"🎯 Goal: {goal}\n"
                f"🕒 Register Date: {row['Log Date']}"
            )
            await update.message.reply_text(message, parse_mode='Markdown')
            return

    await update.message.reply_text("❌ Profile not found. Please try again later.")


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
app.add_handler(CommandHandler("profile", profile))
app.add_handler(CommandHandler("cancel", cancel))
app.add_handler(ConversationHandler(
    entry_points=[CommandHandler("reschedule", reschedule)],
    states={RESCHEDULE_SELECT: [MessageHandler(filters.TEXT & (~filters.COMMAND), reschedule_select)]},
    fallbacks=[]
))


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
