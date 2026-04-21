# Schedule Jarvis

Notion과 Google Calendar를 연동하여 일정을 자동으로 관리하는 시스템입니다.

## 목표

- **Notion**: 원문/추가요구사항/파일을 입력 → Claude Haiku로 자동 파싱 → 필드 자동 채우기
- **Google Calendar**: 파싱된 데이터로 자동 이벤트 생성
- **양방향 동기화**: 노션 변경 ↔ 캘린더 변경 (향후)

## 아키텍처

### 핵심 모듈

1. **ClaudeParser** (`src/claude_parser.py`)
   - Claude Haiku를 사용하여 원문 분석
   - 제목, 날짜, 시간, 장소, 참석자 등 자동 추출
   - JSON 형식으로 구조화된 데이터 반환

2. **NotionClient** (`src/notion_client.py`)
   - Notion API 래퍼
   - 페이지 조회, 속성 업데이트, 데이터베이스 쿼리
   - 양방향 동기화용 추적 필드 관리

3. **GoogleCalendarClient** (`src/google_calendar_client.py`)
   - Google Calendar API 래퍼
   - 이벤트 생성, 수정, 삭제
   - 캘린더 조회 및 검색

4. **SyncManager** (`src/sync_manager.py`)
   - Notion과 Google Calendar 간 동기화
   - 원문 입력 처리 워크플로우
   - 양방향 변경 감지 및 동기화 (향후)

## 사용 방법

### 설치

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 환경 설정

1. `.env.example`을 `.env`로 복사
2. 필요한 API 키 설정:
   - `NOTION_API_KEY`: https://www.notion.so/my-integrations
   - `ANTHROPIC_API_KEY`: https://console.anthropic.com/
   - `GOOGLE_CREDENTIALS_FILE`: Google Calendar OAuth 인증 파일

### 명령어

#### 1. 원문 파싱 및 이벤트 생성

```bash
python main.py parse --text "교내일정 시험지 점검을 도와주셔서 오찬을 준비하였습니다. 시간과 장소는 나눌터에서 11:30~ 입니다."
```

또는 옵션과 함께:

```bash
python main.py parse --text "..." --page-id "notion_page_id"
```

#### 2. 노션 페이지를 캘린더로 동기화

```bash
python main.py sync-notion-to-calendar --page-id "notion_page_id"
```

#### 3. 노션 페이지 목록 조회

```bash
python main.py list-notion-pages
```

#### 4. 캘린더 이벤트 조회

```bash
python main.py list-calendar-events --days 30
```

#### 5. 파서 테스트

```bash
python main.py test-parser --text "test_text"
```

## Notion 데이터베이스 구조

필수 필드:

| 필드명 | 타입 | 설명 |
|--------|------|------|
| 제목 | Title | 일정 제목 |
| 날짜 | Date | 일정 날짜 범위 |
| 시간 | Rich Text | HH:MM~HH:MM 형식 |
| 장소 | Rich Text | 일정 장소 |
| 주요내용 | Rich Text | 일정 요약 |
| 참석자 | Rich Text | 참석자 이름 목록 |
| 참석기관 | Rich Text | 참석자 소속 기관 |
| 일정종류(중요도) | Multi-select | 교내/개인/가족 |
| 비고 및 원문 | Rich Text | 원본 입력 텍스트 |
| 추가 요구사항(GPT) | Rich Text | 추가 요청사항 |
| 파일첨부 | File | 관련 파일 첨부 |
| 캘린더 이벤트 ID | Rich Text | 구글 캘린더 이벤트 ID (추적용) |
| 동기화 상태 | Select | 동기화 상태 추적 (향후) |

## Claude Haiku 파싱 규칙

### 입력

- 텍스트 또는 이미지 파일
- OCR 자동 처리
- 원문 기반 정보 추출

### 출력 (JSON)

```json
{
  "제목": "시험지 점검에 대한 감사 오찬",
  "날짜": "2026.04.21. (화)",
  "시간": "11:30~23:59",
  "장소": ["나눌터"],
  "주요내용": "시험지 점검을 도와준 것에 대한 감사 표시로 오찬을 준비하였습니다.",
  "참석자": ["N/A"],
  "참석기관": ["N/A"],
  "종류": ["교내"],
  "Start Time": "2026-04-21T11:30:00+09:00",
  "End Time": "2026-04-21T23:59:00+09:00",
  "Include Time": true
}
```

## Google Calendar 매핑

모든 일정은 **윤윤남매 가족일정** 캘린더(`iothomepyu@gmail.com`)로 통합됩니다.

## 향후 기능

- [ ] Notion Webhook 자동 감지
- [ ] 양방향 동기화 (수정/삭제)
- [ ] 반복 일정 지원
- [ ] 참석자 초대 기능
- [ ] 다중 캘린더 지원
- [ ] UI 대시보드
- [ ] 배치 처리

## 에러 해결

### Notion API 에러

- API 키 확인
- 데이터베이스 ID 확인
- 통합 권한 확인 (Notion 설정)

### Google Calendar 에러

- OAuth 인증 파일 확인
- 캘린더 ID 확인
- API 활성화 확인 (Google Cloud)

### Claude 파싱 에러

- 입력 형식 확인
- API 키 확인
- 토큰 제한 확인

## 개발 로드맵

### Phase 1: 기본 기능 (현재)
- ✅ 텍스트 파싱
- ✅ Notion 업데이트
- ✅ Google Calendar 이벤트 생성

### Phase 2: 자동화
- [ ] Notion Webhook 통합
- [ ] 실시간 자동 동기화
- [ ] 이미지 파일 OCR 처리

### Phase 3: 양방향 동기화
- [ ] 노션 변경 감지
- [ ] 캘린더 변경 감지
- [ ] 충돌 해결 로직

### Phase 4: 고급 기능
- [ ] 반복 일정 지원
- [ ] 시간대 관리
- [ ] 참석자 초대
- [ ] 알림 설정

## 라이선스

MIT
