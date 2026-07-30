"""YouTube Data API v3 collection client."""
from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from collectors.base import BaseCollector
from utils.file_utils import save_json, utc_now

load_dotenv()


class YouTubeCollector(BaseCollector):
    """Collect videos, channels, comments, and replies with nextPageToken."""

    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY is required to run this collector.")

    def _paged(self, endpoint: str, params: dict[str, Any], max_records: int) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        token: str | None = None
        while len(records) < max_records:
            query = {**params, "key": self.api_key, "maxResults": min(50, max_records - len(records))}
            if token:
                query["pageToken"] = token
            payload = self._get(f"{self.BASE_URL}/{endpoint}", params=query)
            collected_at = utc_now()
            for item in payload.get("items", []):
                item["collected_at"] = collected_at
                records.append(item)
            token = payload.get("nextPageToken")
            if not token:
                break
        return records[:max_records]

    def collect_videos(self, query: str, max_records: int = 50) -> list[dict[str, Any]]:
        """Search IDs, then request video detail records (different quota costs)."""
        search = self._paged("search", {"part": "snippet", "q": query, "type": "video"}, max_records)
        ids = [item["id"]["videoId"] for item in search]
        return self._paged("videos", {"part": "snippet,contentDetails,statistics", "id": ",".join(ids)}, max_records)

    def collect_channels(self, channel_ids: list[str], max_records: int = 50) -> list[dict[str, Any]]:
        return self._paged("channels", {"part": "snippet,statistics", "id": ",".join(channel_ids)}, max_records)

    def collect_comments(self, video_id: str, max_records: int = 100) -> list[dict[str, Any]]:
        return self._paged("commentThreads", {"part": "snippet,replies", "videoId": video_id}, max_records)

    def collect_replies(self, parent_id: str, max_records: int = 100) -> list[dict[str, Any]]:
        return self._paged("comments", {"part": "snippet", "parentId": parent_id}, max_records)

    def persist(self, records: list[dict[str, Any]], path: Any) -> None:
        """Save raw records separately from processed output."""
        save_json({"sample": False, "items": records, "collected_at": utc_now()}, path)

