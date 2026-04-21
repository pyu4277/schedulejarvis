#!/usr/bin/env python3
import sys
import json
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from src import (
    NotionClient,
    GoogleCalendarClient,
    ScheduleParser,
    SyncManager,
    load_settings
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_and_sync(text: str, image_path: Optional[str] = None,
                  notion_page_id: Optional[str] = None,
                  save_to_notion: bool = True) -> dict:
    """
    입력 텍스트와 이미지를 파싱하고 Google Calendar에 동기화

    Args:
        text: 일정 정보 텍스트
        image_path: 이미지 파일 경로 (선택사항)
        notion_page_id: Notion 페이지 ID (선택사항)
        save_to_notion: Notion에 저장할지 여부

    Returns:
        동기화 결과
    """
    try:
        settings = load_settings()

        # 1. Claude로 파싱
        logger.info("📝 Parsing schedule information...")
        parser = ScheduleParser(settings.CLAUDE_API_KEY)
        parsed_data = parser.parse_schedule(text=text, image_path=image_path)

        logger.info(f"✅ Parsed data:\n{json.dumps(parsed_data, indent=2, ensure_ascii=False)}")

        # 2. Notion에 데이터 저장 (선택사항)
        if save_to_notion and notion_page_id:
            logger.info(f"📌 Saving to Notion page {notion_page_id}...")
            notion = NotionClient(settings.NOTION_API_KEY, settings.NOTION_DATABASE_ID)
            _save_to_notion(notion, notion_page_id, parsed_data)

        # 3. Google Calendar에 동기화
        logger.info("📅 Syncing to Google Calendar...")
        google = GoogleCalendarClient(
            settings.GOOGLE_CALENDAR_ID,
            settings.GOOGLE_CREDENTIALS_FILE
        )

        sync_manager = SyncManager(None, google, parsed_data)

        if not sync_manager.validate_sync_compatibility():
            logger.warning("⚠️  Some required fields are missing for sync")
            return {
                "status": "warning",
                "parsed_data": parsed_data,
                "message": "파싱 완료했으나 일부 필수 필드가 누락되었습니다."
            }

        event_data = sync_manager._build_google_event()
        event = google.create_event(event_data)
        event_id = event.get("id")

        # Google Calendar Event ID를 Notion에 저장
        if save_to_notion and notion_page_id:
            notion.set_property(notion_page_id, "구글캘린더_이벤트_ID", event_id)

        logger.info(f"✅ Event created in Google Calendar: {event_id}")

        return {
            "status": "success",
            "parsed_data": parsed_data,
            "google_event_id": event_id,
            "google_event": event,
            "message": "일정이 성공적으로 등록되었습니다."
        }

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": f"오류가 발생했습니다: {e}"
        }

def _save_to_notion(notion: NotionClient, page_id: str, parsed_data: dict) -> None:
    """Notion 페이지에 파싱된 데이터 저장"""
    try:
        # Notion 속성 빌드
        properties = {}

        # 제목
        if parsed_data.get("제목"):
            properties["제목"] = {
                "rich_text": [{"text": {"content": parsed_data["제목"]}}]
            }

        # 주요내용
        if parsed_data.get("주요내용"):
            properties["주요내용"] = {
                "rich_text": [{"text": {"content": parsed_data["주요내용"]}}]
            }

        # 날짜
        if parsed_data.get("날짜") and parsed_data["날짜"] != "N/A":
            date_str = parsed_data["날짜"].split(" ")[0]  # "YYYY.MM.DD" 추출
            date_formatted = date_str.replace(".", "-")  # "YYYY-MM-DD" 형식으로 변환
            properties["일시"] = {
                "date": {
                    "start": date_formatted
                }
            }

        # 장소
        if parsed_data.get("장소") and parsed_data["장소"] != "N/A":
            location_data = parsed_data["장소"]
            if isinstance(location_data, list):
                location_str = ", ".join(location_data)
            else:
                location_str = location_data

            properties["장소"] = {
                "rich_text": [{"text": {"content": location_str}}]
            }

        # 참석자
        if parsed_data.get("참석자") and parsed_data["참석자"] != "N/A":
            attendees = parsed_data["참석자"]
            attendee_str = ", ".join(attendees) if isinstance(attendees, list) else attendees
            properties["참석자"] = {
                "rich_text": [{"text": {"content": attendee_str}}]
            }

        # 참석기관
        if parsed_data.get("참석기관") and parsed_data["참석기관"] != "N/A":
            institutions = parsed_data["참석기관"]
            institution_str = ", ".join(institutions) if isinstance(institutions, list) else institutions
            properties["참석기관"] = {
                "rich_text": [{"text": {"content": institution_str}}]
            }

        # 종류
        if parsed_data.get("종류"):
            types = parsed_data["종류"]
            if types:
                type_name = types[0] if isinstance(types, list) else types
                properties["일정종류(중요도)"] = {
                    "select": {"name": type_name}
                }

        # Notion에 업데이트
        notion.update_properties(page_id, properties)
        logger.info(f"✅ Updated Notion page: {page_id}")

    except Exception as e:
        logger.error(f"Failed to save to Notion: {e}")
        raise

def interactive_mode():
    """대화형 모드"""
    print("\n🗓️  Schedule Jarvis - 일정 관리 자동화")
    print("=" * 50)
    print("사용 방법:")
    print("  1. 텍스트로 입력: text <텍스트>")
    print("  2. 이미지로 입력: image <경로>")
    print("  3. 종료: exit")
    print("=" * 50)

    while True:
        try:
            user_input = input("\n입력 > ").strip()

            if user_input.lower() == "exit":
                print("👋 종료합니다.")
                break

            if user_input.startswith("text "):
                text = user_input[5:].strip()
                if text:
                    result = parse_and_sync(text)
                    print(f"\n{result['message']}")
                    if result['status'] == 'success':
                        print(f"Google Calendar Event ID: {result.get('google_event_id')}")
                else:
                    print("❌ 텍스트를 입력해주세요.")

            elif user_input.startswith("image "):
                image_path = user_input[6:].strip()
                if Path(image_path).exists():
                    result = parse_and_sync("", image_path=image_path)
                    print(f"\n{result['message']}")
                    if result['status'] == 'success':
                        print(f"Google Calendar Event ID: {result.get('google_event_id')}")
                else:
                    print(f"❌ 파일을 찾을 수 없습니다: {image_path}")

            else:
                print("❌ 올바른 명령어를 사용해주세요.")

        except KeyboardInterrupt:
            print("\n👋 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류: {e}")

def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            interactive_mode()
        elif sys.argv[1] == "--init-config":
            from src.config import save_config_template
            save_config_template()
        else:
            print(f"Usage: python main.py [--interactive|--init-config]")
    else:
        interactive_mode()

if __name__ == "__main__":
    main()
