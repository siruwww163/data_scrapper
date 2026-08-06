"""Offline validation for schemas, sample fixtures, and every Streamlit page."""
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from config import SAMPLE_DIR
from ui.platform_page import load_platform_data, youtube_has_real_data


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


def test_platform_pages_show_truthful_sources():
    youtube = AppTest.from_file("pages/1_YouTube.py", default_timeout=10).run()
    if youtube_has_real_data():
        assert any("Real YouTube Data API collection" in item.value for item in youtube.success)
    else:
        assert any("Data source: Sample data" in item.value for item in youtube.warning)
    meta = AppTest.from_file("pages/2_Meta_Graph.py", default_timeout=10).run()
    reddit = AppTest.from_file("pages/3_Reddit.py", default_timeout=10).run()
    assert any("Data source: Sample data" in item.value for item in meta.warning)
    assert any("Data source: Sample data" in item.value for item in reddit.warning)


def test_youtube_source_requires_metadata_and_nonempty_files(tmp_path):
    processed_root, raw_root = tmp_path / "processed", tmp_path / "raw"
    youtube = processed_root / "youtube"
    youtube.mkdir(parents=True)
    (youtube / "data_quality.json").write_text('{"is_sample_data": false, "number_of_videos": 1}', encoding="utf-8")
    load_platform_data.clear()
    fallback = load_platform_data("youtube", True, SAMPLE_DIR, processed_root, raw_root)
    assert fallback.is_sample_data is True

    frames = {
        "videos.csv": "video_id,collected_at\nv1,2026-01-01T00:00:00Z\n",
        "channels.csv": "channel_id,collected_at\nc1,2026-01-01T00:00:00Z\n",
        "comments.csv": "comment_id,is_reply,collected_at\ncm1,False,2026-01-01T00:00:00Z\n",
        "replies.csv": "comment_id,is_reply,collected_at\nr1,True,2026-01-01T00:00:00Z\n",
    }
    for name, content in frames.items():
        (youtube / name).write_text(content, encoding="utf-8")
    load_platform_data.clear()
    real = load_platform_data("youtube", True, SAMPLE_DIR, processed_root, raw_root)
    assert real.is_sample_data is False


def test_streamlit_pages_do_not_import_collectors():
    for path in [Path("app.py"), *Path("pages").glob("*.py"), Path("ui/platform_page.py")]:
        source = path.read_text(encoding="utf-8")
        assert "from collectors" not in source
        assert "import collectors" not in source
