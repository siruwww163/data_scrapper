"""Command-line entry point for offline social-media collection pipelines."""
from __future__ import annotations

import argparse
from collectors.youtube_collector import DEFAULT_QUERY, YouTubeCollector
from processors.youtube_processor import process_raw_files
from utils.logging_utils import get_logger

logger = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect and process official API data before running Streamlit.")
    parser.add_argument("--platform", choices=["youtube"], required=True)
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--max-videos", type=int, default=20)
    parser.add_argument("--max-comments", type=int, default=10)
    args = parser.parse_args()
    if args.max_videos < 1 or args.max_comments < 0:
        parser.error("--max-videos must be at least 1 and --max-comments cannot be negative")
    logger.info("Running %s offline collection pipeline", args.platform)
    collector = YouTubeCollector()
    collector.run(args.query, args.max_videos, args.max_comments)
    quality = process_raw_files()
    logger.info(
        "Pipeline complete: videos=%s channels=%s comments=%s replies=%s",
        quality["number_of_videos"], quality["number_of_channels"],
        quality["number_of_comments"], quality["number_of_replies"],
    )


if __name__ == "__main__":
    main()
