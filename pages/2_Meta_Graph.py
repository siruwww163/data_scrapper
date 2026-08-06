"""Meta Graph platform page."""
from ui.platform_page import render_platform_page
from ui.style import configure_page

configure_page("Meta Graph API")
render_platform_page(
    slug="meta", title="Meta Graph API", source="Meta Graph API",
    summary="Permission-aware Facebook Page, Page-post, comment, reply, and optional insight schemas.",
    authentication="A valid access token with the required reviewed permissions and Page access.",
    objects={
        "Page": ["page_id", "page_name", "category", "about", "website", "fan_count", "followers_count"],
        "Post": ["post_id", "page_id", "message", "created_time", "permalink_url", "attachments", "shares"],
        "Comment": ["comment_id", "post_id", "parent_id", "message", "created_time", "author", "like_count",
                    "comment_count", "is_reply"],
        "Insights / reactions": ["permission-dependent; unavailable is recorded rather than inferred"],
    },
    primary_table="posts", comments_table="comments", id_column="post_id",
    sample_status=["Live API status: Not connected", "Access depends on Page permissions and access token scope."],
    pagination="The collector follows the API-provided cursor-based paging.next URL until the cap is reached.",
    error_strategy="Permission errors remain explicit. Rate limits and selected server errors use bounded exponential backoff; no unavailable metrics are fabricated.",
    limitations=[
        "Data access depends on the token, app permissions, Page role/access, review, and current Meta requirements.",
        "This project does not claim access to arbitrary Facebook users or personal profiles.",
        "Insights and reactions are shown only after a successful authorized response.",
    ],
    special_note="Meta Graph API access is determined by the access token, app permissions, Page access, and Meta review requirements.",
)
