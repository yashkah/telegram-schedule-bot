"""
English lesson scheduling Telegram bot.
Handles lesson management and user notifications.
"""

import asyncio
import os
import threading
import nest_asyncio
from flask import Flask
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv

from telegram_bot.bot.handlers import (
    start,
    nextlesson,
    profile,
    cancel,
    log_message,
)
from telegram_bot.bot.reschedule import reschedule, reschedule_select, RESCHEDULE_SELECT
from telegram_bot.bot.book import book_class, select_slot, SELECT_SLOT
from telegram_bot.bot.reminders import run_schedule

# Flask server for Render hosting
app = Flask(__name__)

@app.route("/")
def home():
    """Handle root route."""
    return "Bot is running!"

def run_flask():
    """Run Flask server in separate thread."""
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Start Flask thread
threading.Thread(target=run_flask).start()

# Load environment variables
try:
    load_dotenv()
    TOKEN = os.getenv("BOT_TOKEN")
except ImportError:
    TOKEN = os.environ["BOT_TOKEN"]

def main():
    """Initialize and run the bot."""
    # Initialize the bot
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("nextlesson", nextlesson))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("cancel", cancel))
    
    # Register conversation handler for reschedule
    application.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("reschedule", reschedule)],
            states={
                RESCHEDULE_SELECT: [
                    MessageHandler(filters.TEXT & (~filters.COMMAND), reschedule_select)
                ]
            },
            fallbacks=[],
        )
    )
    
    # Register conversation handler for booking
    application.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("book", book_class)],
            states={
                SELECT_SLOT: [
                    MessageHandler(filters.TEXT & (~filters.COMMAND), select_slot)
                ]
            },
            fallbacks=[],
        )
    )
    
    # Register message handler
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), log_message))
    
    print("Bot is starting...")
    
    # Start reminders
    run_schedule(application)
    
    # Run the bot
    nest_asyncio.apply()
    return application

if __name__ == "__main__":
    app = main()
    asyncio.get_event_loop().run_until_complete(app.run_polling()) 