import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from src.notion_client import NotionClient
from src.google_calendar_client import GoogleCalendarClient
from src.claude_parser import ClaudeParser
import config

logger = logging.getLogger(__name__)


class SyncManager:
    def __init__(
        self,
        notion_client: NotionClient,
        calendar_client: GoogleCalendarClient,
        parser: ClaudeParser,
    ):
        self.notion = notion_client
        self.calendar = calendar_client
        self.parser = parser

    def process_raw_input(
        self, raw_text: str, page_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process raw input and update Notion + create calendar event"""
        try:
            # Step 1: Parse raw input using Claude
            parsed_data = self.parser.parse_schedule(raw_text)
            logger.info(f"Parsed schedule: {parsed_data.get('제목', 'Unknown')}")

            # Step 2: Update Notion page with parsed data
            if page_id:
                self._update_notion_page(page_id, parsed_data)

            # Step 3: Create Google Calendar event
            calendar_event_id = self._create_calendar_event(parsed_data)
            parsed_data["calendar_event_id"] = calendar_event_id

            # Step 4: Update Notion with calendar event ID
            if page_id and calendar_event_id:
                self._update_notion_calendar_id(page_id, calendar_event_id)

            return parsed_data

        except Exception as e:
            logger.error(f"Error processing raw input: {e}")
            raise

    def _update_notion_page(self, page_id: str, parsed_data: Dict[str, Any]) -> None:
        """Update Notion page with parsed schedule data"""
        try:
            properties_map = {
                "title": parsed_data.get("제목"),
                "date": self._build_notion_date(parsed_data),
                "time": parsed_data.get("시간"),
                "location": parsed_data.get("장소"),
                "content": parsed_data.get("주요내용"),
                "attendees": parsed_data.get("참석자"),
                "organization": parsed_data.get("참석기관"),
                "category": parsed_data.get("종류"),
            }

            properties = self.notion.create_property_dict(
                properties_map, config.NOTION_FIELDS
            )

            if properties:
                self.notion.update_page_properties(page_id, properties)
                logger.info(f"Updated Notion page {page_id}")
        except Exception as e:
            logger.error(f"Error updating Notion page: {e}")
            raise

    def _build_notion_date(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build Notion date object from parsed data"""
        try:
            date_str = parsed_data.get("날짜", "N/A")
            start_date, end_date = self.parser.parse_date_range(date_str)

            if not start_date:
                return None

            date_obj = {"start": start_date.strftime("%Y-%m-%d")}

            if end_date and end_date != start_date:
                date_obj["end"] = end_date.strftime("%Y-%m-%d")

            return date_obj
        except Exception as e:
            logger.error(f"Error building Notion date: {e}")
            return None

    def _create_calendar_event(self, parsed_data: Dict[str, Any]) -> str:
        """Create Google Calendar event from parsed data"""
        try:
            # Extract data
            title = parsed_data.get("제목", "No Title")
            start_time = parsed_data.get("Start Time")
            end_time = parsed_data.get("End Time")
            location = parsed_data.get("장소")
            content = parsed_data.get("주요내용")

            if not start_time or not end_time:
                logger.error("Missing start or end time for calendar event")
                return None

            # Build event body
            event_body = self.calendar.build_event_body(
                title=title,
                start_time=start_time,
                end_time=end_time,
                location=location,
                description=content,
            )

            # Create event
            event = self.calendar.create_event(event_body)
            event_id = event.get("id")
            logger.info(f"Created calendar event: {event_id}")

            return event_id
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return None

    def _update_notion_calendar_id(self, page_id: str, calendar_event_id: str) -> None:
        """Update Notion page with calendar event ID"""
        try:
            properties = {
                config.NOTION_FIELDS["calendar_event_id"]: {
                    "rich_text": [{"text": {"content": calendar_event_id}}]
                }
            }
            self.notion.update_page_properties(page_id, properties)
            logger.info(f"Updated Notion page {page_id} with calendar event ID")
        except Exception as e:
            logger.error(f"Error updating Notion calendar ID: {e}")

    def sync_notion_to_calendar(self, page_id: str) -> Dict[str, Any]:
        """Sync Notion page to Google Calendar"""
        try:
            page = self.notion.get_page_by_id(page_id)

            # Extract data from Notion
            title = self.notion.get_property_value(page, config.NOTION_FIELDS["title"])
            date_obj = self.notion.get_property_value(page, config.NOTION_FIELDS["date"])
            time = self.notion.get_property_value(page, config.NOTION_FIELDS["time"])
            location = self.notion.get_property_value(
                page, config.NOTION_FIELDS["location"]
            )
            content = self.notion.get_property_value(
                page, config.NOTION_FIELDS["content"]
            )
            calendar_event_id = self.notion.get_property_value(
                page, config.NOTION_FIELDS["calendar_event_id"]
            )

            if not title or not date_obj:
                logger.warning(f"Missing title or date for page {page_id}")
                return {}

            # Build calendar event
            start_time, end_time = self._build_calendar_times(date_obj, time)

            event_body = self.calendar.build_event_body(
                title=title,
                start_time=start_time,
                end_time=end_time,
                location=location,
                description=content,
            )

            # Create or update event
            if calendar_event_id:
                self.calendar.update_event(calendar_event_id, event_body)
                logger.info(f"Updated calendar event: {calendar_event_id}")
            else:
                event = self.calendar.create_event(event_body)
                calendar_event_id = event.get("id")
                self._update_notion_calendar_id(page_id, calendar_event_id)
                logger.info(f"Created new calendar event: {calendar_event_id}")

            return {"page_id": page_id, "calendar_event_id": calendar_event_id}

        except Exception as e:
            logger.error(f"Error syncing Notion to Calendar: {e}")
            raise

    def _build_calendar_times(
        self, date_obj: Dict[str, Any], time_str: Optional[str]
    ) -> tuple:
        """Build calendar start and end times from date and time objects"""
        try:
            start_date_str = date_obj.get("start")
            end_date_str = date_obj.get("end", start_date_str)

            if not start_date_str:
                raise ValueError("No start date provided")

            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

            if time_str and time_str != "N/A":
                start_time, end_time = self.parser.parse_time_range(time_str)
            else:
                start_time = "09:00"
                end_time = "17:00"

            start_datetime = start_date.replace(
                hour=int(start_time.split(":")[0]),
                minute=int(start_time.split(":")[1]),
            )
            end_datetime = end_date.replace(
                hour=int(end_time.split(":")[0]),
                minute=int(end_time.split(":")[1]),
            )

            # Convert to ISO 8601 format
            start_iso = start_datetime.isoformat() + "+09:00"
            end_iso = end_datetime.isoformat() + "+09:00"

            return (start_iso, end_iso)
        except Exception as e:
            logger.error(f"Error building calendar times: {e}")
            raise
