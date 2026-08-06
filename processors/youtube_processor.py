"""Transform raw YouTube API responses into research-ready CSV files."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from config import PROCESSED_DIR, RAW_DIR
from processors.common import create_data_dictionary, normalize_records
from utils.file_utils import load_json, save_csv, save_json, utc_now
from utils.logging_utils import get_logger

logger = get_logger(__name__)

VIDEO_FIELDS = ["video_id", "title", "description", "published_at", "channel_id", "channel_title", "tags",
                "category_id", "duration", "view_count", "like_count", "comment_count", "default_language",
                "collected_at", "sample"]
CHANNEL_FIELDS = ["channel_id", "channel_title", "description", "published_at", "subscriber_count",
                  "hidden_subscriber_count", "video_count", "view_count", "country", "custom_url",
                  "collected_at", "sample"]
COMMENT_FIELDS = ["comment_id", "video_id", "parent_id", "author_name", "text", "like_count",
                  "published_at", "updated_at", "reply_count", "is_reply", "content_status", "collected_at", "sample"]


def process_videos(records: list[dict[str, Any]]) -> pd.DataFrame:
    return normalize_records(records, VIDEO_FIELDS, "video_id")


def process_channels(records: list[dict[str, Any]]) -> pd.DataFrame:
    return normalize_records(records, CHANNEL_FIELDS, "channel_id")


def process_comments(records: list[dict[str, Any]]) -> pd.DataFrame:
    return normalize_records(records, COMMENT_FIELDS, "comment_id")


def data_dictionary() -> pd.DataFrame:
    descriptions = {field: field.replace("_", " ").capitalize() for field in VIDEO_FIELDS}
    return create_data_dictionary(descriptions, "Video")


def _items(responses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for response in responses for item in response.get("items", [])]


def _video_rows(responses: list[dict[str, Any]], collected_at: str) -> list[dict[str, Any]]:
    rows = []
    for item in _items(responses):
        snippet, details, stats = item.get("snippet", {}), item.get("contentDetails", {}), item.get("statistics", {})
        rows.append({
            "video_id": item.get("id"), "title": snippet.get("title"), "description": snippet.get("description"),
            "published_at": snippet.get("publishedAt"), "channel_id": snippet.get("channelId"),
            "channel_title": snippet.get("channelTitle"), "tags": snippet.get("tags"),
            "category_id": snippet.get("categoryId"), "duration": details.get("duration"),
            "view_count": stats.get("viewCount"), "like_count": stats.get("likeCount"),
            "comment_count": stats.get("commentCount"), "default_language": snippet.get("defaultLanguage"),
            "collected_at": collected_at, "sample": False,
        })
    return rows


def _channel_rows(responses: list[dict[str, Any]], collected_at: str) -> list[dict[str, Any]]:
    rows = []
    for item in _items(responses):
        snippet, stats = item.get("snippet", {}), item.get("statistics", {})
        rows.append({
            "channel_id": item.get("id"), "channel_title": snippet.get("title"),
            "description": snippet.get("description"), "published_at": snippet.get("publishedAt"),
            "subscriber_count": stats.get("subscriberCount"),
            "hidden_subscriber_count": stats.get("hiddenSubscriberCount"),
            "video_count": stats.get("videoCount"), "view_count": stats.get("viewCount"),
            "country": snippet.get("country"), "custom_url": snippet.get("customUrl"),
            "collected_at": collected_at, "sample": False,
        })
    return rows


def _comment_row(item: dict[str, Any], video_id: str | None, parent_id: str | None,
                 is_reply: bool, collected_at: str, reply_count: int = 0) -> dict[str, Any]:
    snippet = item.get("snippet", {})
    text = snippet.get("textDisplay") or snippet.get("textOriginal")
    return {
        "comment_id": item.get("id"), "video_id": snippet.get("videoId") or video_id,
        "parent_id": snippet.get("parentId") or parent_id, "author_name": snippet.get("authorDisplayName"),
        "text": text, "like_count": snippet.get("likeCount"), "published_at": snippet.get("publishedAt"),
        "updated_at": snippet.get("updatedAt"), "reply_count": reply_count, "is_reply": is_reply,
        "content_status": "available" if text else "unavailable", "collected_at": collected_at, "sample": False,
    }


def process_raw_files(
    raw_dir: Path = RAW_DIR / "youtube", output_dir: Path = PROCESSED_DIR / "youtube"
) -> dict[str, Any]:
    """Read the six raw files and write four datasets, dictionary, and quality JSON."""
    required = ["videos_raw.json", "channels_raw.json", "comments_raw.json", "replies_raw.json", "collection_metadata.json"]
    missing = [name for name in required if not (raw_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing YouTube raw files: {', '.join(missing)}. Run the collector first.")
    metadata = load_json(raw_dir / "collection_metadata.json")
    if metadata.get("is_sample_data") is not False:
        raise ValueError("Raw collection metadata is not marked as real API data.")
    collected_at = metadata.get("collection_completed_at") or utc_now()
    video_rows = _video_rows(load_json(raw_dir / "videos_raw.json"), collected_at)
    channel_rows = _channel_rows(load_json(raw_dir / "channels_raw.json"), collected_at)
    comment_rows, reply_rows = [], []
    for entry in load_json(raw_dir / "comments_raw.json"):
        video_id = entry.get("video_id")
        for thread in entry.get("response", {}).get("items", []):
            thread_snippet = thread.get("snippet", {})
            top = thread_snippet.get("topLevelComment", {})
            comment_rows.append(_comment_row(top, video_id, None, False, collected_at,
                                             int(thread_snippet.get("totalReplyCount", 0) or 0)))
    for entry in load_json(raw_dir / "replies_raw.json"):
        for item in entry.get("response", {}).get("items", []):
            reply_rows.append(_comment_row(item, None, entry.get("parent_id"), True, collected_at))

    raw_counts = {"videos": len(video_rows), "comments": len(comment_rows), "replies": len(reply_rows)}
    videos, channels = process_videos(video_rows), process_channels(channel_rows)
    comments, replies = process_comments(comment_rows), process_comments(reply_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_csv(videos, output_dir / "videos.csv")
    save_csv(channels, output_dir / "channels.csv")
    save_csv(comments, output_dir / "comments.csv")
    save_csv(replies, output_dir / "replies.csv")
    dictionary_rows = []
    for object_name, fields in (("Video", VIDEO_FIELDS), ("Channel", CHANNEL_FIELDS),
                                ("Comment", COMMENT_FIELDS), ("Reply", COMMENT_FIELDS)):
        dictionary_rows.extend({"object": object_name, "field": field,
                                "description": field.replace("_", " ").capitalize()} for field in fields)
    save_csv(pd.DataFrame(dictionary_rows), output_dir / "data_dictionary.csv")
    combined_missing = {
        "videos": videos.isna().sum().astype(int).to_dict(),
        "channels": channels.isna().sum().astype(int).to_dict(),
        "comments": comments.isna().sum().astype(int).to_dict(),
        "replies": replies.isna().sum().astype(int).to_dict(),
    }
    quality = {
        "number_of_videos": len(videos), "number_of_channels": len(channels),
        "number_of_comments": len(comments), "number_of_replies": len(replies),
        "duplicate_video_ids_removed": raw_counts["videos"] - len(videos),
        "duplicate_comment_ids_removed": raw_counts["comments"] - len(comments),
        "duplicate_reply_ids_removed": raw_counts["replies"] - len(replies),
        "missing_values_by_column": combined_missing,
        "comments_disabled_count": int(metadata.get("comments_disabled_count", 0)),
        "failed_requests": int(metadata.get("failed_requests", 0)),
        "query": metadata.get("query"), "collection_timestamp": collected_at,
        "processing_timestamp": utc_now(), "source_api": "YouTube Data API v3", "is_sample_data": False,
    }
    save_json(quality, output_dir / "data_quality.json")
    logger.info("YouTube processing complete: %s", quality)
    return quality


def main() -> None:
    parser = argparse.ArgumentParser(description="Process data/raw/youtube into structured CSV files.")
    parser.parse_args()
    process_raw_files()


if __name__ == "__main__":
    main()
