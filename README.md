# Schedule Jarvis

Notion과 Google Calendar를 양방향 동기화하여 일정을 자동으로 관리하는 시스템입니다.
Claude Haiku를 사용해 원문을 자동 분석하고, 모든 일정을 가족 캘린더에 통합합니다.

## 주요 기능

### 1단계: 파싱 (현재)
- **입력**: Notion "비고 및 원문" 또는 "추가 요구사항(GPT)" 필드
- **처리**: Claude Haiku 자동 분석 (온도: 0.2, Top P: 0.9)
- **출력**: 구조화된 일정 데이터 (JSON)

### 2단계: 자동화 (진행 중)
- **Webhook**: Notion 필드 변경 감지 → 자동 트리거
- **동기화**: 파싱 데이터 → Notion 필드 자동 채우기
- **캘린더**: Google Calendar 자동 이벤트 생성

### 3단계: 양방향 동기화 (계획)
- 노션 수정 → 캘린더 수정
- 캘린더 삭제 → 노션 삭제
- 충돌 해결 로직

## 아키텍처

```
┌─────────────────┐
│   사용자 입력    │
│  (원문/파일)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Claude Parser   │ ◄── Haiku 모델 (온도 0.2, Top P 0.9)
│  (JSON 파싱)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐    ┌──────────────────┐
│  Notion Update   │───▶│  Google Calendar │
│  (필드 채우기)   │    │  (이벤트 생성)    │
└─────────────────┘    └──────────────────┘
         ▲                      │
         │                      ▼
         └──────────────────────┘
          (양방향 동기화)
```

## 빠른 시작

### 1. 설치

```bash
# 저장소 클론
git clone https://github.com/pyu4277/schedulejarvis.git
cd schedulejarvis

# 가상 환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. API 키 설정

```bash
# .env 파일 생성
cp .env.example .env

# 필수 API 키 추가
# - NOTION_API_KEY (https://www.notion.so/my-integrations)
# - ANTHROPIC_API_KEY (https://console.anthropic.com/)
# - Google Calendar 인증 (credentials.json 또는 환경변수)
```

### 3. 사용 방법

#### **방법 1: API 서버 (권장)**

```bash
# Webhook 서버 시작
python webhook_server.py --host 0.0.0.0 --port 5000

# 다른 터미널에서 파싱된 일정 데이터 전송
# (상위 AI가 미리 파싱한 구조화된 JSON 데이터)
curl -X POST http://localhost:5000/api/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "제목": "교내일정 회의",
    "시간": "14:00~15:00",
    "장소": ["회의실"],
    "주요내용": "팀 회의",
    "참석자": ["팀원들"],
    "참석기관": ["부서"],
    "종류": ["교내"],
    "page_id": "optional-page-id"
  }'
```

#### **방법 2: Notion Webhook (원문 수신)**

1. Notion 데이터베이스에서 Webhook 구독 설정
2. Webhook URL: `https://your-server.com/webhook/notion`
3. "비고 및 원문" 필드 입력 시 원문이 서버로 전달됨
4. 서버는 원문을 로깅하고 외부 AI의 파싱을 기다림
5. 파싱 완료 후 `/api/schedule` 엔드포인트로 구조화된 데이터 전송

### API 엔드포인트

```bash
# 1. Webhook 서버 시작
python webhook_server.py --debug

# 2. 구조화된 일정 데이터 동기화
curl -X POST http://localhost:5000/api/schedule \
  -H "Content-Type: application/json" \
  -d '{"제목": "회의", "시간": "14:00~15:00"}'

# 3. 서버 상태 확인
curl http://localhost:5000/health

# 4. Notion Webhook (자동 감지)
# Notion 데이터베이스 설정에서 구독
```

## Notion 데이터베이스 필드

### 주요 필드 (Make.com 기준)

