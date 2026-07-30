"""Project paths and constants."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SAMPLE_DIR = ROOT / "sample_data"
LOG_DIR = ROOT / "logs"

PLATFORMS = {
    "youtube": {"label": "YouTube Data API v3", "source": "YouTube Data API v3"},
    "meta": {"label": "Meta Graph API", "source": "Meta Graph API"},
    "reddit": {"label": "Reddit API", "source": "Reddit API / PRAW"},
}

