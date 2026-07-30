"""Reddit official API collector using PRAW."""
from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from utils.file_utils import save_json, utc_now
from utils.logging_utils import get_logger

load_dotenv()


class RedditCollector:
    """Collect Reddit listings and comment trees through OAuth."""

    def __init__(self) -> None:
        try:
            import praw
        except ImportError as exc:
            raise RuntimeError("Install requirements.txt to use the Reddit collector.") from exc
        credentials = {
            "client_id": os.getenv("REDDIT_CLIENT_ID"),
            "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
            "user_agent": os.getenv("REDDIT_USER_AGENT"),
        }
        if not all(credentials.values()):
            raise ValueError("Reddit OAuth environment variables are required.")
        self.reddit = praw.Reddit(**credentials)
        self.logger = get_logger(self.__class__.__name__)

    def collect_subreddit_posts(self, subreddit: str, max_records: int = 50) -> list[dict[str, Any]]:
        return [self._post(item) for item in self.reddit.subreddit(subreddit).hot(limit=max_records)]

    def collect_comments(self, post_id: str, max_records: int = 100) -> list[dict[str, Any]]:
        submission = self.reddit.submission(id=post_id)
        submission.comments.replace_more(limit=0)
        rows = []
        for comment in submission.comments.list()[:max_records]:
            rows.append({
                "comment_id": comment.id, "post_id": post_id, "parent_id": comment.parent_id,
                "author": str(comment.author) if comment.author else None, "body": comment.body,
                "score": comment.score, "created_utc": comment.created_utc, "depth": comment.depth,
                "is_submitter": comment.is_submitter, "is_reply": comment.depth > 0, "collected_at": utc_now(),
            })
        return rows

    def collect_user_metadata(self, username: str) -> dict[str, Any]:
        user = self.reddit.redditor(username)
        return {"username": username, "account_created_at": user.created_utc, "link_karma": user.link_karma,
                "comment_karma": user.comment_karma, "collected_at": utc_now()}

    def collect_subreddit_metadata(self, subreddit: str) -> dict[str, Any]:
        item = self.reddit.subreddit(subreddit)
        return {"subreddit_name": item.display_name, "subscribers": item.subscribers, "title": item.title,
                "public_description": item.public_description, "created_utc": item.created_utc, "collected_at": utc_now()}

    @staticmethod
    def _post(item: Any) -> dict[str, Any]:
        return {"post_id": item.id, "subreddit": item.subreddit.display_name, "title": item.title,
                "selftext": item.selftext, "author": str(item.author) if item.author else None,
                "created_utc": item.created_utc, "score": item.score, "upvote_ratio": item.upvote_ratio,
                "num_comments": item.num_comments, "url": item.url, "post_flair": item.link_flair_text,
                "is_self": item.is_self, "collected_at": utc_now()}

    def persist(self, records: Any, path: Any) -> None:
        save_json({"sample": False, "items": records, "collected_at": utc_now()}, path)
