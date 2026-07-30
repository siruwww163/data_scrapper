"""Generate deterministic, clearly labeled fictional sample data."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import SAMPLE_DIR
from processors import meta_processor, reddit_processor, youtube_processor
from utils.file_utils import save_csv, save_json

STAMP = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)


def iso(days: int) -> str:
    return (STAMP - timedelta(days=days)).isoformat()


def decorate(rows):
    return [{**row, "collected_at": STAMP.isoformat(), "sample": True} for row in rows]


def youtube():
    videos = decorate([{
        "video_id": f"sample_yt_v{i:02}", "title": f"Sample research methods video {i}",
        "description": None if i == 4 else "Fictional demonstration record; not a live API response.",
        "published_at": iso(i), "channel_id": f"sample_yt_c{(i % 5) + 1:02}",
        "channel_title": f"Sample Channel {(i % 5) + 1}", "tags": ["sample", "research"],
        "category_id": "27", "duration": f"PT{4+i}M", "view_count": 1000 + i * 137,
        "like_count": 50 + i * 7, "comment_count": 0 if i == 7 else 8 + i,
    } for i in range(1, 11)])
    videos.append(dict(videos[0]))
    channels = decorate([{
        "channel_id": f"sample_yt_c{i:02}", "channel_title": f"Sample Channel {i}",
        "description": "Fictional channel used for schema demonstration.", "published_at": iso(300 + i),
        "subscriber_count": 1000 * i, "video_count": 20 + i, "view_count": 50000 * i,
        "country": None if i == 3 else "US",
    } for i in range(1, 6)])
    comments = decorate([{
        "comment_id": f"sample_yt_cm{i:02}", "video_id": f"sample_yt_v{(i % 10) + 1:02}",
        "parent_id": f"sample_yt_cm{(i-10):02}" if i > 10 else None, "author_name": f"Sample User {i}",
        "text": "[unavailable]" if i == 6 else f"Fictional sample comment {i}.", "like_count": i % 4,
        "published_at": iso(i), "updated_at": iso(i), "reply_count": 1 if i in (1, 2, 3) else 0,
        "is_reply": i > 10, "content_status": "unavailable" if i == 6 else "available",
    } for i in range(1, 14)])
    return {"videos": videos, "channels": channels, "comments": comments}


def meta():
    pages = decorate([{"page_id": f"sample_meta_page{i:02}", "page_name": f"Sample Public Page {i}",
                       "category": "Education", "about": "Fictional Page schema example.", "website": None,
                       "fan_count": 100 * i, "followers_count": 110 * i} for i in range(1, 4)])
    posts = decorate([{
        "post_id": f"sample_meta_p{i:02}", "page_id": f"sample_meta_page{(i % 3) + 1:02}",
        "message": None if i == 5 else f"Fictional sample Page post {i}.", "created_time": iso(i),
        "permalink_url": f"https://example.invalid/sample-meta-post-{i}", "attachments": [],
        "shares": i * 2, "insights_status": "permission required",
    } for i in range(1, 11)])
    posts.append(dict(posts[0]))
    comments = decorate([{
        "comment_id": f"sample_meta_cm{i:02}", "post_id": f"sample_meta_p{(i % 10) + 1:02}",
        "parent_id": f"sample_meta_cm{(i-10):02}" if i > 10 else None,
        "message": "[unavailable]" if i == 7 else f"Fictional sample Page comment {i}.",
        "created_time": iso(i), "author": f"Sample Account {i}", "like_count": i % 3,
        "comment_count": 0, "is_reply": i > 10, "content_status": "unavailable" if i == 7 else "available",
    } for i in range(1, 13)])
    return {"pages": pages, "posts": posts, "comments": comments}


def reddit():
    posts = decorate([{
        "post_id": f"sample_rd_p{i:02}", "subreddit": "SampleResearch", "title": f"Sample discussion {i}",
        "selftext": None if i == 3 else "Fictional demonstration content.", "author": None if i == 8 else f"sample_user_{i}",
        "created_utc": iso(i), "score": i * 9, "upvote_ratio": round(0.70 + i / 50, 2),
        "num_comments": i + 2, "url": f"https://example.invalid/sample-reddit-{i}", "post_flair": None,
        "is_self": True, "content_status": "deleted" if i == 8 else "available",
    } for i in range(1, 11)])
    posts.append(dict(posts[0]))
    comments = decorate([{
        "comment_id": f"sample_rd_cm{i:02}", "post_id": f"sample_rd_p{(i % 10) + 1:02}",
        "parent_id": f"t1_sample_rd_cm{(i-10):02}" if i > 10 else f"t3_sample_rd_p{(i % 10) + 1:02}",
        "author": None if i == 5 else f"sample_commenter_{i}", "body": "[removed]" if i == 5 else f"Fictional sample comment {i}.",
        "score": i, "created_utc": iso(i), "depth": 1 if i > 10 else 0, "is_submitter": False,
        "is_reply": i > 10, "content_status": "removed" if i == 5 else "available",
    } for i in range(1, 14)])
    users = decorate([{"username": f"sample_user_{i}", "account_created_at": iso(500 + i),
                       "link_karma": 100 * i, "comment_karma": 75 * i} for i in range(1, 6)])
    subreddits = decorate([{"subreddit_name": "SampleResearch", "subscribers": 12345,
                            "title": "Sample Research Community", "public_description": "Fictional sample only.",
                            "created_utc": iso(1000)}])
    return {"posts": posts, "comments": comments, "users": users, "subreddits": subreddits}


def write_platform(name, raw, frames):
    folder = SAMPLE_DIR / name
    folder.mkdir(parents=True, exist_ok=True)
    save_json({"sample": True, "notice": "Synthetic sample data; not a live API response.", "objects": raw}, folder / "raw_sample.json")
    for object_name, frame in frames.items():
        save_csv(frame, folder / f"{object_name}.csv")


def main():
    yt, mt, rd = youtube(), meta(), reddit()
    write_platform("youtube", yt, {"videos": youtube_processor.process_videos(yt["videos"]),
        "channels": youtube_processor.process_channels(yt["channels"]), "comments": youtube_processor.process_comments(yt["comments"])})
    write_platform("meta", mt, {"pages": meta_processor.process_pages(mt["pages"]),
        "posts": meta_processor.process_posts(mt["posts"]), "comments": meta_processor.process_comments(mt["comments"])})
    write_platform("reddit", rd, {"posts": reddit_processor.process_posts(rd["posts"]),
        "comments": reddit_processor.process_comments(rd["comments"]), "users": reddit_processor.process_users(rd["users"]),
        "subreddits": reddit_processor.process_subreddits(rd["subreddits"])})
    print(f"Sample data written to {SAMPLE_DIR}")


if __name__ == "__main__":
    main()
