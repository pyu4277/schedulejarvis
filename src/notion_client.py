from notion_client import Client
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)


class NotionClient:
    def __init__(self, api_key: str, database_id: str):
        self.client = Client(auth=api_key)
        self.database_id = database_id

    def get_page_by_id(self, page_id: str) -> Dict[str, Any]:
        """Get page details by ID"""
        try:
            page = self.client.pages.retrieve(page_id)
            return page
        except Exception as e:
            logger.error(f"Error retrieving page {page_id}: {e}")
            raise

    def get_page_content(self, page_id: str) -> str:
        """Get page content as markdown"""
        try:
            blocks = self.client.blocks.children.list(page_id)
            content = []
            for block in blocks["results"]:
                if block["type"] == "paragraph":
                    text = block["paragraph"]["rich_text"]
                    if text:
                        content.append("".join([t["plain_text"] for t in text]))
            return "\n".join(content)
        except Exception as e:
            logger.error(f"Error retrieving page content for {page_id}: {e}")
            return ""

    def update_page_properties(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update page properties"""
        try:
            page = self.client.pages.update(page_id, properties=properties)
            logger.info(f"Updated page {page_id}")
            return page
        except Exception as e:
            logger.error(f"Error updating page {page_id}: {e}")
            raise

    def query_database(
        self,
        filter_condition: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Query database with optional filters and sorts"""
        try:
            results = self.client.databases.query(
                self.database_id, filter=filter_condition, sorts=sorts
            )
            return results.get("results", [])
        except Exception as e:
            logger.error(f"Error querying database: {e}")
            raise

    def get_all_pages(self) -> List[Dict[str, Any]]:
        """Get all pages in database"""
        try:
            results = []
            cursor = None
            while True:
                response = self.client.databases.query(
                    self.database_id, start_cursor=cursor
                )
                results.extend(response.get("results", []))
                if not response.get("has_more"):
                    break
                cursor = response.get("next_cursor")
            return results
        except Exception as e:
            logger.error(f"Error getting all pages: {e}")
            raise

    def get_property_value(self, page: Dict[str, Any], property_name: str) -> Any:
        """Extract property value from page"""
        try:
            if "properties" not in page:
                return None

            properties = page["properties"]
            if property_name not in properties:
                return None

            prop = properties[property_name]
            prop_type = prop.get("type")

            if prop_type == "title":
                return "".join([t["plain_text"] for t in prop.get("title", [])])
            elif prop_type == "rich_text":
                return "".join([t["plain_text"] for t in prop.get("rich_text", [])])
            elif prop_type == "date":
                date_obj = prop.get("date")
                if date_obj:
                    return date_obj
                return None
            elif prop_type == "multi_select":
                return [item["name"] for item in prop.get("multi_select", [])]
            elif prop_type == "select":
                select_obj = prop.get("select")
                return select_obj["name"] if select_obj else None
            elif prop_type == "relation":
                return [item["id"] for item in prop.get("relation", [])]
            elif prop_type == "people":
                return [item["name"] for item in prop.get("people", [])]
            elif prop_type == "files":
                return [
                    {
                        "name": f.get("name"),
                        "url": f.get("file", {}).get("url") or f.get("external", {}).get("url"),
                    }
                    for f in prop.get("files", [])
                ]
            else:
                return prop.get(prop_type)
        except Exception as e:
            logger.warning(f"Error extracting property {property_name}: {e}")
            return None

    def create_property_dict(
        self, properties_map: Dict[str, Any], field_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """Create Notion properties dictionary from data"""
        result = {}

        for key, value in properties_map.items():
            if key not in field_mapping:
                continue

            field_name = field_mapping[key]

            if value is None or value == "N/A":
                continue

            if key == "title":
                result[field_name] = {"title": [{"text": {"content": str(value)}}]}
            elif key == "date":
                if isinstance(value, dict):
                    result[field_name] = {"date": value}
                else:
                    result[field_name] = {"date": {"start": str(value)}}
            elif key == "location":
                if isinstance(value, list):
                    content = ", ".join(value)
                else:
                    content = str(value)
                result[field_name] = {"rich_text": [{"text": {"content": content}}]}
            elif key == "content":
                result[field_name] = {"rich_text": [{"text": {"content": str(value)}}]}
            elif key == "attendees":
                if isinstance(value, list):
                    content = ", ".join(value)
                else:
                    content = str(value)
                result[field_name] = {"rich_text": [{"text": {"content": content}}]}
            elif key == "organization":
                if isinstance(value, list):
                    content = ", ".join(value)
                else:
                    content = str(value)
                result[field_name] = {"rich_text": [{"text": {"content": content}}]}
            elif key == "category":
                if isinstance(value, list):
                    result[field_name] = {
                        "multi_select": [{"name": v} for v in value]
                    }
                else:
                    result[field_name] = {"select": {"name": str(value)}}
            elif key == "time":
                result[field_name] = {"rich_text": [{"text": {"content": str(value)}}]}
            elif key == "calendar_event_id":
                result[field_name] = {"rich_text": [{"text": {"content": str(value)}}]}

        return result
