"""Reddit schema extraction and cleaning."""
from processors.common import create_data_dictionary, normalize_records

POST_FIELDS = ["post_id", "subreddit", "title", "selftext", "author", "created_utc", "score", "upvote_ratio",
               "num_comments", "url", "post_flair", "is_self", "content_status", "collected_at", "sample"]
COMMENT_FIELDS = ["comment_id", "post_id", "parent_id", "author", "body", "score", "created_utc", "depth",
                  "is_submitter", "is_reply", "content_status", "collected_at", "sample"]
USER_FIELDS = ["username", "account_created_at", "link_karma", "comment_karma", "collected_at", "sample"]
SUBREDDIT_FIELDS = ["subreddit_name", "subscribers", "title", "public_description", "created_utc", "collected_at", "sample"]


def process_posts(records):
    return normalize_records(records, POST_FIELDS, "post_id")


def process_comments(records):
    return normalize_records(records, COMMENT_FIELDS, "comment_id")


def process_users(records):
    return normalize_records(records, USER_FIELDS, "username")


def process_subreddits(records):
    return normalize_records(records, SUBREDDIT_FIELDS, "subreddit_name")


def data_dictionary():
    return create_data_dictionary({field: field.replace("_", " ").capitalize() for field in POST_FIELDS}, "Post")

