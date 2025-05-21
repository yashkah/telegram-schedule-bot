import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext

# Import our modules
import calendar_service
import utils

# Constants
TOKEN = "7840640138:AAGuY61G9cZ6MeTuPinIIy0DNyqzvZntTYs"
CALENDAR_CHECK_INTERVAL = 300  # 5 minutes
REMINDER_TIME = 30  # minutes before class
TIMEZONE = "Europe/Moscow"  # Adjust to your timezone

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot")
    
    # Store user in students list if not already present
    students = utils.load_students()
    if str(user.id) not in students:
        if user.username:
            students[str(user.id)] = f"@{user.username}"
        else:
            students[str(user.id)] = f"{user.first_name} {user.last_name or ''}"
        utils.save_students(students)
    
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋 Я бот-помощник, который будет напоминать "
        f"тебе о предстоящих занятиях. Используй /my_schedule, чтобы узнать свое расписание."
    )

async def my_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's upcoming schedule."""
    user = update.effective_user
    logger.info(f"User {user.id} requested schedule")
    
    # Get user identifier from our database
    students = utils.load_students()
    user_identifier = students.get(str(user.id))
    
    if not user_identifier:
        await update.message.reply_text("Извините, я не могу найти вас в базе данных студентов.")
        return
    
    # Get upcoming events for this user
    upcoming_events = await get_upcoming_events(user_identifier)
    
    if not upcoming_events:
        await update.message.reply_text("У вас нет предстоящих занятий на ближайшее время.")
        return
    
    # Format and send the schedule
    response = utils.format_schedule_message(upcoming_events)
    await update.message.reply_text(response)

# Calendar integration
async def get_upcoming_events(user_identifier: str) -> List[Dict[str, Any]]:
    """Get upcoming events for a specific user from Google Calendar."""
    # Get events for this user from the calendar service
    try:
        # Get events for next 7 days by default
        now = datetime.now()
        return await calendar_service.get_events_for_user(
            user_identifier=user_identifier,
            time_min=now,
            time_max=now + timedelta(days=7)
        )
    except Exception as e:
        logger.error(f"Error getting events for user {user_identifier}: {e}")
        # Fallback to mock data for demonstration or during development
        mock_events = [
            {
                "title": "Python Programming Basics",
                "start_time": datetime.now() + timedelta(hours=2),
                "description": "Introduction to variables and data types"
            },
            {
                "title": "Advanced Python Concepts",
                "start_time": datetime.now() + timedelta(days=1),
                "description": "Classes and Object-Oriented Programming"
            }
        ]
        return mock_events

async def check_calendar_and_send_reminders(application: Application) -> None:
    """Check the calendar for upcoming lessons and send reminders."""
    logger.info("Checking calendar for upcoming lessons...")
    
    # Get all students
    students = utils.load_students()
    
    # For each student, check upcoming events
    for user_id, user_identifier in students.items():
        events = await get_upcoming_events(user_identifier)
        
        # Filter events that start within the reminder time
        now = datetime.now()
        reminder_events = [
            event for event in events
            if now <= event["start_time"] <= now + timedelta(minutes=REMINDER_TIME) and 
               event.get("id") and not utils.was_reminder_sent(event["id"])
        ]
        
        # Send reminder for each event
        for event in reminder_events:
            try:
                await send_reminder(application, user_id, event)
                logger.info(f"Sent reminder to user {user_id} for event {event['title']}")
                
                # Mark reminder as sent
                if event.get("id"):
                    utils.add_sent_reminder(event["id"])
            except Exception as e:
                logger.error(f"Failed to send reminder to user {user_id}: {e}")

async def send_reminder(application: Application, user_id: str, event: Dict[str, Any]) -> None:
    """Send a reminder to a user about an upcoming event."""
    start_time = event["start_time"]
    time_until = utils.format_time_until(start_time)
    
    message = (
        f"🔔 Напоминание о занятии!\n\n"
        f"📚 {event['title']}\n"
        f"🕒 Начало через {time_until} "
        f"({start_time.strftime('%H:%M')})\n"
    )
    
    if event.get("description"):
        description = event.get("description", "")
        if len(description) > 100:
            description = description[:97] + "..."
        message += f"📝 {description}\n"
    
    await application.bot.send_message(chat_id=user_id, text=message)

# Calendar checker task
async def calendar_checker(application: Application) -> None:
    """Periodic task to check calendar and send reminders."""
    while True:
        try:
            await check_calendar_and_send_reminders(application)
        except Exception as e:
            logger.error(f"Error in calendar checker: {e}")
        
        await asyncio.sleep(CALENDAR_CHECK_INTERVAL)

async def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("my_schedule", my_schedule))

    # Start the Bot
    await application.initialize()
    await application.start()
    
    logger.info("Bot started successfully!")
    
    # Start calendar checking task
    asyncio.create_task(calendar_checker(application))
    
    # Run the bot until the user presses Ctrl-C
    await asyncio.Event().wait()

if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
