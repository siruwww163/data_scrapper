"""Shared processor functions."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from utils.data_quality import remove_duplicate_ids
from utils.file_utils import save_csv


def normalize_records(records: list[dict[str, Any]], fields: list[str], id_column: str) -> pd.DataFrame:
    """Flatten records, select a stable schema, convert timestamps, and deduplicate."""
    frame = pd.json_normalize(records, sep="_").reindex(columns=fields)
    for column in [name for name in frame if "created" in name or "published" in name or "updated" in name or name.endswith("_at")]:
        frame[column] = pd.to_datetime(frame[column], utc=True, errors="coerce")
    for column in frame.select_dtypes(include=["object"]):
        frame[column] = frame[column].map(lambda value: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value)
    return remove_duplicate_ids(frame, id_column)


def export_dataset(frame: pd.DataFrame, output_path: Path) -> Path:
    """Write a processed table separately from raw JSON."""
    return save_csv(frame, output_path)


def create_data_dictionary(fields: dict[str, str], object_name: str) -> pd.DataFrame:
    """Create a concise, display-ready field dictionary."""
    return pd.DataFrame([{"Object": object_name, "Field": field, "Description": description} for field, description in fields.items()])

