"""Meta Page schema extraction and cleaning."""
from processors.common import create_data_dictionary, normalize_records

PAGE_FIELDS = ["page_id", "page_name", "category", "about", "website", "fan_count", "followers_count", "collected_at", "sample"]
POST_FIELDS = ["post_id", "page_id", "message", "created_time", "permalink_url", "attachments", "shares",
               "insights_status", "collected_at", "sample"]
COMMENT_FIELDS = ["comment_id", "post_id", "parent_id", "message", "created_time", "author", "like_count",
                  "comment_count", "is_reply", "content_status", "collected_at", "sample"]


def process_pages(records):
    return normalize_records(records, PAGE_FIELDS, "page_id")


def process_posts(records):
    return normalize_records(records, POST_FIELDS, "post_id")


def process_comments(records):
    return normalize_records(records, COMMENT_FIELDS, "comment_id")


def data_dictionary():
    return create_data_dictionary({field: field.replace("_", " ").capitalize() for field in POST_FIELDS}, "Post")

