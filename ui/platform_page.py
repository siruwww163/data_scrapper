"""Consistent, reusable layout for all three platform pages."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from config import SAMPLE_DIR
from utils.data_quality import quality_summary
from utils.file_utils import load_json
from ui.style import sample_notice


def load_platform_data(slug: str) -> tuple[dict, dict[str, pd.DataFrame]]:
    folder = SAMPLE_DIR / slug
    raw = load_json(folder / "raw_sample.json")
    frames = {path.stem: pd.read_csv(path) for path in folder.glob("*.csv")}
    return raw, frames


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
) -> None:
    st.title(title)
    st.caption(summary)
    sample_notice()
    if special_note:
        st.info(special_note)
    raw, frames = load_platform_data(slug)
    primary, comments = frames[primary_table], frames[comments_table]
    checks = quality_summary(primary, comments, id_column)

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
        metric_keys = ["Primary objects", "Comments", "Replies", "Fields"]
        for column, key in zip(st.columns(4), metric_keys):
            column.metric(key, checks[key])
        st.dataframe(pd.DataFrame([
            {"Check": "Missing values", "Result": checks["Missing values"]},
            {"Check": "Duplicate IDs after processing", "Result": checks["Duplicate IDs"]},
            {"Check": "Failed requests (sample run)", "Result": checks["Failed requests"]},
            {"Check": "Records skipped (sample run)", "Result": checks["Records skipped"]},
            {"Check": "Collection timestamp", "Result": str(primary["collected_at"].iloc[0])},
            {"Check": "Source API", "Result": source},
            {"Check": "Processing status", "Result": "Validated sample; ready for cleaning/EDA"},
        ]), hide_index=True, use_container_width=True)

    with raw_tab:
        st.subheader("Raw API response shape")
        st.caption("Stored JSON remains separate from cleaned CSV. Display is limited to two records per object.")
        preview = {name: values[:2] if isinstance(values, list) else values for name, values in raw["objects"].items()}
        st.json({"sample": True, "notice": raw["notice"], "objects": preview}, expanded=2)

    with processed:
        st.subheader("Processed datasets")
        table_names = list(frames)
        selected = st.selectbox("Dataset", table_names, format_func=lambda value: value.replace("_", " ").title())
        st.dataframe(frames[selected], hide_index=True, use_container_width=True)
        csv_bytes = frames[selected].to_csv(index=False).encode("utf-8")
        st.download_button("Download sample CSV", csv_bytes, f"{slug}_{selected}_sample.csv", "text/csv")

    with dictionary:
        rows = []
        for object_name, fields in objects.items():
            rows.extend({"Object": object_name, "Field": field, "Description": field.replace("_", " ").capitalize()}
                        for field in fields)
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    with technical:
        st.subheader("Pagination method")
        st.write(pagination)
        st.subheader("Error-handling strategy")
        st.write(error_strategy)
        st.subheader("Access limitations")
        for item in limitations:
            st.markdown(f"- {item}")
        st.caption("The Streamlit application reads local files only; collectors are run separately.")

