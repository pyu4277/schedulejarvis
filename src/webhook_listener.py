import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from src.sync_manager import SyncManager
from src.notion_client import NotionClient
from src.google_calendar_client import GoogleCalendarClient
import config

logger = logging.getLogger(__name__)


class WebhookListener:
    def __init__(self, app: Flask = None):
        self.app = app or Flask(__name__)
        self.setup_routes()

        # Initialize sync components
        try:
            self.notion = NotionClient(config.NOTION_API_KEY, config.NOTION_DATABASE_ID)
            self.calendar = GoogleCalendarClient(config.TARGET_CALENDAR_ID)
            self.sync_manager = SyncManager(self.notion, self.calendar)
            logger.info("Sync components initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing sync components: {e}")
            raise

    def setup_routes(self):
        """Setup Flask routes"""
        @self.app.route("/health", methods=["GET"])
        def health():
            return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})

        @self.app.route("/webhook/notion", methods=["POST"])
        def notion_webhook():
            """Handle Notion webhook events"""
            try:
                # Verify webhook signature (optional but recommended)
                signature = request.headers.get("X-Notion-Signature")
                # TODO: Implement signature verification

                data = request.get_json()
                logger.info(f"Received Notion webhook: {json.dumps(data, indent=2)}")

                # Process the webhook
                result = self._handle_notion_webhook(data)

                return jsonify({"success": True, "result": result}), 200

            except Exception as e:
                logger.error(f"Error handling Notion webhook: {e}")
                return jsonify({"success": False, "error": str(e)}), 400

        @self.app.route("/webhook/notion/edit", methods=["POST"])
        def notion_edit_webhook():
            """Handle Notion page edit events"""
            try:
                data = request.get_json()
                logger.info(f"Received Notion edit webhook: {json.dumps(data, indent=2)}")

                result = self._handle_notion_edit_webhook(data)

                return jsonify({"success": True, "result": result}), 200

            except Exception as e:
                logger.error(f"Error handling Notion edit webhook: {e}")
                return jsonify({"success": False, "error": str(e)}), 400

        @self.app.route("/api/schedule", methods=["POST"])
        def api_schedule():
            """API endpoint for syncing already-parsed schedule data"""
            try:
                payload = request.get_json()

                if not payload:
                    return (
                        jsonify({"error": "No JSON payload provided"}),
                        400,
                    )

                # Expected fields from parsed data
                title = payload.get("제목")
                page_id = payload.get("page_id")

                if not title:
                    return (
                        jsonify({"error": "Missing required field: 제목 (title)"}),
                        400,
                    )

                logger.info(f"API schedule sync request: title={title}, page_id={page_id}")

                result = self.sync_manager.process_parsed_data(payload, page_id)

                return (
                    jsonify({"success": True, "data": result}),
                    200,
                )

            except Exception as e:
                logger.error(f"Error in API schedule sync: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

    def _handle_notion_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Notion creation webhook events - stores raw text for parsing by external AI"""
        try:
            page_id = data.get("id")
            properties_value = data.get("properties_value", {})

            if not page_id:
                logger.warning("No page ID in webhook data")
                return {"status": "skipped", "reason": "No page ID"}

            # Extract raw text and additional requirements
            raw_text = properties_value.get("비고 및 원문", "")
            additional_req = properties_value.get("추가 요구사항(GPT)", "")

            text_content = raw_text or additional_req

            if not text_content:
                logger.info(f"No text provided for page {page_id}")
                return {"status": "skipped", "reason": "No text provided"}

            logger.info(f"Notion webhook: page {page_id} received text: {text_content[:50]}...")
            logger.info(f"Note: External AI should parse this text and send parsed data to /api/schedule endpoint")

            return {
                "status": "received",
                "page_id": page_id,
                "message": "Raw text received. Send parsed JSON data to /api/schedule endpoint.",
                "raw_text": text_content,
            }

        except Exception as e:
            logger.error(f"Error handling Notion webhook: {e}")
            raise

    def _handle_notion_edit_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Notion page edit events (for two-way sync)"""
        try:
            page_id = data.get("id")

            if not page_id:
                logger.warning("No page ID in edit webhook data")
                return {"status": "skipped", "reason": "No page ID"}

            logger.info(f"Syncing edited page {page_id} to calendar...")

            # Sync the page to calendar
            result = self.sync_manager.sync_notion_to_calendar(page_id)

            return {
                "status": "success",
                "page_id": page_id,
                "calendar_event_id": result.get("calendar_event_id"),
            }

        except Exception as e:
            logger.error(f"Error handling edit webhook: {e}")
            raise

    def run(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
        """Run the Flask application"""
        logger.info(f"Starting webhook listener on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def create_app() -> Flask:
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config["JSON_AS_ASCII"] = False  # Support for Korean characters
    return app
