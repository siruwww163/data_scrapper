"""Offline validation for schemas, sample fixtures, and every Streamlit page."""
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from config import SAMPLE_DIR


def test_sample_data_meets_demo_contract():
    contracts = {
        "youtube": ("videos", "video_id"),
        "meta": ("posts", "post_id"),
        "reddit": ("posts", "post_id"),
    }
    for platform, (primary_name, id_column) in contracts.items():
        primary = pd.read_csv(SAMPLE_DIR / platform / f"{primary_name}.csv")
        comments = pd.read_csv(SAMPLE_DIR / platform / "comments.csv")
        assert len(primary) >= 10
        assert len(comments) >= 10
        assert comments["is_reply"].astype(bool).any()
        assert primary[id_column].is_unique
        assert primary["sample"].astype(bool).all()
        assert comments["content_status"].ne("available").any()
        assert primary.isna().any().any()


def test_raw_samples_are_explicitly_labeled():
    for platform in ("youtube", "meta", "reddit"):
        text = (SAMPLE_DIR / platform / "raw_sample.json").read_text(encoding="utf-8")
        assert '"sample": true' in text
        assert "not a live API response" in text


def test_all_streamlit_pages_render_without_exceptions():
    paths = [
        Path("app.py"),
        Path("pages/1_YouTube.py"),
        Path("pages/2_Meta_Graph.py"),
        Path("pages/3_Reddit.py"),
        Path("pages/4_Pipeline_and_Documentation.py"),
    ]
    for path in paths:
        app = AppTest.from_file(str(path), default_timeout=10).run()
        assert not app.exception, f"{path}: {app.exception}"
