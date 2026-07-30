"""JSON and CSV persistence helpers."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def utc_now() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def save_json(payload: Any, path: Path) -> Path:
    """Persist an API payload as UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_json(path: Path) -> Any:
    """Load a UTF-8 JSON document."""
    return json.loads(path.read_text(encoding="utf-8"))


def save_csv(frame: pd.DataFrame, path: Path) -> Path:
    """Persist a dataframe as UTF-8 CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8")
    return path

