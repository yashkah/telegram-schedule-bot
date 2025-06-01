"""
Booking functionality for English lessons.
"""

from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from telegram_bot.sheets.google import connect_to_sheet
from telegram_bot.bot.sync import sync_schedule_with_slots
from telegram_bot.bot.utils import notify_admin_command_usage

# Conversation states
SELECT_SLOT = range(1)

# Store booking options in memory during selection
user_booking_options = {}

async def book_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the lesson booking process."""
    await notify_admin_command_usage(context, update, "book")
    user_id = str(update.effective_user.id)
    now = datetime.now(pytz.timezone('Europe/Moscow'))
    
    # Sync schedule with slots first
    try:
        sync_schedule_with_slots()
        print(f"✅ Synced schedule with slots for user {user_id}")
    except Exception as e:
        print(f"❌ Failed to sync schedule: {e}")
        await update.message.reply_text(
            "❌ Sorry, there was an error preparing the booking system. Please try again later."
        )
        return ConversationHandler.END

    # Check if user already has a future lesson
    sheets = connect_to_sheet()
    schedule_sheet = sheets["schedule"]
    data = schedule_sheet.get_all_records()

    for row in data:
        if str(row["Telegram_ID"]) == user_id:
            try:
                dt = datetime.strptime(f"{row['Date']} {row['Time']}", "%d.%m.%Y %H:%M")
                dt = pytz.timezone('Europe/Moscow').localize(dt)
                if dt > now:
                    await update.message.reply_text(
                        "❌ You already have an upcoming lesson. Please use /reschedule if you want to change it."
                    )
                    return ConversationHandler.END
            except ValueError:
                continue

    # Get available slots
    slots_sheet = sheets["slots"]
    slots_data = slots_sheet.get_all_records()
    available = []

    for slot in slots_data:
        if slot["Booked"].strip().upper() != "TRUE":
            try:
                dt = datetime.strptime(f"{slot['Date']} {slot['Time']}", "%d.%m.%Y %H:%M")
                dt = pytz.timezone('Europe/Moscow').localize(dt)
                if dt > now:
                    available.append(slot)
            except ValueError:
                continue

    if not available:
        await update.message.reply_text("📭 No available time slots right now.")
        return ConversationHandler.END

    # Show top 5 slots
    top_slots = available[:5]
    user_booking_options[user_id] = top_slots

    message = "🕒 Choose a time slot by number:\n\n"
    for i, slot in enumerate(top_slots, start=1):
        message += f"{i}. {slot['Date']} at {slot['Time']}\n"

    await update.message.reply_text(message)
    return SELECT_SLOT


async def select_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle time slot selection for booking."""
    # No need to notify for slot selection as it's part of the booking process
    user_id = str(update.effective_user.id)
    user_input = update.message.text.strip()

    if user_id not in user_booking_options:
        await update.message.reply_text("⚠️ Session expired. Please try /book again.")
        return ConversationHandler.END

    try:
        choice = int(user_input)
        selected_slot = user_booking_options[user_id][choice - 1]
    except (ValueError, IndexError):
        await update.message.reply_text("⚠️ Invalid choice. Please select a number from the list.")
        return SELECT_SLOT

    # Verify slot is still available
    sheets = connect_to_sheet()
    slots_sheet = sheets["slots"]
    schedule_sheet = sheets["schedule"]
    
    slots_data = slots_sheet.get_all_records()
    slot_found = False
    slot_index = None

    for index, slot in enumerate(slots_data, start=2):
        if (
            slot["Date"] == selected_slot["Date"]
            and slot["Time"] == selected_slot["Time"]
        ):
            if slot["Booked"].strip().upper() == "TRUE":
                await update.message.reply_text(
                    "❌ This slot was just booked by someone else. Please try another slot."
                )
                return SELECT_SLOT
            slot_found = True
            slot_index = index
            break

    if not slot_found:
        await update.message.reply_text("❌ This slot is no longer available. Please try /book again.")
        return ConversationHandler.END

    # Add new lesson to schedule
    user = update.effective_user
    next_row = len(schedule_sheet.get_all_values()) + 1

    # Insert data into specific cells
    schedule_sheet.update(
        f"A{next_row}:K{next_row}",
        [
            [
                selected_slot["Date"],
                datetime.strptime(selected_slot["Date"], "%d.%m.%Y").strftime("%A"),
                selected_slot["Time"],
                user.first_name,
                "English",
                "60",
                user_id,
                "",
                "",
                "Online",
                "",
            ]
        ],
    )

    # Update slot as booked
    slots_sheet.update(f"C{slot_index}", "TRUE")  # Booked
    slots_sheet.update(f"D{slot_index}", user.first_name)  # Student
    slots_sheet.update(f"E{slot_index}", user_id)  # Telegram ID

    await update.message.reply_text(
        f"✅ Your lesson has been booked for:\n🗓️ {selected_slot['Date']} ⏰ {selected_slot['Time']}"
    )

    user_booking_options.pop(user_id, None)
    return ConversationHandler.END 