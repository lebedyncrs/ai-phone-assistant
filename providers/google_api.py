import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import pickle

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

CLIENT_SECRET_FILE = os.environ.get("GOOGLE_CLIENT_SECRET_FILE")
TOKEN_FILE = os.environ.get("GOOGLE_TOKEN_FILE")
SCOPES = ["https://www.googleapis.com/auth/contacts.readonly", "https://www.googleapis.com/auth/calendar.readonly"]


def get_google_service(service_name: str, version: str):
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        raise Exception("Invalid credentials")
    return build(service_name, version, credentials=creds)


def search_contacts(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    service = get_google_service("people", "v1")
    results = service.people().searchContacts(query=query, pageSize=max_results, readMask="names,emailAddresses,phoneNumbers").execute()

    contacts = []
    for person in results.get("results", []):
        person_data = person.get("person", {})
        contact_info = {
            "first_name": person_data.get("names", [[]])[0].get("givenName", ""),
            "last_name": person_data.get("names", [[]])[0].get("familyName", ""),
            "phone_numbers": person_data.get("phoneNumbers", [])[0].get("value", ""),
        }
        contacts.append(contact_info)

    return contacts


def get_calendar_events(start_time: datetime, end_time: datetime, calendar_id: str = "primary", max_results: int = 10) -> List[Dict[str, Any]]:
    try:
        service = get_google_service("calendar", "v3")
        start_time_str = start_time.isoformat() + "Z"
        end_time_str = end_time.isoformat() + "Z"

        events_result = (
            service.events()
            .list(calendarId=calendar_id, timeMin=start_time_str, timeMax=end_time_str, maxResults=max_results, singleEvents=True, orderBy="startTime")
            .execute()
        )

        events = []
        for event in events_result.get("items", []):
            event_info = {
                "id": event.get("id", ""),
                "summary": event.get("summary", "No title"),
                "description": event.get("description", ""),
                "location": event.get("location", ""),
                "start": event.get("start", {}),
                "end": event.get("end", {}),
                "attendees": event.get("attendees", []),
                "organizer": event.get("organizer", {}),
                "status": event.get("status", ""),
            }
            events.append(event_info)

        return events

    except Exception as e:
        print(f"Error retrieving calendar events: {e}")
        return []
