import datetime
import os
import pickle
from typing import Optional
from mcp.server.fastmcp import FastMCP
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

mcp = FastMCP("calendar")

SCOPES = ['https://www.googleapis.com/auth/calendar']

# Auth

def get_calendar_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('calendar', 'v3', credentials=creds)

# Event
@mcp.tool()
async def create_event(summary: str, start_time: str, end_time: str, description: Optional[str] = None) -> str:
    """Create a calendar event. Time format: 'YYYY-MM-DDTHH:MM:SS' (24h, ISO 8601)"""
    service = get_calendar_service()
    event = {
        'summary': summary,
        'description': description or '',
        'start': {'dateTime': start_time, 'timeZone': 'UTC'},
        'end': {'dateTime': end_time, 'timeZone': 'UTC'},
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    return f"Event created: {event.get('htmlLink')}"

# Reminder (as all-day event with 'reminder' in summary)
@mcp.tool()
async def create_reminder(summary: str, date: str) -> str:
    """Create a reminder (all-day event). Date format: 'YYYY-MM-DD'"""
    service = get_calendar_service()
    event = {
        'summary': f"Reminder: {summary}",
        'start': {'date': date},
        'end': {'date': date},
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    return f"Reminder created: {event.get('htmlLink')}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
