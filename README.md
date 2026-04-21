# 🗓️ Schedule Jarvis - 노션 & 구글캘린더 연동 자동화

노션의 일정 데이터를 Claude AI로 자동 파싱하여 구글캘린더에 동기화하는 시스템입니다.

## 📋 프로젝트 목표

1. **Notion 중심 관리**: 노션 데이터베이스에 일정 원문 입력
2. **AI 기반 파싱**: Claude Haiku를 이용한 자동 데이터 추출
3. **Google Calendar 동기화**: 파싱된 데이터를 구글캘린더에 자동 생성
4. **양방향 동기화**: Notion ↔ Google Calendar 변경사항 자동 반영 (최종 목표)

## 🏗️ 프로젝트 구조

```
schedulejarvis/
├── src/
│   ├── config.py                 # 설정 관리
│   ├── notion_client.py          # Notion API 래퍼
│   ├── google_calendar_client.py # Google Calendar API 래퍼
│   ├── schedule_parser.py        # Claude Haiku 파싱
│   ├── sync_manager.py           # 양방향 동기화
│   └── __init__.py
├── main.py                        # CLI 진입점
├── requirements.txt               # 의존성
├── .env.example                   # 환경변수 템플릿
└── README.md                      # 이 파일
```

## 🚀 시작하기

### 1. 환경 설정

```bash
# 저장소 클론
cd schedulejarvis

# 의존성 설치
pip install -r requirements.txt

# .env 파일 생성
cp .env.example .env
```

### 2. API 키 설정

`.env` 파일에 다음 정보를 입력하세요:

```env
# Notion API Key 획득 방법:
# https://www.notion.so/my-integrations → 새 통합 생성
NOTION_API_KEY=your-key

# Claude API Key 획득 방법:
# https://console.anthropic.com → API Keys
CLAUDE_API_KEY=your-key

# Google Calendar 인증은 첫 실행 시 자동 설정됩니다.
GOOGLE_CALENDAR_ID=iothomepyu@gmail.com
```

### 3. 프로그램 실행

#### 대화형 모드 (권장)
```bash
python main.py --interactive
```

#### 또는 직접 호출
```python
from main import parse_and_sync

result = parse_and_sync(
    text="교내일정\n2026년 4월 25일(토) 10:00~12:00\n장소: 학생회관 대회의실\n...",
    notion_page_id="page-uuid"  # 선택사항
)
```

## 📝 입력 형식

### 텍스트 입력 예시
```
교내일정
일정명: RISE사업 G2 간담회 참석
날짜: 2026.07.15. (화)
시간: 13:00~15:00
장소: 산학협력관 2층 세미나실
주요내용: RISE사업 G2(글로벌 지역특화 인재양성) 관련 교육과정 개발을 위한 간담회 진행
참석자: 송온유, 박용운, 변황우
참석기관: RISE사업단, 순천제일대학교
```

### 이미지 입력
```bash
image path/to/schedule.png
```

## 📊 파싱 결과 형식

Claude Haiku가 자동으로 다음 JSON 형식으로 반환합니다:

```json
{
  "제목": "RISE사업 G2 간담회 참석",
  "날짜": "2026.07.15. (화)",
  "시간": "13:00~15:00",
  "장소": ["산학협력관 2층 세미나실"],
  "주요내용": "RISE사업 G2 관련 교육과정 개발을 위한 간담회 진행",
  "참석자": ["송온유", "박용운", "변황우"],
  "참석기관": ["RISE사업단", "순천제일대학교"],
  "종류": ["교내"],
  "Start Time": "2026-07-15T13:00:00+09:00",
  "End Time": "2026-07-15T15:00:00+09:00",
  "Include Time": true
}
```

## 🔄 동기화 워크플로우

### 현재 (Phase 1)
```
사용자 입력 텍스트/이미지
    ↓
Claude Haiku 파싱
    ↓
Notion 데이터 저장 (선택사항)
    ↓
Google Calendar 이벤트 생성
    ↓
Google Calendar Event ID → Notion 역참조
```

### 최종 목표 (Phase 2)
```
Notion 필드 변경 감지 (Webhook)
    ↓
Make.com 시나리오 자동 트리거
    ↓
Google Calendar 자동 동기화
```

### 양방향 동기화 (Phase 3)
```
Notion ←→ Google Calendar
양쪽 변경사항 자동 감지 및 동기화
충돌 해결 로직 추가
```

## 🔧 주요 컴포넌트

### NotionClient
- Notion API를 통한 데이터 조회/수정
- 속성값 추출 및 변환
- 데이터베이스 스키마 관리

### GoogleCalendarClient
- Google Calendar API를 통한 이벤트 관리
- OAuth 인증 처리
- 이벤트 생성/수정/삭제

### ScheduleParser
- Claude Haiku를 이용한 일정 파싱
- 이미지 OCR 지원
- JSON 유효성 검사

### SyncManager
- Notion ↔ Google Calendar 동기화
- 데이터 형식 변환
- 충돌 해결

## 📱 Notion 데이터베이스 구조

필수 속성:
- **제목** (Title): 일정 제목
- **비고 및 원문** (Text): 원본 텍스트 입력 필드
- **추가 요구사항(GPT)** (Text): 추가 정보
- **파일첨부** (Files): 관련 파일
- **일시** (Date): 일정 기간
- **시간** (Text): 구체적 시간 (HH:MM~HH:MM)
- **장소** (Text): 일정 장소
- **주요내용** (Text): 요약
- **참석자** (Text): 참석자 목록
- **참석기관** (Text): 참석 기관
- **일정종류(중요도)** (Select): 교내/개인/가족
- **구글캘린더_이벤트_ID** (Text): 동기화된 Google Event ID

## 🐛 문제 해결

### "Invalid JSON response from Claude"
- Claude의 응답 형식이 잘못되었습니다.
- 로그를 확인하고 프롬프트를 조정하세요.

### "Google Calendar API 인증 실패"
- credentials.json 파일이 없거나 손상되었습니다.
- 첫 실행 시 브라우저를 통해 재인증하세요.

### "Notion API 키 오류"
- 올바른 API 키를 입력했는지 확인하세요.
- 권한을 확인하고 재발급받으세요.

## 📚 참고 자료

- [Notion API 문서](https://developers.notion.com)
- [Google Calendar API 문서](https://developers.google.com/calendar)
- [Anthropic Claude API 문서](https://docs.anthropic.com)
- [Make.com 문서](https://www.make.com/docs)

## 📄 라이센스

MIT License

## 🤝 기여

이슈와 풀 리퀘스트는 환영합니다!

## 📧 연락처

문제가 있으시면 이슈를 등록해주세요.
