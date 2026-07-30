# Official Social Media API Data Collection Demo

A concise Streamlit portfolio project demonstrating how research data can be authenticated, collected, paginated, preserved, normalized, validated, and presented from three official social-media APIs:

- YouTube Data API v3
- Meta Graph API (Facebook Pages only, subject to permission)
- Reddit API through PRAW

The site uses **pre-collected local files only**. It does not make API calls during page rendering, and it does not perform sentiment analysis, topic modeling, prediction, or complex exploratory analysis.

## Purpose

This repository is designed for a research-assistant or data-engineering interview. Its focus is API data coverage, reliable collection, structured output, provenance, and readiness for later cleaning and EDA.

The bundled records are clearly labeled, synthetic sample data. They are not real-time API responses, do not represent actual findings, and contain no real-user private information.

## Project structure

```text
.
├── app.py
├── pages/
│   ├── 1_YouTube.py
│   ├── 2_Meta_Graph.py
│   ├── 3_Reddit.py
│   └── 4_Pipeline_and_Documentation.py
├── collectors/
│   ├── base.py
│   ├── youtube_collector.py
│   ├── meta_collector.py
│   └── reddit_collector.py
├── processors/
│   ├── common.py
│   ├── youtube_processor.py
│   ├── meta_processor.py
│   └── reddit_processor.py
├── utils/
│   ├── data_quality.py
│   ├── file_utils.py
│   └── logging_utils.py
├── data/
│   ├── raw/{youtube,meta,reddit}/
│   └── processed/{youtube,meta,reddit}/
├── sample_data/{youtube,meta,reddit}/
├── generate_sample_data.py
├── requirements.txt
└── .env.example
```

Collection code, processing code, and Streamlit display code remain separate. The app imports only processed/sample files; it never instantiates a collector.

## Installation

Python 3.10 or newer is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Copy the environment template:

```powershell
Copy-Item .env.example .env
```

Add only the credentials needed for collectors you intend to run. The website works without any API credentials.

## Environment variables

| Variable | Used by | Notes |
|---|---|---|
| `YOUTUBE_API_KEY` | YouTube | Public-data endpoints; some operations require OAuth instead |
| `META_ACCESS_TOKEN` | Meta | Must carry the required reviewed permissions and Page access |
| `META_API_VERSION` | Meta | Explicit Graph API version |
| `REDDIT_CLIENT_ID` | Reddit | OAuth application identifier |
| `REDDIT_CLIENT_SECRET` | Reddit | OAuth application secret |
| `REDDIT_USER_AGENT` | Reddit | Descriptive client user agent |

Credentials are read through environment variables, excluded by `.gitignore`, and never written to logs.

## Run the website

```powershell
streamlit run app.py
```

Use the sidebar to open YouTube, Meta Graph, Reddit, and pipeline documentation pages. Each platform page provides a consistent Overview, Raw JSON, Processed Data, Data Dictionary, and Technical Notes layout. Sample CSV files can be downloaded from the browser.

To regenerate the deterministic sample files:

```powershell
python generate_sample_data.py
```

## Running collectors

Collectors are library-style clients so a research collection run can supply its own targets, dates, and record caps.

```python
from pathlib import Path
from collectors.youtube_collector import YouTubeCollector

client = YouTubeCollector(timeout=30, max_retries=3)
videos = client.collect_videos("research methods", max_records=25)
client.persist(videos, Path("data/raw/youtube/videos.json"))
```

Meta and Reddit follow the same separation:

```python
from collectors.meta_collector import MetaCollector
from collectors.reddit_collector import RedditCollector

meta = MetaCollector()
page_posts = meta.collect_page_posts("AUTHORIZED_PAGE_ID", max_records=25)

reddit = RedditCollector()
posts = reddit.collect_subreddit_posts("AskSocialScience", max_records=25)
```

Run collectors outside Streamlit. Choose targets consistent with platform terms, research ethics, and approved access. Store results in `data/raw/<platform>/`.

## Running processors

Processors accept Python lists of raw dictionaries and return Pandas dataframes:

```python
from processors.youtube_processor import process_videos
from utils.file_utils import load_json, save_csv

payload = load_json("data/raw/youtube/videos.json")
frame = process_videos(payload["items"])
save_csv(frame, "data/processed/youtube/videos.csv")
```

They flatten nested structures, select stable fields, standardize timestamps to UTC, serialize nested values, preserve missing values, remove duplicate IDs, and support separate comment/reply records. `processors.common.create_data_dictionary` generates field dictionaries. The same processed data can optionally be written to SQLite with `pandas.DataFrame.to_sql`.

## Storage and provenance

- `data/raw/` stores API responses separately from transformed data.
- `data/processed/` stores structured CSV or optional SQLite tables.
- `sample_data/` stores deterministic fictional demonstration records.
- Each collected record includes `collected_at`.
- Unique object IDs are used for deduplication.
- Deleted, removed, disabled, and unavailable content is flagged rather than reconstructed.
- Raw data should be treated as append-only evidence; reruns should create a new timestamped collection file.

## Authentication, pagination, and errors

| Platform | Authentication | Pagination | Main limitation |
|---|---|---|---|
| YouTube | API key or endpoint-dependent OAuth | `nextPageToken` | Quota; comments may be disabled |
| Meta Graph | Access token | Cursor-based `paging.next` | App review, permissions, token, and Page access |
| Reddit | OAuth through PRAW | Listing iterator / `after` cursor | Listing limits, rate limits, and API rules |

The shared HTTP collector applies request timeouts, bounded retries, and exponential backoff for rate limits and selected server errors. Exceptions contain no credentials. Platform collectors stop at `max_records`, keep raw JSON, and log skipped/inaccessible objects. Search and video-detail YouTube endpoints have different quota costs.

Meta Graph API access is explicitly permission-dependent. This project does **not** claim access to arbitrary Facebook users or public personal profiles. Page fields, comments, replies, reactions, and insights are shown only when the access token, reviewed app permissions, Page access, and current Meta requirements permit them. Unavailable insights are labeled `permission required`; they are never fabricated.

## Known limitations

- APIs, fields, quotas, policies, and required permissions can change.
- YouTube comments may be disabled and optional fields may be absent.
- Meta Page data depends on current token scopes, app review, Page access, and endpoint eligibility.
- Reddit listing limits and removed/deleted content constrain completeness.
- Counts in the sample UI describe the bundled fictional records, not platform populations.
- The collectors demonstrate robust patterns but a production study should add run manifests, automated schema-change alerts, persistent retry queues, and study-specific tests.

## Ethics and privacy

Use only official, authorized access. Minimize personal data, define a research purpose and retention schedule, respect deletions and platform terms, secure raw files, and obtain institutional review where applicable. Do not infer sensitive traits or attempt to deanonymize users. The included sample records use fictional identifiers and `example.invalid` URLs.

## Platform scope

YouTube coverage includes videos, channels, comments, replies, and engagement counts. Meta coverage is limited to authorized Facebook Pages and permission-dependent Page content. Reddit coverage includes listings, nested comments, users, and subreddit metadata exposed through authorized API access. These differences are visible in the homepage comparison table.
