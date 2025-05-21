import datetime
import logging
import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# === CONFIGURATION ===
CLIENT_ID = '406119069791-fijp59i00tm0fkpcoomm43b3foqkrf2t.apps.googleusercontent.com'
CLIENT_SECRET = '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'
SCOPES = ['https://www.googleapis.com/auth/calendar']
REDIRECT_URI = 'http://localhost'
TOKEN_PATH = 'token.pickle'

# === LOGGING SETUP ===
logging.basicConfig(
    filename='calendar.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_credentials():
    creds = None

    # Try loading existing token
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
            logging.info("Loaded credentials from token.pickle.")

    # Refresh or authenticate if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logging.info("Refreshed access token.")
            except Exception as e:
                logging.error(f"Failed to refresh token: {e}")
        else:
            try:
                flow = Flow.from_client_config(
                    {
                        "installed": {
                            "client_id": CLIENT_ID,
                            "client_secret": CLIENT_SECRET,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": [REDIRECT_URI]
                        }
                    },
                    scopes=SCOPES
                )
                flow.redirect_uri = REDIRECT_URI
                auth_url, _ = flow.authorization_url(prompt='consent')

                print("Please go to this URL and authorize access:\n", auth_url)
                code = input("Enter the authorization code: ")
                flow.fetch_token(code=code)
                creds = flow.credentials
                with open(TOKEN_PATH, 'wb') as token:
                    pickle.dump(creds, token)
                logging.info("Authenticated and saved credentials to token.pickle.")
            except Exception as e:
                logging.critical(f"Authentication failed: {e}")
                raise

    return creds

def get_calendar_service():
    creds = get_credentials()
    try:
        service = build('calendar', 'v3', credentials=creds)
        logging.info("Google Calendar service created successfully.")
        return service
    except Exception as e:
        logging.critical(f"Failed to create calendar service: {e}")
        raise

def list_events():
    logging.info("Listing upcoming events.")
    try:
        service = get_calendar_service()
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            print("No upcoming events found.")
            logging.info("No upcoming events found.")
        else:
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"{start} - {event['summary']}")
                logging.info(f"Event: {start} - {event['summary']}")
    except Exception as e:
        logging.error(f"Failed to list events: {e}")

if __name__ == '__main__':
    list_events()
