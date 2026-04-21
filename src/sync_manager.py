from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

class SyncManager:
    """Notion과 Google Calendar 간의 양방향 동기화"""

    def __init__(self, notion_client, google_client, parsed_data: Dict[str, Any]):
        self.notion = notion_client
        self.google = google_client
        self.parsed_data = parsed_data

    def sync_to_google_calendar(self, notion_page_id: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """파싱된 데이터를 Google Calendar에 동기화"""
        try:
            # 이벤트 빌드
            event_data = self._build_google_event()

            # Google Calendar에 생성
            event = self.google.create_event(event_data)
            event_id = event.get("id")

            # Notion에 Google Calendar Event ID 저장
            self.notion.set_property(
                notion_page_id,
                "구글캘린더_이벤트_ID",
                event_id
            )

            logger.info(f"✅ Event synced to Google Calendar: {event_id}")
            return event_id, event

        except Exception as e:
            logger.error(f"Failed to sync to Google Calendar: {e}")
            raise

    def sync_from_google_calendar(self, event_id: str, notion_page_id: str) -> None:
        """Google Calendar의 변경사항을 Notion에 동기화"""
        try:
            event = self.google.get_event(event_id)

            # 데이터 추출
            title = event.get("summary", "")
            location = event.get("location", "")
            description = event.get("description", "")

            # 시간 정보 추출
            start = event.get("start", {})
            end = event.get("end", {})

            # Notion 속성 업데이트
            update_data = {
                "제목": title,
                "주요내용": description,
            }

            if location:
                update_data["장소"] = location

            # 날짜/시간 처리
            if "dateTime" in start:
                # 시간 포함
                start_dt = date_parser.isoparse(start["dateTime"])
                end_dt = date_parser.isoparse(end["dateTime"])

                # Notion date 형식으로 변환
                update_data["일시"] = {
                    "start": start_dt.strftime("%Y-%m-%d"),
                    "end": end_dt.strftime("%Y-%m-%d")
                }
                update_data["시간"] = f"{start_dt.strftime('%H:%M')}~{end_dt.strftime('%H:%M')}"

            elif "date" in start:
                # 종일 일정
                start_date = start["date"]
                end_date = end.get("date", start_date)
                update_data["일시"] = {
                    "start": start_date,
                    "end": end_date
                }

            # Notion 업데이트
            properties = self.notion._build_properties(update_data)
            self.notion.update_properties(notion_page_id, properties)

            logger.info(f"✅ Changes synced from Google Calendar to Notion: {notion_page_id}")

        except Exception as e:
            logger.error(f"Failed to sync from Google Calendar: {e}")
            raise

    def _build_google_event(self) -> Dict[str, Any]:
        """파싱된 데이터로 Google Calendar 이벤트 생성"""
        title = self.parsed_data.get("제목", "")
        start_time = self.parsed_data.get("Start Time", "")
        end_time = self.parsed_data.get("End Time", "")
        location_data = self.parsed_data.get("장소", "N/A")
        description = self.parsed_data.get("주요내용", "")
        attendees = self.parsed_data.get("참석자", "N/A")

        # 장소 처리 (배열일 수 있음)
        if isinstance(location_data, list):
            location = ", ".join(location_data) if location_data else ""
        else:
            location = location_data if location_data != "N/A" else ""

        # 설명 작성
        full_description = description
        if self.parsed_data.get("참석기관") and self.parsed_data.get("참석기관") != "N/A":
            institutions = self.parsed_data.get("참석기관")
            institution_str = ", ".join(institutions) if isinstance(institutions, list) else institutions
            full_description += f"\n참석기관: {institution_str}"

        # 종류 추가
        if self.parsed_data.get("종류"):
            type_str = ", ".join(self.parsed_data.get("종류", []))
            full_description += f"\n종류: {type_str}"

        # 이벤트 생성
        event = {
            "summary": title,
            "description": full_description,
            "start": {"dateTime": start_time, "timeZone": "Asia/Seoul"},
            "end": {"dateTime": end_time, "timeZone": "Asia/Seoul"},
        }

        if location:
            event["location"] = location

        # 참석자 추가 (이메일이 있는 경우만)
        if attendees != "N/A" and isinstance(attendees, list):
            # 참석자 이름만 있으므로, 실제 이메일로 변환 필요
            # 지금은 스킵 (나중에 참석자 DB와 연동)
            pass

        return event

    def handle_notion_deletion(self, event_id: str) -> None:
        """Notion에서 일정이 삭제될 때 Google Calendar에서도 삭제"""
        try:
            if event_id:
                self.google.delete_event(event_id)
                logger.info(f"✅ Event deleted from Google Calendar: {event_id}")
        except Exception as e:
            logger.error(f"Failed to delete event from Google Calendar: {e}")
            raise

    def handle_google_deletion(self, notion_page_id: str) -> None:
        """Google Calendar에서 이벤트가 삭제될 때 Notion에서도 삭제"""
        try:
            # Notion 페이지 삭제는 API로 직접 삭제 불가능하므로,
            # 상태를 표시하거나 스킵 처리
            self.notion.set_property(notion_page_id, "상태", "삭제됨")
            logger.info(f"✅ Notion page marked as deleted: {notion_page_id}")
        except Exception as e:
            logger.error(f"Failed to handle Google Calendar deletion: {e}")
            raise

    def validate_sync_compatibility(self) -> bool:
        """동기화 호환성 검증"""
        required_fields = ["제목", "Start Time", "End Time"]
        for field in required_fields:
            if not self.parsed_data.get(field):
                logger.warning(f"Missing required field for sync: {field}")
                return False
        return True
