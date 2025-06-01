"""
Synchronization functionality between schedule and slots sheets.
"""

from datetime import datetime
import pytz
from telegram_bot.sheets.google import connect_to_sheet

def sync_schedule_with_slots() -> dict:
    """
    Synchronize schedule with available slots.
    
    Returns:
        dict: Statistics about the sync operation
    """
    print("🔄 Starting schedule-slot synchronization...")
    stats = {"synced": 0, "skipped": 0, "errors": 0}
    
    try:
        # Connect to sheets
        sheets = connect_to_sheet()
        schedule_sheet = sheets["schedule"]
        slots_sheet = sheets["slots"]
        
        # Get data from both sheets
        schedule_data = schedule_sheet.get_all_records()
        slots_data = slots_sheet.get_all_records()
        
        # Process each lesson in schedule
        for lesson in schedule_data:
            try:
                # Skip lessons without required fields
                if not all(key in lesson for key in ["Date", "Time", "Name", "Telegram_ID"]):
                    print(f"⚠️ Skipping lesson with missing fields: {lesson}")
                    stats["skipped"] += 1
                    continue
                
                # Find matching slot
                for index, slot in enumerate(slots_data, start=2):
                    if (
                        slot["Date"] == lesson["Date"]
                        and slot["Time"] == lesson["Time"]
                    ):
                        # Skip if slot is already booked
                        if slot["Booked"].strip().upper() == "TRUE":
                            print(f"⏭️ Slot already booked: {lesson['Date']} {lesson['Time']}")
                            stats["skipped"] += 1
                            continue
                        
                        # Update slot
                        slots_sheet.update(f"C{index}", "TRUE")  # Booked
                        slots_sheet.update(f"D{index}", lesson["Name"])  # Student
                        slots_sheet.update(f"E{index}", lesson["Telegram_ID"])  # Telegram ID
                        
                        print(f"✅ Synced slot: {lesson['Date']} {lesson['Time']}")
                        stats["synced"] += 1
                        break
                        
            except Exception as e:
                print(f"❌ Error processing lesson: {e}")
                stats["errors"] += 1
                continue
        
        print(f"✅ Sync completed: {stats['synced']} synced, {stats['skipped']} skipped, {stats['errors']} errors")
        return stats
        
    except Exception as e:
        print(f"❌ Failed to sync sheets: {e}")
        raise 