from anthropic import Anthropic
from typing import Dict, Any, Optional
import json
import logging
import base64
from pathlib import Path

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """너를 만든 목적은 원문을 보고 일정을 정리하여 요약하고 등록해주는 용도야.

- 텍스트만 입력되면 텍스트를 기반으로, 이미지 파일이 포함된다면 일정을 만드는 이미지라는 점을 염두하고 OCR을 수행하여 텍스트로 변환하여 진행해줘.

- 이전 대화 내용에 영향을 받지 말고, 항상 현재 주어진 원문에서만 정보를 추출해줘. 특히 날짜나 시간은 잘못된 과거 날짜(예: 2026.11.05.)는 추출하지 말고 모르겠으면 주어진 원문을 기준으로만 작성해줘.

결과는 내가 확인하지 않고 API를 통해 파싱하여 다른 플랫폼에 원하는 값들을 알맞게 데이터를 전달해야 하니 언제나 항상 아래 조건에 맞게 출력해줘.

1. 주요내용은 회의나 일정의 목적 및 핵심을 요약해서 자연스러운 1~2 문장 사이로 작성해줘.

2. 가장 중요한 부분은 제목이야. 가장 중요한 만큼 모든 내용을 정리하고 마지막에 생성해줘. 제목은 원문에 제목이 있어도 무시하고 '1. 주요내용' 부분만을 다시 분석하여 주제의 핵심을 파악하고 일정 등록이라는 목적에 알맞게 제목을 만들어줘.

3. 내용을 분석해서 일정과 장소를 찾아서 다음과 같은 형식으로 각각 출력해줘(연도나 일자가 없다면 올해연도를 참고하여 오늘날자를 기준으로 없는 연도나 월을 유추해서 작성해줘):
- 날짜: 시작일과 종료일이 다를 경우 'YYYY.MM.DD. (요일)' 형식으로 출력, 동일한 경우도 'YYYY.MM.DD. (요일)' 형식으로 출력
- 시간: HH:MM~HH:MM (끝 시간이 없으면 23:59)
- 장소: 문자열 또는 배열

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

8. 출력은 항상 순수 JSON 객체 형식으로 해줘. 코드블럭도 넣지 말고, 부가설명도 하지 말고, JSON만 반환해줘.

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

10. 모든 key는 누락 없이 항상 동일한 순서로 출력해줘. 순서가 바뀌거나 빠지면 안돼."""

class ScheduleParser:
    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022"):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.temperature = 0.2
        self.top_p = 0.9

    def parse_schedule(self, text: Optional[str] = None, image_path: Optional[str] = None) -> Dict[str, Any]:
        """원문 또는 이미지를 파싱하여 일정 정보 추출"""
        if not text and not image_path:
            raise ValueError("text 또는 image_path 중 하나는 필수입니다.")

        content = []

        # 텍스트 추가
        if text:
            content.append({
                "type": "text",
                "text": text
            })

        # 이미지 추가
        if image_path:
            content.extend(self._prepare_image(image_path))

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": content
                }],
                temperature=self.temperature,
                top_p=self.top_p
            )

            # 응답에서 JSON 추출
            response_text = response.content[0].text.strip()

            # JSON 파싱
            parsed = json.loads(response_text)
            logger.info("✅ Schedule parsed successfully")
            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response_text}")
            raise ValueError(f"Invalid JSON response from Claude: {e}")
        except Exception as e:
            logger.error(f"Failed to parse schedule: {e}")
            raise

    def _prepare_image(self, image_path: str) -> list:
        """이미지 파일을 Claude API 형식으로 변환"""
        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # 지원하는 이미지 형식
        supported_formats = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        if path.suffix.lower() not in supported_formats:
            raise ValueError(f"Unsupported image format: {path.suffix}")

        # 이미지 타입 결정
        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        media_type = media_type_map[path.suffix.lower()]

        # 이미지 읽기 및 Base64 인코딩
        with open(path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        return [{
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": image_data
            }
        }]

    def validate_parsed_data(self, data: Dict[str, Any]) -> bool:
        """파싱된 데이터 유효성 검사"""
        required_keys = {
            "제목", "날짜", "시간", "장소", "주요내용",
            "참석자", "참석기관", "종류", "Start Time", "End Time", "Include Time"
        }

        if not isinstance(data, dict):
            logger.error("Parsed data is not a dictionary")
            return False

        missing_keys = required_keys - set(data.keys())
        if missing_keys:
            logger.error(f"Missing keys: {missing_keys}")
            return False

        return True
