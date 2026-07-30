"""Permission-aware Meta Graph API Page collector."""
from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from collectors.base import BaseCollector
from utils.file_utils import save_json, utc_now

load_dotenv()


class MetaCollector(BaseCollector):
    """Collect only Page data authorized by the supplied access token."""

    def __init__(self, access_token: str | None = None, api_version: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.access_token = access_token or os.getenv("META_ACCESS_TOKEN")
        self.api_version = api_version or os.getenv("META_API_VERSION", "v23.0")
        if not self.access_token:
            raise ValueError("META_ACCESS_TOKEN is required to run this collector.")
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def _paged(self, path: str, fields: str, max_records: int) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        url = f"{self.base_url}/{path}"
        params: dict[str, Any] | None = {"access_token": self.access_token, "fields": fields, "limit": min(100, max_records)}
        while url and len(records) < max_records:
            payload = self._get(url, params=params)
            timestamp = utc_now()
            for item in payload.get("data", [payload] if "id" in payload else []):
                item["collected_at"] = timestamp
                records.append(item)
            url = payload.get("paging", {}).get("next")
            params = None
        return records[:max_records]

    def collect_page(self, page_id: str) -> dict[str, Any]:
        return self._paged(page_id, "id,name,category,about,website,fan_count,followers_count", 1)[0]

    def collect_page_posts(self, page_id: str, max_records: int = 50) -> list[dict[str, Any]]:
        return self._paged(f"{page_id}/posts", "id,message,created_time,permalink_url,attachments,shares", max_records)

    def collect_comments(self, post_id: str, max_records: int = 100) -> list[dict[str, Any]]:
        return self._paged(f"{post_id}/comments", "id,message,created_time,from,like_count,comment_count,parent", max_records)

    def collect_replies(self, comment_id: str, max_records: int = 100) -> list[dict[str, Any]]:
        return self._paged(f"{comment_id}/comments", "id,message,created_time,from,like_count,parent", max_records)

    def collect_insights(self, object_id: str, metrics: list[str], max_records: int = 100) -> list[dict[str, Any]]:
        """Collect insights only when the token has the required reviewed permission."""
        return self._paged(f"{object_id}/insights", ",".join(metrics), max_records)

    def persist(self, records: Any, path: Any) -> None:
        save_json({"sample": False, "items": records, "collected_at": utc_now()}, path)

