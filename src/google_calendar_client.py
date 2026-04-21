from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from google.api_python_client import discovery
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import json
import os

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarClient:
    def __init__(self, calendar_id: str, credentials_file: str = "credentials.json"):
        self.calendar_id = calendar_id
        self.credentials_file = credentials_file
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Google Calendar API 인증"""
        try:
            creds = None

            # saved token이 있으면 로드
            if os.path.exists("token.json"):
                creds = UserCredentials.from_authorized_user_file("token.json", SCOPES)

            # 유효한 credentials가 없으면 새로 인증
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)

                # token.json에 저장
                with open("token.json", "w") as token:
                    token.write(creds.to_json())

            self.service = discovery.build("calendar", "v3", credentials=creds)
            logger.info("✅ Google Calendar API authenticated")

        except Exception as e:
            logger.error(f"Failed to authenticate Google Calendar: {e}")
            raise

    def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """이벤트 생성"""
        try:
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event_data
            ).execute()
            logger.info(f"✅ Event created: {event.get('id')}")
            return event
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            raise

    def update_event(self, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """이벤트 수정"""
        try:
            event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event_data
            ).execute()
            logger.info(f"✅ Event updated: {event_id}")
            return event
        except Exception as e:
            logger.error(f"Failed to update event {event_id}: {e}")
            raise

    def delete_event(self, event_id: str) -> None:
        """이벤트 삭제"""
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            logger.info(f"✅ Event deleted: {event_id}")
        except Exception as e:
            logger.error(f"Failed to delete event {event_id}: {e}")
            raise

    def get_event(self, event_id: str) -> Dict[str, Any]:
        """이벤트 조회"""
        try:
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            return event
        except Exception as e:
            logger.error(f"Failed to retrieve event {event_id}: {e}")
            raise

    def list_events(self, time_min: Optional[str] = None, time_max: Optional[str] = None,
                    max_results: int = 250) -> List[Dict[str, Any]]:
        """이벤트 목록 조회"""
        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get("items", [])
        except Exception as e:
            logger.error(f"Failed to list events: {e}")
            raise

    def build_event(self, title: str, start_time: str, end_time: str,
                   location: Optional[str] = None, description: Optional[str] = None,
                   attendees: Optional[List[str]] = None) -> Dict[str, Any]:
        """이벤트 객체 생성"""
        event = {
            "summary": title,
            "start": {"dateTime": start_time, "timeZone": "Asia/Seoul"},
            "end": {"dateTime": end_time, "timeZone": "Asia/Seoul"},
        }

        if location:
            event["location"] = location

        if description:
            event["description"] = description

        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]

        return event

    def build_all_day_event(self, title: str, start_date: str, end_date: Optional[str] = None,
                           location: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """종일 이벤트 객체 생성"""
        event = {
            "summary": title,
            "start": {"date": start_date},
            "end": {"date": end_date or self._add_days(start_date, 1)},
        }

        if location:
            event["location"] = location

        if description:
            event["description"] = description

        return event

    def find_event_by_description_hint(self, hint: str) -> Optional[Dict[str, Any]]:
        """설명에 특정 텍스트가 포함된 이벤트 찾기"""
        try:
            events = self.list_events(max_results=250)
            for event in events:
                if hint.lower() in (event.get("description", "") or "").lower() or \
                   hint.lower() in (event.get("summary", "") or "").lower():
                    return event
            return None
        except Exception as e:
            logger.error(f"Failed to find event with hint '{hint}': {e}")
            return None

    @staticmethod
    def _add_days(date_str: str, days: int) -> str:
        """날짜에 일수 더하기 (YYYY-MM-DD 형식)"""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return (date_obj + timedelta(days=days)).strftime("%Y-%m-%d")
