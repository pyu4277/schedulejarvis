import json
import logging
from typing import Dict, Any, Optional
from anthropic import Anthropic
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class ClaudeParser:
    def __init__(self, api_key: str):
        self.client = Anthropic()
        self.api_key = api_key

    def parse_schedule(self, text: str, image_data: Optional[bytes] = None) -> Dict[str, Any]:
        """Parse schedule from text or image using Claude Haiku"""
        try:
            prompt = self._build_parser_prompt(text)

            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                temperature=0.2,
                top_p=0.9,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text

            parsed_data = json.loads(response_text)

            parsed_data = self._validate_parsed_data(parsed_data)

            return parsed_data

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from Claude response: {e}")
            logger.error(f"Response text: {response_text}")
            raise
        except Exception as e:
            logger.error(f"Error parsing schedule: {e}")
            raise

    def _build_parser_prompt(self, text: str) -> str:
        """Build the parser prompt based on user instructions"""
        today = datetime.now()
        today_str = today.strftime("%Y.%m.%d.")

        prompt = f"""너를 만든 목적은 원문을 보고 일정을 정리하여 요약하고 등록해주는 용도야.

- 텍스트만 입력되면 텍스트를 기반으로, 이미지 파일이 포함된다면 일정을 만드는 이미지라는 점을 염두하고 OCR을 수행하여 텍스트로 변환하여 진행해줘.

- 이전 대화 내용에 영향을 받지 말고, 항상 현재 주어진 원문에서만 정보를 추출해줘. 특히 날짜나 시간은 잘못된 과거 날짜(예: 2026.11.05.)는 추출하지 말고 모르겠으면 주어진 원문을 기준으로만 작성해줘.

결과는 내가 확인하지 않고 API를 통해 파싱하여 다른 플랫폼에 원하는 값들을 알맞게 데이터를 전달해야 하니 언제나 항상 아래 조건에 맞게 출력해줘.

1. 주요내용은 회의나 일정의 목적 및 핵심을 요약해서 자연스러운 1~2 문장 사이로 작성해줘.

2. 가장 중요한 부분은 제목이야. 가장 중요한 만큼 모든 내용을 정리하고 마지막에 생성해줘. 제목은 원문에 제목이 있어도 무시하고 '1. 주요내용' 부분만을 다시 분석하여 주제의 핵심을 파악하고 일정 등록이라는 목적에 알맞게 제목을 만들어줘.(예를 들어 시험지 점검을 도와주셔서 오찬을 준비하였습니다. 시간과 장소는 나눌터에서 11:30~ 입니다. 라고 있으면 '나눌터에서 점심약속'이 제목이 아니고 왜 오찬을 준비하였는지에 대한 목적인 '시험지 점검에 대한 감사 오찬'이 제목이 되는거야.)

2. 내용을 분석해서 일정과 장소를 찾아서 다음과 같은 형식으로 각각 출력해줘(연도나 일자가 없다면 올해연도를 참고하여 오늘날자({today_str})를 기준으로 없는 연도나 월을 유추해서 작성해줘):
- 날짜: 시작일과 종료일이 다를 경우 'YYYY.MM.DD. (요일) ~ YYYY.MM.DD. (요일)' 형식으로 출력
        동일한 경우 'YYYY.MM.DD. (요일)' 형식으로 출력
- 시간: HH:MM~HH:MM (끝 시간이 없으면 23:59)
- 장소: 문자열
정보가 없는 항목은 반드시 'N/A'로 명시해줘.

4. 참석자는 이름만 리스트로 추출해줘. 없으면 'N/A'로 명시해줘.

5. 참석기관은 참석자의 참석기관이야. 행사진행장소가 아니니까 이점 유의해줘. 마찬가지로 기관명들만 리스트로 추출해줘. 없으면 'N/A'로 명시해줘.

6. 일정 종류(중요도) 정보를 분석해서 다음 중 해당하는 모든 항목들을 배열로 추출해줘:
- 교내
- 개인
- 가족
해당 키워드는 보통 원문의 시작 부분(예: '교내일정' 또는 '교내 및 개인 일정' 등)에 등장하니 잘 파악해서 '종류' 배열에 넣어줘. 복수 선택도 가능하니까 복수 일정인지 잘 분석해줘.

7. 또한 Make의 날짜 입력에 활용할 수 있도록 아래 3개의 항목을 추가로 JSON에 포함해줘:
- Start Time: ISO 8601 형식(예: 2026-07-15T13:00:00+09:00)
- End Time: ISO 8601 형식(예: 2026-07-15T15:00:00+09:00). 끝 시간이 없으면 23:59로 설정해줘.
- Include Time: 시간 정보가 포함되었으면 true, 아니면 false

8. 출력은 항상 **순수 JSON 객체 형식**으로 해줘. **코드블럭도 넣지 말고**, 부가설명도 하지 말고, JSON만 반환해줘.

9. JSON은 다음 key를 꼭 포함해야 해:
- 제목 (string)
- 날짜 (string)
- 시간 (string)
- 장소 (string[] 또는 "N/A")
- 주요내용 (string)
- 참석자 (string[] 또는 "N/A")
- 참석기관 (string[] 또는 "N/A")
- 종류 (string[])
- Start Time (string)
- End Time (string)
- Include Time (boolean)

10. 모든 key는 누락 없이 항상 동일한 순서로 출력해줘. 순서가 바뀌거나 빠지면 안돼.

다음은 분석할 원문이야:

{text}
"""
        return prompt

    def _validate_parsed_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize parsed data"""
        required_keys = [
            "제목",
            "날짜",
            "시간",
            "장소",
            "주요내용",
            "참석자",
            "참석기관",
            "종류",
            "Start Time",
            "End Time",
            "Include Time",
        ]

        for key in required_keys:
            if key not in data:
                logger.warning(f"Missing key in parsed data: {key}")

        # Normalize list fields
        for key in ["장소", "참석자", "참석기관", "종류"]:
            if key in data:
                if isinstance(data[key], str):
                    if data[key] != "N/A":
                        data[key] = [data[key]]
                    else:
                        data[key] = "N/A"
                elif isinstance(data[key], list):
                    data[key] = [str(item) for item in data[key]]

        return data

    def parse_date_range(self, date_str: str) -> tuple:
        """Parse date range string and return (start_date, end_date)"""
        if date_str == "N/A":
            return (None, None)

        try:
            if "~" in date_str:
                parts = date_str.split("~")
                start_str = parts[0].strip()
                end_str = parts[1].strip()

                start_date = self._parse_single_date(start_str)
                end_date = self._parse_single_date(end_str)

                return (start_date, end_date)
            else:
                date = self._parse_single_date(date_str)
                return (date, date)
        except Exception as e:
            logger.error(f"Error parsing date range: {e}")
            return (None, None)

    def _parse_single_date(self, date_str: str) -> datetime:
        """Parse a single date string"""
        date_str = date_str.strip()

        # Remove day of week if present (e.g., "2026.07.15. (화)" -> "2026.07.15.")
        date_str = re.sub(r"\s*\([^)]+\)\s*", "", date_str)
        date_str = date_str.strip()

        # Try different date formats
        formats = [
            "%Y.%m.%d.",
            "%Y-%m-%d",
            "%Y/%m/%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        raise ValueError(f"Unable to parse date: {date_str}")

    def parse_time_range(self, time_str: str) -> tuple:
        """Parse time range string and return (start_time, end_time)"""
        if time_str == "N/A":
            return ("00:00", "23:59")

        try:
            time_str = time_str.strip()

            if "~" in time_str:
                parts = time_str.split("~")
                start_time = parts[0].strip()
                end_time = parts[1].strip() if len(parts) > 1 else "23:59"
            else:
                start_time = time_str
                end_time = "23:59"

            # Validate time format
            start_time = self._validate_time(start_time)
            end_time = self._validate_time(end_time)

            return (start_time, end_time)
        except Exception as e:
            logger.error(f"Error parsing time range: {e}")
            return ("00:00", "23:59")

    def _validate_time(self, time_str: str) -> str:
        """Validate and format time string"""
        time_str = time_str.strip()

        # Try to parse HH:MM format
        if ":" in time_str:
            parts = time_str.split(":")
            if len(parts) == 2:
                try:
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    return f"{hours:02d}:{minutes:02d}"
                except ValueError:
                    pass

        # If parsing fails, return 00:00 or 23:59
        return "00:00"