| 필드명 | 타입 | 용도 |
|--------|------|------|
| **주제** | Title | 일정 제목 (자동 생성) |
| **비고 및 원문** | Rich Text | **입력 필드** - 원본 텍스트 |
| **추가 요구사항(GPT)** | Rich Text | **입력 필드** - 추가 지시사항 |
| **파일 첨부** | Files | **입력 필드** - 첨부 파일 |
| **일시** | Date | 일정 날짜 범위 (자동 채우기) |
| **시간** | Rich Text | 시간 (자동 채우기) |
| **일시/장소** | Rich Text | 장소 정보 (자동 채우기) |
| **주요내용** | Rich Text | 요약 (자동 채우기) |
| **참석자** | Relation | 참석자 (자동 추출) |
| **참석기관** | Rich Text | 소속 기관 (자동 추출) |
| **일정종류(중요도)** | Multi-select | 분류 (자동 추출) |
| **구글ID** | Rich Text | Google Calendar Event ID (자동) |
| **생성(setting)** | Checkbox | 캘린더 생성 완료 (자동) |
| **GPT 요약 결과** | Rich Text | Claude 분석 결과 (자동) |

### 워크플로우

```
사용자 입력 ("비고 및 원문" 입력)
    ↓
웹훅 감지 (또는 수동 트리거)
    ↓
Claude Haiku 분석 (JSON 생성)
    ↓
Notion 필드 자동 채우기
    ↓
Google Calendar 이벤트 생성
    ↓
"구글ID" & "생성(setting)" 업데이트 완료
```

## Claude Haiku 파싱 포맷

### 입력 예시

```
교내일정: 시험지 점검을 도와주셔서 오찬을 준비했습니다. 
시간과 장소는 나눌터에서 11:30~ 입니다.
```

### 출력 (JSON)

```json
{
  "제목": "시험지 점검에 대한 감사 오찬",
  "날짜": "2026.04.21. (월)",
  "시간": "11:30~23:59",
  "장소": ["나눌터"],
  "주요내용": "시험지 점검을 도와주신 것에 감사드리는 오찬",
  "참석자": ["N/A"],
  "참석기관": ["N/A"],
  "종류": ["교내"],
  "Start Time": "2026-04-21T11:30:00+09:00",
  "End Time": "2026-04-21T23:59:00+09:00",
  "Include Time": true
}
```

## Google Calendar 설정

- **대상 캘린더**: 윤윤남매 가족일정 (`iothomepyu@gmail.com`)
- **인증 방식**: 
  - OAuth 2.0 (credentials.json)
  - 또는 Refresh Token (환경변수)

## Webhook 서버 배포

### 로컬 테스트

```bash
python webhook_server.py --debug
```

### 프로덕션 배포 (Gunicorn)

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "src.webhook_listener:create_app()"
```

### Docker 배포 (예정)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "webhook_server.py"]
```

## 개발 로드맵

### ✅ 완료
- CLI 인터페이스
- Claude Haiku 파싱
- Notion 필드 자동 채우기
- Google Calendar 이벤트 생성
- Webhook 리스너 (API 방식)

### 🔄 진행 중
- Notion Webhook 자동 감지
- 필드명 매핑 최종화
- Google Calendar 인증 통합

### 📋 계획 중
- 양방향 동기화 (수정/삭제)
- 이미지 OCR 처리
- 반복 일정 지원
- 참석자 자동 초대
- 웹 UI 대시보드
- Docker 컨테이너

## 문제 해결

### API 키 관련 오류

```bash
# .env 파일 확인
cat .env

# 필수 키 존재 확인
- NOTION_API_KEY ✓
- ANTHROPIC_API_KEY ✓
- GOOGLE_CLIENT_ID 또는 GOOGLE_CREDENTIALS_FILE ✓
```

### 권한 오류

```
Notion: 통합 권한 확인 (https://www.notion.so/my-integrations)
Google: Google Cloud Console에서 Calendar API 활성화
Anthropic: 계정의 API 사용량 확인
```

## 기술 스택

- **Backend**: Python 3.11+
- **LLM**: Claude Haiku (Temperature: 0.2, Top P: 0.9)
- **Notion**: Notion API v1
- **Google Calendar**: Google Calendar API v3
- **Web Framework**: Flask 3.0
- **Deployment**: Gunicorn, Docker (계획)

## 라이선스

MIT

## 문의

이슈 및 피드백은 GitHub Issues에 등록해주세요.
