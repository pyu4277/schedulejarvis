from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import logging
import os

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarClient:
    def __init__(self, calendar_id: str, credentials_file: Optional[str] = None):
        self.calendar_id = calendar_id
        self.service = self._build_service(credentials_file)

    def _build_service(self, credentials_file: Optional[str] = None):
        """Build Google Calendar API service"""
        try:
            if credentials_file and os.path.exists(credentials_file):
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_file, scopes=SCOPES
                )
            else:
                # Try to use OAuth flow if no service account
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                credentials = flow.run_local_server(port=0)

            service = build("calendar", "v3", credentials=credentials)
            logger.info("Google Calendar service built successfully")
            return service
        except Exception as e:
            logger.error(f"Error building Google Calendar service: {e}")
            raise

    def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new event in Google Calendar"""
        try:
            event = self.service.events().insert(
                calendarId=self.calendar_id, body=event_data
            ).execute()
            logger.info(f"Created event: {event.get('id')}")
            return event
        except HttpError as e:
            logger.error(f"Error creating event: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating event: {e}")
            raise

    def update_event(self, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing event"""
        try:
            event = self.service.events().update(
                calendarId=self.calendar_id, eventId=event_id, body=event_data
            ).execute()
            logger.info(f"Updated event: {event_id}")
            return event
        except HttpError as e:
            logger.error(f"Error updating event {event_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating event: {e}")
            raise

    def delete_event(self, event_id: str) -> None:
        """Delete an event"""
        try:
            self.service.events().delete(
                calendarId=self.calendar_id, eventId=event_id
            ).execute()
            logger.info(f"Deleted event: {event_id}")
        except HttpError as e:
            logger.error(f"Error deleting event {event_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting event: {e}")
            raise

    def get_event(self, event_id: str) -> Dict[str, Any]:
        """Get event details"""
        try:
            event = self.service.events().get(
                calendarId=self.calendar_id, eventId=event_id
            ).execute()
            return event
        except HttpError as e:
            logger.error(f"Error retrieving event {event_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving event: {e}")
            raise

    def list_events(
        self,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List events in calendar"""
        try:
            kwargs = {
                "calendarId": self.calendar_id,
                "singleEvents": True,
                "orderBy": "startTime",
            }

            if time_min:
                kwargs["timeMin"] = time_min
            if time_max:
                kwargs["timeMax"] = time_max
            if query:
                kwargs["q"] = query

            events = self.service.events().list(**kwargs).execute()
            return events.get("items", [])
        except HttpError as e:
            logger.error(f"Error listing events: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing events: {e}")
            raise

    def build_event_body(
        self,
        title: str,
        start_time: str,
        end_time: str,
        location: Optional[str] = None,
        description: Optional[str] = None,
        attendees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Build event body for Google Calendar API"""
        event = {
            "summary": title,
            "start": {"dateTime": start_time},
            "end": {"dateTime": end_time},
        }

        if location:
            if isinstance(location, list):
                event["location"] = ", ".join(location)
            else:
                event["location"] = location

        if description:
            event["description"] = description

        if attendees and isinstance(attendees, list):
            event["attendees"] = [{"email": email} for email in attendees if email]

        return event
