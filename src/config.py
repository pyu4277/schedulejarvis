import json
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Notion Settings
    NOTION_API_KEY: str
    NOTION_DATABASE_ID: str = "a96a3b8563e342908b2f0af8960370b7"

    # Google Calendar Settings
    GOOGLE_CALENDAR_ID: str = "iothomepyu@gmail.com"
    GOOGLE_CLIENT_ID: str = "137605297463-r6sd1nru58k79lg01mes6ggsop3n0uva.apps.googleusercontent.com"
    GOOGLE_CREDENTIALS_FILE: str = "credentials.json"

    # Claude API Settings
    CLAUDE_API_KEY: str
    CLAUDE_MODEL: str = "claude-3-5-haiku-20241022"

    # Make.com Settings (optional)
    MAKE_WEBHOOK_URL: Optional[str] = None

    # Webhook Settings
    WEBHOOK_PORT: int = 5000
    WEBHOOK_SECRET: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

def load_settings() -> Settings:
    """환경변수 및 .env 파일에서 설정 로드"""
    return Settings()

def save_config_template(config_path: str = "config.example.json"):
    """설정 파일 샘플 생성"""
    template = {
        "notion": {
            "api_key": "your-notion-api-key",
            "database_id": "a96a3b8563e342908b2f0af8960370b7"
        },
        "google_calendar": {
            "calendar_id": "iothomepyu@gmail.com",
            "client_id": "137605297463-r6sd1nru58k79lg01mes6ggsop3n0uva.apps.googleusercontent.com",
            "credentials_file": "credentials.json"
        },
        "claude": {
            "api_key": "your-claude-api-key",
            "model": "claude-3-5-haiku-20241022"
        },
        "webhook": {
            "port": 5000,
            "secret": "your-webhook-secret"
        }
    }

    Path(config_path).write_text(json.dumps(template, indent=2, ensure_ascii=False))
    print(f"✅ Config template saved to {config_path}")
