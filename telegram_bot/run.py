"""
Launcher script for the Telegram bot.
"""

import asyncio
from telegram_bot.main import main

if __name__ == "__main__":
    app = main()
    asyncio.run(app.run_polling()) 