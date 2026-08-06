"""Offline YouTube Data API v3 collection pipeline.

This module is never imported by Streamlit. It writes complete API responses to
``data/raw/youtube`` for later, offline processing.
"""
from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import RAW_DIR
from utils.file_utils import save_json
from utils.logging_utils import get_logger

DEFAULT_QUERY = "artificial intelligence education"
logger = get_logger(__name__)


def utc_now() -> str:
    """Return a UTC ISO-8601 timestamp."""
    return datetime.now(timezone.utc).isoformat()


class YouTubeCollector:
    """Collect videos, channels, comment threads, replies, and run metadata."""

    def __init__(self, api_key: str | None = None, max_retries: int = 3) -> None:
        load_dotenv()
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "YOUTUBE_API_KEY is missing. Copy .env.example to .env and add your YouTube API key."
            )
        self.max_retries = max_retries
        self.youtube = build("youtube", "v3", developerKey=self.api_key, cache_discovery=False)
        self.failed_requests: list[dict[str, str]] = []

    @staticmethod
    def _http_reason(error: HttpError) -> str:
        """Extract a non-secret API error reason suitable for logs and metadata."""
        try:
            details = error.error_details
            if details:
                return str(details[0].get("reason", "http_error"))
        except (AttributeError, IndexError, TypeError):
            pass
        return f"http_{getattr(error.resp, 'status', 'error')}"

    def _execute(self, request_factory: Callable[[], Any], operation: str) -> dict[str, Any]:
        """Execute a request with bounded exponential backoff for 429 and 5xx."""
        for attempt in range(self.max_retries + 1):
            try:
                return request_factory().execute(num_retries=0)
            except HttpError as error:
                status = int(getattr(error.resp, "status", 0))
                reason = self._http_reason(error)
                retryable = status == 429 or 500 <= status < 600
                if retryable and attempt < self.max_retries:
                    delay = 2**attempt
                    logger.warning("%s failed (%s); retrying in %ss", operation, reason, delay)
                    time.sleep(delay)
                    continue
                self.failed_requests.append({"operation": operation, "reason": reason})
                raise
            except OSError as error:
                if attempt < self.max_retries:
                    delay = 2**attempt
                    logger.warning("%s failed (%s); retrying in %ss", operation, type(error).__name__, delay)
                    time.sleep(delay)
                    continue
                self.failed_requests.append({"operation": operation, "reason": type(error).__name__})
                raise
        raise RuntimeError("Request retry loop ended unexpectedly")

    def collect_search(self, query: str, max_videos: int) -> tuple[list[dict[str, Any]], list[str]]:
        """Collect search pages and return unique video IDs."""
        responses: list[dict[str, Any]] = []
        video_ids: list[str] = []
        page_token: str | None = None
        while len(video_ids) < max_videos:
            limit = min(50, max_videos - len(video_ids))
            params = {"part": "snippet", "q": query, "type": "video", "maxResults": limit}
            if page_token:
                params["pageToken"] = page_token
            response = self._execute(
                lambda params=params: self.youtube.search().list(**params), "search.list"
            )
            responses.append(response)
            for item in response.get("items", []):
                video_id = item.get("id", {}).get("videoId")
                if video_id and video_id not in video_ids:
                    video_ids.append(video_id)
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return responses, video_ids[:max_videos]

    def collect_videos(self, video_ids: list[str]) -> list[dict[str, Any]]:
        """Batch video detail requests; search responses do not include statistics."""
        responses = []
        for offset in range(0, len(video_ids), 50):
            batch = video_ids[offset : offset + 50]
            responses.append(self._execute(
                lambda batch=batch: self.youtube.videos().list(
                    part="snippet,contentDetails,statistics", id=",".join(batch)
                ),
                "videos.list",
            ))
        return responses

    def collect_channels(self, channel_ids: list[str]) -> list[dict[str, Any]]:
        """Batch unique channel IDs into channels.list requests."""
        unique_ids = list(dict.fromkeys(channel_ids))
        responses = []
        for offset in range(0, len(unique_ids), 50):
            batch = unique_ids[offset : offset + 50]
            responses.append(self._execute(
                lambda batch=batch: self.youtube.channels().list(
                    part="snippet,statistics", id=",".join(batch)
                ),
                "channels.list",
            ))
        return responses

    def _collect_all_replies(self, parent_id: str) -> list[dict[str, Any]]:
        """Fetch every available reply when a thread contains only a partial subset."""
        responses = []
        page_token: str | None = None
        while True:
            params: dict[str, Any] = {"part": "snippet", "parentId": parent_id, "maxResults": 100}
            if page_token:
                params["pageToken"] = page_token
            response = self._execute(
                lambda params=params: self.youtube.comments().list(**params), "comments.list"
            )
            responses.append({"parent_id": parent_id, "source": "comments.list", "response": response})
            page_token = response.get("nextPageToken")
            if not page_token:
                return responses

    def collect_comments(
        self, video_ids: list[str], max_comments_per_video: int
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
        """Collect top-level comment pages and complete reply collections per video."""
        comment_responses: list[dict[str, Any]] = []
        reply_responses: list[dict[str, Any]] = []
        comments_disabled = 0
        for video_id in video_ids:
            collected = 0
            page_token: str | None = None
            try:
                while collected < max_comments_per_video:
                    limit = min(100, max_comments_per_video - collected)
                    params: dict[str, Any] = {
                        "part": "snippet,replies", "videoId": video_id,
                        "maxResults": limit, "textFormat": "plainText",
                    }
                    if page_token:
                        params["pageToken"] = page_token
                    response = self._execute(
                        lambda params=params: self.youtube.commentThreads().list(**params),
                        f"commentThreads.list:{video_id}",
                    )
                    comment_responses.append({"video_id": video_id, "response": response})
                    items = response.get("items", [])
                    collected += len(items)
                    for thread in items:
                        snippet = thread.get("snippet", {})
                        parent_id = snippet.get("topLevelComment", {}).get("id")
                        embedded = thread.get("replies", {}).get("comments", [])
                        total = int(snippet.get("totalReplyCount", 0) or 0)
                        if total > len(embedded) and parent_id:
                            reply_responses.extend(self._collect_all_replies(parent_id))
                        elif embedded:
                            reply_responses.append({
                                "parent_id": parent_id, "source": "commentThreads.list",
                                "response": {"items": embedded},
                            })
                    page_token = response.get("nextPageToken")
                    if not page_token:
                        break
            except HttpError as error:
                reason = self._http_reason(error)
                if reason in {"commentsDisabled", "forbidden", "videoNotFound"}:
                    comments_disabled += 1
                logger.warning("Skipping comments for video %s (%s)", video_id, reason)
                continue
            except OSError as error:
                logger.warning("Skipping comments for video %s (%s)", video_id, type(error).__name__)
                continue
        return comment_responses, reply_responses, comments_disabled

    def run(
        self,
        query: str = DEFAULT_QUERY,
        max_videos: int = 20,
        max_comments_per_video: int = 10,
        raw_dir: Path = RAW_DIR / "youtube",
    ) -> dict[str, Any]:
        """Run collection and persist six credential-free raw JSON documents."""
        started_at = utc_now()
        raw_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Starting YouTube collection for query=%r, max_videos=%s", query, max_videos)
        search_raw, video_ids = self.collect_search(query, max_videos)
        videos_raw = self.collect_videos(video_ids)
        channel_ids = [
            item.get("snippet", {}).get("channelId")
            for response in videos_raw for item in response.get("items", [])
            if item.get("snippet", {}).get("channelId")
        ]
        channels_raw = self.collect_channels(channel_ids)
        comments_raw, replies_raw, comments_disabled = self.collect_comments(
            video_ids, max_comments_per_video
        )
        videos_count = sum(len(response.get("items", [])) for response in videos_raw)
        channels_count = sum(len(response.get("items", [])) for response in channels_raw)
        comments_count = sum(len(entry["response"].get("items", [])) for entry in comments_raw)
        replies_count = sum(len(entry["response"].get("items", [])) for entry in replies_raw)
        metadata = {
            "platform": "youtube", "query": query, "collection_started_at": started_at,
            "collection_completed_at": utc_now(), "requested_video_count": max_videos,
            "max_comments_per_video": max_comments_per_video, "videos_collected": videos_count,
            "channels_collected": channels_count, "comments_collected": comments_count,
            "replies_collected": replies_count, "comments_disabled_count": comments_disabled,
            "failed_requests": len(self.failed_requests), "request_errors": self.failed_requests,
            "source_api": "YouTube Data API v3", "is_sample_data": False,
        }
        save_json(search_raw, raw_dir / "search_raw.json")
        save_json(videos_raw, raw_dir / "videos_raw.json")
        save_json(channels_raw, raw_dir / "channels_raw.json")
        save_json(comments_raw, raw_dir / "comments_raw.json")
        save_json(replies_raw, raw_dir / "replies_raw.json")
        save_json(metadata, raw_dir / "collection_metadata.json")
        logger.info("YouTube collection complete: %s", metadata)
        return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect real YouTube data into data/raw/youtube.")
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--max-videos", type=int, default=20)
    parser.add_argument("--max-comments", type=int, default=10, help="Top-level comments per video")
    args = parser.parse_args()
    YouTubeCollector().run(args.query, args.max_videos, args.max_comments)


if __name__ == "__main__":
    main()
