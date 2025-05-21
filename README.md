# Student Schedule Telegram Bot

A Telegram bot for managing student schedules and lesson reminders using Google Calendar integration.

## Features

- 🤖 Responds to `/start` with a greeting
- 📅 Shows upcoming lessons with `/my_schedule`
- ⏰ Sends automatic reminders 30 minutes before class
- 🔍 Matches students to calendar events using their Telegram username or full name
- 📊 Connects to Google Calendar for schedule management

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Google Calendar API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Calendar API for your project
4. Create OAuth 2.0 credentials (Desktop app)
5. Download the credentials JSON file and save it as `credentials.json` in the project root

### 3. Configure the Bot

The bot uses environment variables for configuration, which you can modify in the `.env` file:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from BotFather
- `CALENDAR_CHECK_INTERVAL`: How often to check the calendar (in seconds)
- `REMINDER_TIME`: How many minutes before class to send reminders
- `TIMEZONE`: Your local timezone

### 4. Running the Bot

```bash
python bot.py
```

The first time you run the bot, it will prompt you to authorize access to your Google Calendar.

## Usage

### Adding Students to the Bot

1. Students should start the bot by sending the `/start` command
2. The bot will automatically add them to the student database

### Creating Calendar Events

When creating events in Google Calendar, include student identifiers in one of these ways:

1. Add student's Telegram username as an attendee (e.g., `@username`)
2. Include the student's Telegram username in the event description with @ symbol
3. Add the student's full name as an attendee or in the description

### Available Commands

- `/start` - Initialize the bot
- `/my_schedule` - Show your upcoming lessons

## Extending the Bot

This bot provides a foundation that can be extended with additional features, such as:

- Homework submission and tracking
- Attendance tracking
- Direct messaging between teachers and students
- AI-powered tutoring or study assistance

## Architecture

The project follows a modular design:

- `bot.py`: Main bot logic and command handlers
- `calendar_service.py`: Google Calendar API integration
- `data/students.json`: Student database

## Troubleshooting

If you encounter issues connecting to Google Calendar, delete the `tokens/token.json` file and restart the bot to re-authenticate.

For any other issues, check the logs for error messages. 