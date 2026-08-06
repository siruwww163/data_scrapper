"""YouTube platform page."""
from ui.platform_page import render_platform_page
from ui.style import configure_page

configure_page("YouTube Data API v3")
render_platform_page(
    slug="youtube", title="YouTube Data API v3", source="YouTube Data API v3",
    summary="Pre-collected video, channel, comment, reply, and engagement fields from the official API.",
    authentication="API key for public-data endpoints; OAuth is required for authorized/private operations.",
    objects={
        "Video": ["video_id", "title", "description", "published_at", "channel_id", "channel_title", "tags",
                  "category_id", "duration", "view_count", "like_count", "comment_count"],
        "Channel": ["channel_id", "channel_title", "description", "published_at", "subscriber_count", "video_count",
                    "view_count", "country"],
        "Comment": ["comment_id", "video_id", "parent_id", "author_name", "text", "like_count", "published_at",
                    "updated_at", "reply_count", "is_reply"],
    },
    primary_table="videos", comments_table="comments", id_column="video_id",
    prefer_real=True,
    pagination="Each list request follows nextPageToken until the record cap or the final page.",
    error_strategy="429 and selected 5xx responses use bounded exponential backoff. Missing optional fields are kept as null; videos with disabled comments are logged and skipped.",
    limitations=[
        "Search and video-detail endpoints have different quota costs.",
        "Videos with comments disabled cannot return comment threads.",
        "Some fields can be absent or hidden by the owner.",
        "Raw JSON and processed CSV are stored separately.",
    ],
)
