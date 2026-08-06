"""Reddit platform page."""
from ui.platform_page import render_platform_page
from ui.style import configure_page

configure_page("Reddit API")
render_platform_page(
    slug="reddit", title="Reddit API", source="Reddit API / PRAW",
    summary="Pre-collected posts, nested comments, users, subreddits, scores, and timestamps via OAuth/PRAW.",
    authentication="OAuth application credentials through PRAW and a descriptive user agent.",
    objects={
        "Post": ["post_id", "subreddit", "title", "selftext", "author", "created_utc", "score", "upvote_ratio",
                 "num_comments", "url", "post_flair", "is_self"],
        "Comment": ["comment_id", "post_id", "parent_id", "author", "body", "score", "created_utc", "depth",
                    "is_submitter", "is_reply"],
        "User": ["username", "account_created_at", "link_karma", "comment_karma"],
        "Subreddit": ["subreddit_name", "subscribers", "title", "public_description", "created_utc"],
    },
    primary_table="posts", comments_table="comments", id_column="post_id",
    sample_status=["Live API status: Not connected in this demo", "Previous Reddit API experience is demonstrated in a separate project."],
    pagination="PRAW listing iterators manage listing pagination; API listings may expose an after cursor.",
    error_strategy="Rate-limited/transient requests are retried by the client strategy. Deleted authors become null; [deleted] and [removed] bodies are preserved as explicit statuses.",
    limitations=[
        "Listing size, rate limits, content availability, and Reddit API rules constrain coverage.",
        "Deleted or removed content cannot be reconstructed.",
        "Comment trees may require extra requests and explicit MoreComments handling.",
    ],
)
