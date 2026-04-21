from notion_client import Client
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class NotionClient:
    def __init__(self, api_key: str, database_id: str):
        self.client = Client(auth=api_key)
        self.database_id = database_id

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """페이지 정보 조회"""
        try:
            return self.client.pages.retrieve(page_id)
        except Exception as e:
            logger.error(f"Failed to retrieve page {page_id}: {e}")
            raise

    def get_properties(self, page_id: str) -> Dict[str, Any]:
        """페이지의 모든 속성 조회"""
        try:
            page = self.get_page(page_id)
            return page.get("properties", {})
        except Exception as e:
            logger.error(f"Failed to get properties for page {page_id}: {e}")
            raise

    def get_property_value(self, page_id: str, property_name: str) -> Any:
        """특정 속성값 조회"""
        try:
            properties = self.get_properties(page_id)
            prop = properties.get(property_name, {})
            return self._extract_value(prop)
        except Exception as e:
            logger.error(f"Failed to get property {property_name} for page {page_id}: {e}")
            raise

    def update_properties(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """페이지 속성 업데이트"""
        try:
            return self.client.pages.update(page_id, properties=properties)
        except Exception as e:
            logger.error(f"Failed to update properties for page {page_id}: {e}")
            raise

    def query_database(self, filter_obj: Optional[Dict] = None, sorts: Optional[List] = None) -> List[Dict]:
        """데이터베이스 쿼리"""
        try:
            results = []
            has_more = True
            start_cursor = None

            while has_more:
                response = self.client.databases.query(
                    self.database_id,
                    filter=filter_obj,
                    sorts=sorts,
                    start_cursor=start_cursor
                )
                results.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")

            return results
        except Exception as e:
            logger.error(f"Failed to query database {self.database_id}: {e}")
            raise

    def create_page(self, properties: Dict[str, Any], parent_database: Optional[str] = None) -> Dict[str, Any]:
        """새 페이지 생성"""
        try:
            parent = {"database_id": parent_database or self.database_id}
            return self.client.pages.create(parent=parent, properties=properties)
        except Exception as e:
            logger.error(f"Failed to create page: {e}")
            raise

    def get_database_schema(self) -> Dict[str, Any]:
        """데이터베이스 스키마 조회"""
        try:
            db = self.client.databases.retrieve(self.database_id)
            return db.get("properties", {})
        except Exception as e:
            logger.error(f"Failed to retrieve database schema: {e}")
            raise

    def _extract_value(self, prop: Dict[str, Any]) -> Any:
        """Notion 속성에서 값 추출"""
        prop_type = prop.get("type")

        if prop_type == "title":
            return self._extract_text(prop.get("title", []))
        elif prop_type == "rich_text":
            return self._extract_text(prop.get("rich_text", []))
        elif prop_type == "text":
            return self._extract_text(prop.get("text", []))
        elif prop_type == "select":
            return prop.get("select", {}).get("name")
        elif prop_type == "multi_select":
            return [s.get("name") for s in prop.get("multi_select", [])]
        elif prop_type == "date":
            date_obj = prop.get("date", {})
            return {
                "start": date_obj.get("start"),
                "end": date_obj.get("end")
            }
        elif prop_type == "checkbox":
            return prop.get("checkbox", False)
        elif prop_type == "people":
            return [p.get("name") for p in prop.get("people", [])]
        elif prop_type == "files":
            return [f.get("name") for f in prop.get("files", [])]
        else:
            return None

    def _extract_text(self, text_arr: List[Dict]) -> str:
        """텍스트 배열에서 텍스트 추출"""
        return "".join([item.get("plain_text", "") for item in text_arr])

    def set_property(self, page_id: str, property_name: str, value: Any) -> None:
        """단일 속성 설정"""
        properties = self._build_properties({property_name: value})
        self.update_properties(page_id, properties)

    def _build_properties(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """파이썬 딕셔너리를 Notion API 형식으로 변환"""
        notion_props = {}

        for key, value in data.items():
            if value is None:
                continue

            if isinstance(value, str):
                notion_props[key] = {
                    "rich_text": [{"text": {"content": value}}]
                }
            elif isinstance(value, bool):
                notion_props[key] = {"checkbox": value}
            elif isinstance(value, list):
                notion_props[key] = {
                    "multi_select": [{"name": v} for v in value if isinstance(v, str)]
                }
            elif isinstance(value, dict) and "start" in value:
                # Date property
                notion_props[key] = {"date": {k: v for k, v in value.items() if v}}
            elif isinstance(value, dict) and "name" in value:
                # Select property
                notion_props[key] = {"select": {"name": value.get("name")}}

        return notion_props
