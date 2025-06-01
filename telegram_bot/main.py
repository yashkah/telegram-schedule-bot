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
    app_builder = ApplicationBuilder().token(TOKEN).build()
    
    # Register command handlers
    app_builder.add_handler(CommandHandler("start", start))
    app_builder.add_handler(CommandHandler("nextlesson", nextlesson))
    app_builder.add_handler(CommandHandler("profile", profile))
    app_builder.add_handler(CommandHandler("cancel", cancel))
    
    # Register conversation handler for reschedule
    app_builder.add_handler(
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
    
    # Register message handler
    app_builder.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), log_message))
    
    # Start reminders
    run_schedule(app_builder)
    
    print("Bot is starting...")
    
    # Run the bot
    nest_asyncio.apply()
    return app_builder

if __name__ == "__main__":
    app = main()
    asyncio.get_event_loop().run_until_complete(app.run_polling()) 