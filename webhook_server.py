#!/usr/bin/env python3
"""
Schedule Jarvis Webhook Server

사용 방법:
    python webhook_server.py --host 0.0.0.0 --port 5000
    python webhook_server.py --debug  # 개발 모드

환경 설정:
    - PORT: 포트 번호 (기본값: 5000)
    - HOST: 바인딩 주소 (기본값: 0.0.0.0)
    - DEBUG: 디버그 모드 (true/false)
"""

import click
import logging
import os
from src.webhook_listener import WebhookListener, create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", default="0.0.0.0", help="Server host")
@click.option("--port", default=5000, type=int, help="Server port")
@click.option("--debug", is_flag=True, help="Enable debug mode")
def run_server(host: str, port: int, debug: bool):
    """Run Schedule Jarvis Webhook Server"""
    try:
        app = create_app()
        listener = WebhookListener(app)

        click.echo(f"""
╔════════════════════════════════════════╗
║    Schedule Jarvis Webhook Server     ║
╚════════════════════════════════════════╝

📍 Server Information:
   - Host: {host}
   - Port: {port}
   - Debug: {debug}

🔗 Endpoints:
   - Health Check: http://{host}:{port}/health
   - Notion Webhook: POST http://{host}:{port}/webhook/notion
   - Edit Webhook: POST http://{host}:{port}/webhook/notion/edit
   - API Parse: POST http://{host}:{port}/api/parse

📝 Example Request (cURL):
   curl -X POST http://{host}:{port}/api/parse \\
     -H "Content-Type: application/json" \\
     -d '{{"text": "교내일정: 회의가 11:00에 있습니다."}}'

⚙️  Configuration:
   - Check .env file for API keys
   - Notion API Key: {'✓' if os.getenv('NOTION_API_KEY') else '✗'}
   - Anthropic API Key: {'✓' if os.getenv('ANTHROPIC_API_KEY') else '✗'}
   - Google Calendar: {'✓' if os.getenv('GOOGLE_CREDENTIALS_FILE') or os.getenv('GOOGLE_REFRESH_TOKEN') else '✗'}

Press Ctrl+C to stop the server.
""")

        listener.run(host=host, port=port, debug=debug)

    except Exception as e:
        click.echo(f"❌ Error starting webhook server: {e}", err=True)
        logger.exception("Webhook server error")
        exit(1)


if __name__ == "__main__":
    run_server()
