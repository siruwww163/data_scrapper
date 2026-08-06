"""Home page for the Official Social Media API Data Collection Demo."""
import pandas as pd
import streamlit as st

from ui.style import configure_page, sample_notice
from ui.platform_page import youtube_has_real_data

configure_page("Official Social Media API Data Collection Demo")

st.markdown('<div class="eyebrow">Research data engineering portfolio</div>', unsafe_allow_html=True)
st.title("Official Social Media API Data Collection Demo")
st.subheader("A comparison of research data available through YouTube, Meta Graph, and Reddit APIs")
st.write(
    "This project demonstrates official API authentication, pagination, resilient collection, raw-data preservation, "
    "schema extraction, validation, and research-ready tabular output. It intentionally stops before analysis or modeling."
)
st.info(
    "This demo includes a verified YouTube Data API collection pipeline. The Meta Graph and Reddit sections "
    "currently use clearly labeled sample datasets to demonstrate their schemas and data coverage. Sample "
    "records are not presented as live API results."
)
sample_notice()

st.header("Platform status")
youtube_real = youtube_has_real_data()
st.dataframe(pd.DataFrame([
    {"Platform": "YouTube", "Data source": "Real pre-collected API data" if youtube_real else "Sample data",
     "API status": "Connected" if youtube_real else "Not yet collected"},
    {"Platform": "Meta Graph", "Data source": "Sample data", "API status": "Not connected"},
    {"Platform": "Reddit", "Data source": "Sample data", "API status": "Not connected in this demo"},
]), hide_index=True, width="stretch")

cards = [
    ("YouTube Data API", "Videos<br>Channels<br>Comments and replies<br>Engagement metrics"),
    ("Meta Graph API", "Facebook Pages<br>Page posts<br>Permission-dependent comments, replies, reactions or insights"),
    ("Reddit API", "Subreddits and posts<br>Comments and replies<br>Users<br>Scores and timestamps"),
]
for column, (name, items) in zip(st.columns(3), cards):
    column.markdown(f'<div class="platform-card"><div class="eyebrow">Official API</div><h3>{name}</h3><p>{items}</p></div>',
                    unsafe_allow_html=True)

st.header("Platform data coverage")
comparison = pd.DataFrame([
    ["YouTube", "Video", "Channel", "Yes", "Yes", "Views, likes, comment count", "Channel metadata",
     "API key / endpoint-dependent OAuth", "nextPageToken", "Quota; comments may be disabled", "JSON", "CSV"],
    ["Meta Graph", "Facebook Page post", "Page", "Permission-dependent", "Permission-dependent",
     "Reactions, shares, comments, allowed insights", "Page metadata", "Access token", "Cursor-based paging",
     "App permissions, review, and Page access", "JSON", "CSV"],
    ["Reddit", "Post", "User or subreddit", "Yes", "Yes", "Score, upvote ratio, comment count",
     "User and subreddit metadata", "OAuth / PRAW", "after cursor / listing iterator",
     "Listing limits and API access rules", "JSON", "CSV"],
], columns=["Platform", "Primary content object", "Creator or account object", "Comments", "Replies",
            "Engagement metrics", "User or channel information", "Authentication method", "Pagination method",
            "Main access limitation", "Raw storage format", "Processed storage format"])
st.dataframe(comparison, hide_index=True, width="stretch")

st.header("Collection workflow")
st.markdown('<div class="pipeline">Authentication → API request → Pagination → Raw JSON → Schema extraction → '
            'Cleaning & validation → Processed CSV → Streamlit presentation</div>', unsafe_allow_html=True)

left, right = st.columns(2)
with left:
    st.subheader("Project boundaries")
    st.markdown("""
- Pre-collected local data only; the website makes no live API calls.
- No sentiment analysis, topic modeling, prediction, or complex EDA.
- Availability depends on API policy, permissions, quotas, deletions, and disabled comments.
- Sample records demonstrate engineering behavior, not platform findings.
""")
with right:
    st.subheader("Repository design")
    st.code("""collectors/   Official API clients
processors/   Schema and cleaning logic
data/raw/     Immutable collection outputs
data/processed/ Structured research tables
sample_data/  Offline demonstration records
pages/        Platform and pipeline views
utils/        Persistence, logging, validation""", language="text")
