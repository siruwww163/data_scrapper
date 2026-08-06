"""Consistent, reusable layout and offline source selection for platform pages."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from config import PROCESSED_DIR, RAW_DIR, SAMPLE_DIR
from utils.data_quality import quality_summary
from utils.file_utils import load_json
from ui.style import sample_notice


@dataclass(frozen=True)
class PlatformData:
    """Local files selected for one page; no API client is involved."""

    raw: dict[str, Any]
    frames: dict[str, pd.DataFrame]
    metadata: dict[str, Any]
    is_sample_data: bool


def _read_csv_files(folder: Path, excluded: set[str] | None = None) -> dict[str, pd.DataFrame]:
    excluded = excluded or set()
    return {
        path.stem: pd.read_csv(path)
        for path in sorted(folder.glob("*.csv"))
        if path.stem not in excluded and path.stat().st_size > 0
    }


def _load_sample(slug: str, sample_dir: Path) -> PlatformData:
    folder = sample_dir / slug
    raw_path = folder / "raw_sample.json"
    if not raw_path.is_file():
        raise FileNotFoundError(
            f"Sample data is missing for {slug}: {raw_path}. Run python generate_sample_data.py."
        )
    raw = load_json(raw_path)
    frames = _read_csv_files(folder)
    if not frames:
        raise FileNotFoundError(f"No sample CSV files found in {folder}.")
    return PlatformData(raw, frames, {"is_sample_data": True}, True)


def _valid_real_youtube(processed_dir: Path) -> tuple[bool, dict[str, Any]]:
    """Validate real status using metadata plus required, non-empty processed files."""
    quality_path = processed_dir / "data_quality.json"
    if not quality_path.is_file():
        return False, {}
    try:
        quality = load_json(quality_path)
    except (OSError, ValueError):
        return False, {}
    required = ["videos.csv", "channels.csv", "comments.csv", "replies.csv"]
    valid_files = all((processed_dir / name).is_file() and (processed_dir / name).stat().st_size > 0 for name in required)
    return quality.get("is_sample_data") is False and valid_files and quality.get("number_of_videos", 0) > 0, quality


@st.cache_data(max_entries=8)
def load_platform_data(
    slug: str,
    prefer_real: bool = False,
    sample_dir: Path = SAMPLE_DIR,
    processed_root: Path = PROCESSED_DIR,
    raw_root: Path = RAW_DIR,
) -> PlatformData:
    """Read real YouTube files when verified; otherwise return explicit sample files."""
    processed_dir = processed_root / slug
    if slug == "youtube" and prefer_real:
        is_valid, quality = _valid_real_youtube(processed_dir)
        if is_valid:
            frames = _read_csv_files(processed_dir, {"data_dictionary"})
            raw_dir = raw_root / slug
            raw = {
                path.stem: load_json(path)
                for path in sorted(raw_dir.glob("*_raw.json"))
                if path.is_file()
            }
            collection_path = raw_dir / "collection_metadata.json"
            collection = load_json(collection_path) if collection_path.is_file() else {}
            return PlatformData(raw, frames, {**collection, **quality}, False)
    return _load_sample(slug, sample_dir)


def youtube_has_real_data() -> bool:
    """Return the homepage YouTube status without exposing credentials."""
    valid, _ = _valid_real_youtube(PROCESSED_DIR / "youtube")
    return valid


def render_platform_page(
    *,
    slug: str,
    title: str,
    source: str,
    summary: str,
    authentication: str,
    objects: dict[str, list[str]],
    primary_table: str,
    comments_table: str,
    id_column: str,
    pagination: str,
    error_strategy: str,
    limitations: list[str],
    special_note: str | None = None,
    prefer_real: bool = False,
    sample_status: list[str] | None = None,
) -> None:
    st.title(title)
    st.caption(summary)
    data = load_platform_data(slug, prefer_real=prefer_real)
    if data.is_sample_data:
        st.warning("Data source: Sample data")
        for line in sample_status or []:
            st.caption(line)
        if slug == "youtube":
            st.caption("Run the YouTube collector to generate real API data.")
        sample_notice()
    else:
        st.success("Data source: Real YouTube Data API collection")
        status = data.metadata
        labels = [
            ("Query", status.get("query")), ("Collection date", status.get("collection_timestamp")),
            ("Videos collected", status.get("number_of_videos")),
            ("Channels collected", status.get("number_of_channels")),
            ("Comments collected", status.get("number_of_comments")),
            ("Replies collected", status.get("number_of_replies")),
        ]
        st.dataframe(pd.DataFrame(labels, columns=["Collection detail", "Value"]), hide_index=True, width="stretch")
    if special_note:
        st.info(special_note)
    frames = data.frames
    primary = frames[primary_table]
    comments = frames[comments_table]
    if "replies" in frames and comments_table == "comments":
        comments_for_checks = pd.concat([comments, frames["replies"]], ignore_index=True)
    else:
        comments_for_checks = comments
    checks = quality_summary(primary, comments_for_checks, id_column,
                             failed_requests=int(data.metadata.get("failed_requests", 0)))

    overview, raw_tab, processed, dictionary, technical = st.tabs(
        ["Overview", "Raw JSON", "Processed Data", "Data Dictionary", "Technical Notes"]
    )
    with overview:
        left, right = st.columns([1, 1])
        with left:
            st.subheader("Platform overview")
            st.write(summary)
            st.markdown(f"**Authentication method:** {authentication}")
        with right:
            st.subheader("Data objects collected")
            for object_name, fields in objects.items():
                st.markdown(f"**{object_name}** — {', '.join(fields)}")
        st.subheader("Data quality summary")
        for column, key in zip(st.columns(4), ["Primary objects", "Comments", "Replies", "Fields"]):
            column.metric(key, checks[key])
        readiness = "Validated sample; ready for cleaning/EDA" if data.is_sample_data else "Real collection processed; ready for cleaning/EDA"
        st.dataframe(pd.DataFrame([
            {"Check": "Missing values", "Result": checks["Missing values"]},
            {"Check": "Duplicate IDs after processing", "Result": checks["Duplicate IDs"]},
            {"Check": "Failed requests", "Result": checks["Failed requests"]},
            {"Check": "Records skipped", "Result": checks["Records skipped"]},
            {"Check": "Collection timestamp", "Result": str(primary["collected_at"].iloc[0])},
            {"Check": "Source API", "Result": source},
            {"Check": "Processing status", "Result": readiness},
        ]), hide_index=True, width="stretch")

    with raw_tab:
        st.subheader("Raw API response shape")
        st.caption("Stored JSON remains separate from cleaned CSV. Display is limited for readability.")
        if data.is_sample_data:
            preview = {name: values[:2] if isinstance(values, list) else values
                       for name, values in data.raw["objects"].items()}
            st.json({"sample": True, "notice": data.raw["notice"], "objects": preview}, expanded=2)
        else:
            preview = {name: value[:1] if isinstance(value, list) else value for name, value in data.raw.items()}
            st.json(preview, expanded=1)

    with processed:
        st.subheader("Processed datasets")
        table_names = list(frames)
        selected = st.selectbox("Dataset", table_names, format_func=lambda value: value.replace("_", " ").title())
        st.dataframe(frames[selected], hide_index=True, width="stretch")
        kind = "sample" if data.is_sample_data else "real"
        st.download_button("Download CSV", frames[selected].to_csv(index=False).encode("utf-8"),
                           f"{slug}_{selected}_{kind}.csv", "text/csv")

    with dictionary:
        dictionary_path = PROCESSED_DIR / slug / "data_dictionary.csv"
        if not data.is_sample_data and dictionary_path.is_file():
            dictionary_frame = pd.read_csv(dictionary_path)
        else:
            rows = []
            for object_name, fields in objects.items():
                rows.extend({"Object": object_name, "Field": field,
                             "Description": field.replace("_", " ").capitalize()} for field in fields)
            dictionary_frame = pd.DataFrame(rows)
        st.dataframe(dictionary_frame, hide_index=True, width="stretch")

    with technical:
        st.subheader("Pagination method")
        st.write(pagination)
        st.subheader("Error-handling strategy")
        st.write(error_strategy)
        st.subheader("Access limitations")
        for item in limitations:
            st.markdown(f"- {item}")
        st.caption("The Streamlit application reads local files only; collectors are run separately.")
