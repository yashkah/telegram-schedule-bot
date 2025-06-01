"""
Command handlers for the Telegram bot.
"""

from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.sheets.google import connect_to_sheet
from telegram_bot.bot.utils import save_user_to_users_sheet, notify_admin_command_usage

# Admin Telegram ID
ADMIN_ID = 6878992518


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await notify_admin_command_usage(context, update, "start")
    welcome_message = (
        "👋 *Hello! I'm your personal lesson assistant bot!*\n\n"
        "Here's what I can do for you:\n"
        "▫️ /nextlesson — Show your upcoming lesson\n"
        "▫️ /cancel — Cancel your next class\n"
        "▫️ /reschedule — Reschedule your class to a different time\n"
        "▫️ /book — Book a new lesson\n"
        "▫️ /profile — View your profile info\n"
        "💡 Just type one of the commands above or send me a message to interact!"
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown")


async def nextlesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's next lesson."""
    await notify_admin_command_usage(context, update, "nextlesson")
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
                except ValueError:
                    continue

            if dt > now:
                lesson_type = row.get("Type") or row.get(" Type") or "Not set"
                comment = row.get("Comments") or row.get(" Comments") or "No comment"

                message = (
                    f"📅 *Your Next Lesson:*\n\n"
                    f"🗓️ *Date:* {row['Day']}, {row['Date']}\n"
                    f"⏰ *Time:* {row['Time']}\n"
                    f"📚 *Subject:* {row['Subject']}\n"
                    f"🧑‍💻 *Type:* {lesson_type}\n"
                    f"📝 *Comment:* {comment}"
                )

                await update.message.reply_text(message, parse_mode="Markdown")
                return

    await update.message.reply_text("You don't have any upcoming lessons 🤷")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel user's next scheduled lesson."""
    await notify_admin_command_usage(context, update, "cancel")
    user_id = str(update.effective_user.id)
    now = datetime.now()

    sheets = connect_to_sheet()
    schedule_sheet = sheets["schedule"]
    data = schedule_sheet.get_all_records()

    for index, row in enumerate(data, start=2):
        if str(row["Telegram_ID"]) == user_id:
            try:
                dt = datetime.strptime(f"{row['Date']} {row['Time']}", "%d.%m.%Y %H:%M")
            except ValueError:
                continue

            if dt > now:
                schedule_sheet.delete_rows(index)
                message = (
                    f"❌ *Lesson Cancelled:*\n\n"
                    f"🗓️ *Date:* {row['Date']}\n"
                    f"⏰ *Time:* {row['Time']}"
                )
                await update.message.reply_text(message, parse_mode="Markdown")

                return

    await update.message.reply_text("📭 You don't have any upcoming lessons to cancel.")


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile information."""
    await notify_admin_command_usage(context, update, "profile")
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
                f"📛 *Name:* {row['Name']}\n"
                f"💬 *Username:* @{row['Username']}\n"
                f"🆔 *Telegram ID:* {row['Telegram ID']}\n"
                f"🧠 *Level:* {level}\n"
                f"📈 *Experience:* {experience}\n"
                f"🎯 *Goal:* {goal}\n"
                f"🕒 *Register Date:* {row['Log Date']}"
            )
            await update.message.reply_text(message, parse_mode="Markdown")
            return

    await update.message.reply_text("❌ Profile not found. Please try again later.")


async def log_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log user messages and save new users."""
    # No need to notify for regular messages
    user = update.effective_user
    message = update.message.text

    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = user.username or "-"
    user_id = user.id
    timestamp = datetime.now().strftime("%Y.%m.%d")

    print(f"💬 Message from {name} (@{username}, ID: {user_id}) at {timestamp}: {message}")
    save_user_to_users_sheet(name, username, user_id, timestamp) 