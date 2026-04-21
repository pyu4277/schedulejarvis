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

# Notion Field Names (Make.com 시나리오 기준)
NOTION_FIELDS = {
    "title": "주제",  # Make.com에서는 "주제" (title type)
    "date": "일시",  # Make.com에서는 "일시" (date type)
    "time": "시간",  # 시간 정보 (HH:MM~HH:MM)
    "location": "일시/장소",  # 장소 정보는 이 필드의 rich_text에 포함됨
    "content": "주요내용",
    "attendees": "참석자",  # relation type
    "organization": "참석기관",  # rich_text
    "category": "일정종류(중요도)",  # multi_select
    "raw_text": "비고 및 원문",
    "additional_requirement": "추가 요구사항(GPT)",
    "attachment": "파일첨부",  # files type
    "sync_status": "동기화 상태",  # select (향후 사용)
    "calendar_event_id": "구글ID",  # Make.com과 동일한 필드명
    "creation_time": "생성 일시",  # 생성된 시간
    "last_edited_time": "최종 편집 일시",  # 마지막 수정 시간
    "gpt_summary": "GPT 요약 결과",  # Claude 파싱 결과 전체
    "parse_result": "Parse 결과",  # 파싱 결과 상세
    "generation_flag": "생성(setting)",  # checkbox - 캘린더 생성 여부
}
