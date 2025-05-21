import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Setup logging
logger = logging.getLogger(__name__)

# Data directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
STUDENTS_FILE = DATA_DIR / "students.json"
REMINDERS_FILE = DATA_DIR / "sent_reminders.json"

# Initialize files if they don't exist
if not STUDENTS_FILE.exists():
    with open(STUDENTS_FILE, "w") as f:
        json.dump({}, f)

if not REMINDERS_FILE.exists():
    with open(REMINDERS_FILE, "w") as f:
        json.dump([], f)

def load_students() -> Dict[str, str]:
    """Load student data from JSON file."""
    try:
        with open(STUDENTS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_students(students: Dict[str, str]) -> None:
    """Save student data to JSON file."""
    with open(STUDENTS_FILE, "w") as f:
        json.dump(students, f)

def load_sent_reminders() -> List[str]:
    """Load IDs of events for which reminders have been sent."""
    try:
        with open(REMINDERS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_sent_reminders(reminder_ids: List[str]) -> None:
    """Save IDs of events for which reminders have been sent."""
    with open(REMINDERS_FILE, "w") as f:
        json.dump(reminder_ids, f)

def add_sent_reminder(event_id: str) -> None:
    """Add an event ID to the list of sent reminders."""
    reminders = load_sent_reminders()
    
    # Clean up old reminders (older than 1 day)
    # Format for IDs: event_id:timestamp
    now = datetime.now().timestamp()
    reminders = [r for r in reminders if ':' not in r or float(r.split(':')[1]) > now - 86400]
    
    # Add new reminder with timestamp
    reminder_id = f"{event_id}:{now}"
    reminders.append(reminder_id)
    
    save_sent_reminders(reminders)

def was_reminder_sent(event_id: str) -> bool:
    """Check if a reminder has already been sent for this event."""
    reminders = load_sent_reminders()
    
    # Check if any reminder ID starts with the event_id
    for reminder in reminders:
        if reminder.startswith(f"{event_id}:"):
            return True
    
    return False

def format_time_until(dt: datetime) -> str:
    """Format a friendly string showing time until the given datetime."""
    now = datetime.now()
    delta = dt - now
    
    if delta.days > 0:
        if delta.days == 1:
            return f"{delta.days} день"
        elif 1 < delta.days < 5:
            return f"{delta.days} дня"
        else:
            return f"{delta.days} дней"
    
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if hours > 0:
        if hours == 1:
            hours_str = f"{hours} час"
        elif 1 < hours < 5:
            hours_str = f"{hours} часа"
        else:
            hours_str = f"{hours} часов"
            
        if minutes > 0:
            if minutes == 1:
                minutes_str = f"{minutes} минуту"
            elif 1 < minutes < 5:
                minutes_str = f"{minutes} минуты"
            else:
                minutes_str = f"{minutes} минут"
            return f"{hours_str} и {minutes_str}"
        else:
            return hours_str
    
    if minutes > 0:
        if minutes == 1:
            return f"{minutes} минуту"
        elif 1 < minutes < 5:
            return f"{minutes} минуты"
        else:
            return f"{minutes} минут"
    
    return "меньше минуты"

def format_schedule_message(events: List[Dict[str, Any]]) -> str:
    """Format a message with upcoming schedule events."""
    if not events:
        return "У вас нет предстоящих занятий на ближайшее время."
    
    now = datetime.now()
    response = "Ваше расписание занятий:\n\n"
    
    for event in events:
        start_time = event["start_time"]
        time_until = format_time_until(start_time)
        
        response += f"📚 {event['title']}\n"
        response += f"🕒 {start_time.strftime('%d.%m.%Y %H:%M')} (через {time_until})\n"
        if event.get("description"):
            # Truncate long descriptions
            description = event.get("description", "")
            if len(description) > 100:
                description = description[:97] + "..."
            response += f"📝 {description}\n"
        response += "\n"
    
    return response 