import os
import datetime
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

# For Google Calendar API
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Setup logging
logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Path for token storage
TOKENS_DIR = Path("tokens")
TOKENS_DIR.mkdir(exist_ok=True)
TOKEN_PATH = TOKENS_DIR / "token.json"
CREDENTIALS_PATH = Path("credentials.json")


def get_calendar_service():
    """Connect to Google Calendar API and return the service."""
    creds = None
    
    # The file token.json stores the user's access and refresh tokens
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_info(
            json.loads(TOKEN_PATH.read_text()), SCOPES)
    
    # If credentials don't exist or are invalid, request new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                logger.error(f"Credentials file not found at {CREDENTIALS_PATH}. "
                           f"Please download credentials file from Google Cloud Console.")
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        TOKEN_PATH.write_text(json.dumps({
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }))
    
    return build('calendar', 'v3', credentials=creds)


async def get_events(calendar_id: str = 'primary', 
                     time_min: Optional[datetime.datetime] = None,
                     time_max: Optional[datetime.datetime] = None,
                     max_results: int = 10) -> List[Dict[str, Any]]:
    """Get events from Google Calendar.
    
    Args:
        calendar_id: Calendar ID to fetch events from
        time_min: Minimum time for events (defaults to now)
        time_max: Maximum time for events (defaults to 7 days from now)
        max_results: Maximum number of events to return
        
    Returns:
        List of event objects with normalized format
    """
    service = get_calendar_service()
    if not service:
        logger.error("Failed to get calendar service")
        return []
    
    # Set default time values if not provided
    now = datetime.datetime.utcnow()
    time_min = time_min or now
    time_max = time_max or (now + datetime.timedelta(days=7))
    
    # Format times for API
    time_min_str = time_min.isoformat() + 'Z'  # 'Z' indicates UTC time
    time_max_str = time_max.isoformat() + 'Z'
    
    try:
        # Call the Calendar API
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min_str,
            timeMax=time_max_str,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            logger.info('No upcoming events found.')
            return []
        
        # Normalize event format
        normalized_events = []
        for event in events:
            # Get start time
            start = event['start'].get('dateTime', event['start'].get('date'))
            if 'T' in start:  # This is a dateTime, not just a date
                start_time = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
            else:
                # All-day event, set to midnight
                start_time = datetime.datetime.fromisoformat(f"{start}T00:00:00")
            
            # Get attendees if any
            attendees = []
            if 'attendees' in event:
                for attendee in event['attendees']:
                    email = attendee.get('email', '')
                    display_name = attendee.get('displayName', '')
                    
                    # Try to extract username if it's an email
                    if '@' in email:
                        username = email.split('@')[0]
                        attendees.append(f"@{username}")
                    
                    # Also add display name if available
                    if display_name:
                        attendees.append(display_name)
            
            # Extract full names or usernames from description
            description = event.get('description', '')
            if description:
                # Look for @username or full names in description
                import re
                usernames = re.findall(r'@\w+', description)
                attendees.extend(usernames)
                
                # Also look for Name: something patterns
                names = re.findall(r'(Student|Name|Attendee):\s*([^,\n]+)', description)
                attendees.extend([name[1].strip() for name in names])
            
            normalized_events.append({
                'id': event['id'],
                'title': event.get('summary', 'Untitled Event'),
                'start_time': start_time,
                'description': description,
                'attendees': list(set(attendees))  # Remove duplicates
            })
        
        return normalized_events
        
    except Exception as error:
        logger.error(f'An error occurred: {error}')
        return []


async def get_events_for_user(user_identifier: str,
                             time_min: Optional[datetime.datetime] = None,
                             time_max: Optional[datetime.datetime] = None) -> List[Dict[str, Any]]:
    """Get events relevant to a specific user."""
    all_events = await get_events(time_min=time_min, time_max=time_max, max_results=50)
    
    # Filter events for this user
    return [
        {
            'id': event['id'],
            'title': event['title'],
            'start_time': event['start_time'],
            'description': event.get('description', '')
        }
        for event in all_events
        if user_identifier in event.get('attendees', [])
    ] 