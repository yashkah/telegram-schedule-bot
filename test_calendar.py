import asyncio
import sys
import logging
from datetime import datetime, timedelta
import calendar_service

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def test_calendar_integration():
    """Test the calendar integration by fetching upcoming events."""
    logger.info("Testing calendar integration...")
    
    # Test getting all events
    now = datetime.now()
    events = await calendar_service.get_events(
        time_min=now,
        time_max=now + timedelta(days=7),
        max_results=10
    )
    
    logger.info(f"Found {len(events)} events in the next 7 days")
    
    if not events:
        logger.info("No events found. Make sure you have events in your calendar.")
        return
    
    # Display events
    logger.info("Upcoming events:")
    for event in events:
        logger.info(f"Title: {event['title']}")
        logger.info(f"Start time: {event['start_time'].strftime('%Y-%m-%d %H:%M')}")
        logger.info(f"Attendees: {event.get('attendees', [])}")
        logger.info(f"Description: {event.get('description', '(No description)')}")
        logger.info("-" * 40)
    
    # Test getting events for a specific user
    test_user = input("Enter a test user identifier (e.g., @username or full name): ")
    user_events = await calendar_service.get_events_for_user(
        user_identifier=test_user,
        time_min=now,
        time_max=now + timedelta(days=30)
    )
    
    logger.info(f"Found {len(user_events)} events for user {test_user} in the next 30 days")
    
    if not user_events:
        logger.info(f"No events found for {test_user}. Make sure the user is included in event attendees or description.")
        return
    
    # Display user events
    logger.info(f"Upcoming events for {test_user}:")
    for event in user_events:
        logger.info(f"Title: {event['title']}")
        logger.info(f"Start time: {event['start_time'].strftime('%Y-%m-%d %H:%M')}")
        logger.info(f"Description: {event.get('description', '(No description)')}")
        logger.info("-" * 40)

if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(test_calendar_integration()) 