"""Data QA checks for month completeness and schema health."""

from __future__ import annotations

import pandas as pd

from utils import config


def latest_date(df: pd.DataFrame) -> pd.Timestamp | None:
    for col in ["date", "week_start"]:
        if col in df.columns:
            dt = pd.to_datetime(df[col], errors="coerce")
            if dt.notna().any():
                return dt.max()
    return None


def missing_columns(df: pd.DataFrame, required: list[str]) -> list[str]:
    return [c for c in required if c not in df.columns]


def month_status(latest_dt: pd.Timestamp | None, today: pd.Timestamp) -> str:
    if latest_dt is None:
        return "unknown"
    month_end = latest_dt.to_period("M").end_time.normalize()
    return "complete" if latest_dt.normalize() >= month_end else "partial"


def denominator_warnings(metrics_dict: dict) -> list[str]:
    warns = []
    for k, v in metrics_dict.items():
        if v is None:
            warns.append(f"{k} has null value due to zero/missing denominator.")
    return warns


def build_qa_summary(data: dict[str, pd.DataFrame], selected_month: str, unclassified_lp: pd.DataFrame) -> dict:
    today = pd.Timestamp.utcnow().normalize()
    summary = {
        "selected_month": selected_month,
        "sheets": {},
        "unclassified_count": len(unclassified_lp),
        "missing_required_columns": {},
        "date_parsing_issues": {},
    }
    for tab, df in data.items():
        ldt = latest_date(df)
        summary["sheets"][tab] = {
            "rows": int(len(df)),
            "latest_date": ldt,
            "latest_month_status": month_status(ldt, today),
        }
        summary["missing_required_columns"][tab] = missing_columns(df, config.EXPECTED_COLUMNS[tab])
        date_col = "date" if "date" in df.columns else "week_start"
        if date_col in df.columns:
            summary["date_parsing_issues"][tab] = int(df[date_col].isna().sum())
        else:
            summary["date_parsing_issues"][tab] = len(df)
    return summary
