# English Lesson Scheduling Telegram Bot

A Telegram bot for scheduling and managing English lessons. The bot allows users to view upcoming lessons, reschedule, cancel, and check their profiles.

## Project Structure

```
telegram_bot/
│
├── main.py                  # entry point, bot initialization
├── run.py                   # launcher script
├── bot/
│   ├── __init__.py
│   ├── handlers.py          # /start, /nextlesson, /cancel, /profile, log_message
│   ├── reschedule.py        # reschedule and reschedule_select functions
│   ├── reminders.py         # send_reminders and run_schedule functions
│   └── utils.py             # save_user_to_users_sheet function
├── sheets/
│   ├── __init__.py
│   └── google.py            # connect_to_sheet function
└── requirements.txt
```

## Setup

1. Create a `.env` file in the project root with your Telegram bot token:
   ```
   BOT_TOKEN=your_telegram_bot_token
   ```

2. Place your Google Sheets `credentials.json` file in the project root.

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Run the bot:
   ```
   python -m telegram_bot.run
   ```

## Features

- `/start` - Welcome message and bot introduction
- `/nextlesson` - Show upcoming lesson details
- `/cancel` - Cancel the next scheduled lesson
- `/reschedule` - Reschedule a lesson to a different time slot
- `/profile` - View user profile information

## Google Sheets Integration

The bot connects to Google Sheets to store and retrieve:
- User information
- Lesson schedules
- Available time slots

## Reminder System

The bot automatically sends reminders to users one hour before their scheduled lessons. 