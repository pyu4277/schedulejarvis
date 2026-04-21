import os
from dotenv import load_dotenv

load_dotenv()

# Notion Configuration
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "a96a3b8563e342908b2f0af8960370b7")

# Google Calendar Configuration
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "iothomepyu@gmail.com")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "google_credentials.json")

# Anthropic Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Sync Configuration
SYNC_ENABLED = os.getenv("SYNC_ENABLED", "true").lower() == "true"

# Calendar Type Mapping
CALENDAR_MAPPING = {
    "교내": "pyu_internal",  # PYU 업무 캘린더 (현재는 가족 캘린더로 통합)
    "개인": "pyu_personal",  # pyu4277office@gmail.com (현재는 가족 캘린더로 통합)
    "가족": "family",        # 윤윤남매 가족일정
}

# Target Calendar (모든 일정 → 가족 캘린더로 통합)
TARGET_CALENDAR_ID = "iothomepyu@gmail.com"

# Notion Field Names
NOTION_FIELDS = {
    "title": "제목",
    "date": "일시/장소, 일시",
    "time": "시간",
    "location": "장소",
    "content": "주요내용",
    "attendees": "참석자",
    "organization": "참석기관",
    "category": "일정종류(중요도)",
    "raw_text": "비고 및 원문",
    "additional_requirement": "추가 요구사항(GPT)",
    "attachment": "파일첨부",
    "sync_status": "동기화 상태",
    "calendar_event_id": "캘린더 이벤트 ID",
}
