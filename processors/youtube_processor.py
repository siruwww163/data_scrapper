"""YouTube schema extraction and cleaning."""
from __future__ import annotations

from processors.common import create_data_dictionary, export_dataset, normalize_records

VIDEO_FIELDS = ["video_id", "title", "description", "published_at", "channel_id", "channel_title", "tags",
                "category_id", "duration", "view_count", "like_count", "comment_count", "collected_at", "sample"]
CHANNEL_FIELDS = ["channel_id", "channel_title", "description", "published_at", "subscriber_count",
                  "video_count", "view_count", "country", "collected_at", "sample"]
COMMENT_FIELDS = ["comment_id", "video_id", "parent_id", "author_name", "text", "like_count",
                  "published_at", "updated_at", "reply_count", "is_reply", "content_status", "collected_at", "sample"]


def process_videos(records):
    return normalize_records(records, VIDEO_FIELDS, "video_id")


def process_channels(records):
    return normalize_records(records, CHANNEL_FIELDS, "channel_id")


def process_comments(records):
    return normalize_records(records, COMMENT_FIELDS, "comment_id")


def data_dictionary():
    return create_data_dictionary({field: field.replace("_", " ").capitalize() for field in VIDEO_FIELDS}, "Video")

