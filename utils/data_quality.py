"""Lightweight validation used before exploratory analysis."""
from __future__ import annotations

from typing import Any

import pandas as pd


def quality_summary(
    primary: pd.DataFrame,
    comments: pd.DataFrame,
    id_column: str,
    *,
    failed_requests: int = 0,
    records_skipped: int = 0,
) -> dict[str, Any]:
    """Calculate transparent, non-analytical readiness checks."""
    reply_count = int(comments.get("is_reply", pd.Series(dtype=bool)).fillna(False).astype(bool).sum())
    return {
        "Primary objects": len(primary),
        "Comments": len(comments),
        "Replies": reply_count,
        "Fields": len(primary.columns),
        "Missing values": int(primary.isna().sum().sum() + comments.isna().sum().sum()),
        "Duplicate IDs": int(primary.duplicated(id_column).sum()) if id_column in primary else 0,
        "Failed requests": failed_requests,
        "Records skipped": records_skipped,
    }


def remove_duplicate_ids(frame: pd.DataFrame, id_column: str) -> pd.DataFrame:
    """Keep the first record for each non-null unique identifier."""
    return frame.drop_duplicates(subset=[id_column], keep="first").reset_index(drop=True)

