"""
Reschedule functionality for lessons.
"""

from datetime import datetime
from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from telegram_bot.sheets.google import connect_to_sheet

# Conversation states
RESCHEDULE_SELECT = range(1)

# Store slots in memory during selection
user_slot_options = {}

async def reschedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start lesson rescheduling process."""
    user_id = str(update.effective_user.id)
    sheets = connect_to_sheet()
    slots_sheet = sheets["slots"]
    schedule_sheet = sheets["schedule"]

    # Get next lesson
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
            except ValueError:
                continue

    if not upcoming_lesson_row:
        await update.message.reply_text(
            "❌ You don't have any upcoming lessons to reschedule."
        )
        return ConversationHandler.END

    # Get available slots
    slots_data = slots_sheet.get_all_records()
    available = []
    for slot in slots_data:
        if slot["Booked"].strip().upper() != "TRUE":
            try:
                dt = datetime.strptime(f"{slot['Date']} {slot['Time']}", "%d.%m.%Y %H:%M")
                if dt > now:
                    available.append(slot)
            except ValueError:
                continue

    if not available:
        await update.message.reply_text("📭 No available time slots right now.")
        return ConversationHandler.END

    # Show top 5 slots
    top_slots = available[:5]
    user_slot_options[user_id] = top_slots

    message = "🕒 Choose a new time slot by number:\n\n"
    for i, slot in enumerate(top_slots, start=1):
        message += f"{i}. {slot['Date']} at {slot['Time']}\n"

    await update.message.reply_text(message)
    return RESCHEDULE_SELECT


async def reschedule_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle time slot selection for rescheduling."""
    user_id = str(update.effective_user.id)
    user_input = update.message.text.strip()

    if user_id not in user_slot_options:
        await update.message.reply_text("⚠️ Session expired. Please try /reschedule again.")
        return ConversationHandler.END

    try:
        choice = int(user_input)
        selected_slot = user_slot_options[user_id][choice - 1]
    except (ValueError, IndexError):
        await update.message.reply_text("⚠️ Invalid choice. Please select a number from the list.")
        return RESCHEDULE_SELECT

    sheets = connect_to_sheet()
    slots_sheet = sheets["slots"]
    schedule_sheet = sheets["schedule"]

    # 1. Delete old lesson
    data = schedule_sheet.get_all_records()
    old_date = old_time = old_comment = ""

    for index, row in enumerate(data, start=2):
        if str(row["Telegram_ID"]) == user_id:
            try:
                dt = datetime.strptime(f"{row['Date']} {row['Time']}", "%d.%m.%Y %H:%M")
                if dt > datetime.now():
                    old_date = row["Date"]
                    old_time = row["Time"]
                    old_comment = row.get("Comments", "").strip() or ""
                    schedule_sheet.delete_rows(index)
                    break
            except ValueError:
                continue

    # 2. Add new lesson to schedule
    user = update.effective_user
    reschedule_note = f"Rescheduled from {old_date} at {old_time}"
    combined_comment = (
        f"{old_comment} | {reschedule_note}" if old_comment else reschedule_note
    )

    # Find first empty row
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
                combined_comment,
                "Online",
                "",
            ]
        ],
    )

    # 3. Update slot as booked
    slots_data = slots_sheet.get_all_records()
    for index, slot in enumerate(slots_data, start=2):
        if (
            slot["Date"] == selected_slot["Date"]
            and slot["Time"] == selected_slot["Time"]
        ):
            slots_sheet.update(f"C{index}", "TRUE")  # Booked
            slots_sheet.update(f"D{index}", user.first_name)  # Student
            slots_sheet.update(f"E{index}", user_id)  # Telegram ID
            break

    await update.message.reply_text(
        f"✅ Your lesson was rescheduled to:\n🗓️ {selected_slot['Date']} ⏰ {selected_slot['Time']}"
    )

    user_slot_options.pop(user_id, None)
    return ConversationHandler.END 