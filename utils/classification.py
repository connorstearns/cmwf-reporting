"""Classification helpers for platform and month handling."""

from __future__ import annotations

import pandas as pd


def normalize_platform_name(platform: str) -> str:
    if not isinstance(platform, str):
        return "Other"
    p = platform.strip().lower()
    if "meta" in p or "facebook" in p or "instagram" in p:
        return "Meta"
    if "linkedin" in p or "linked in" in p:
        return "LinkedIn"
    if "google" in p or "search" in p or "youtube" in p:
        return "Google"
    return platform.strip().title()


def add_month_key(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    out = df.copy()
    if date_col in out.columns:
        out["month_key"] = pd.to_datetime(out[date_col], errors="coerce").dt.to_period("M").astype(str)
    elif {"year", "month"}.issubset(set(out.columns)):
        out["month_key"] = out["year"].astype(str) + "-" + pd.to_datetime(out["month"], format="%b", errors="coerce").dt.month.astype("Int64").astype(str).str.zfill(2)
    return out
