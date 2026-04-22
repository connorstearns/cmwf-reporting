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


def objective_qa(campaign: pd.DataFrame, lp: pd.DataFrame) -> dict:
    out: dict = {}
    missing_objective = campaign[campaign["objective"].isna() | (campaign["objective"] == "Unclassified")]
    out["missing_objective_campaigns"] = missing_objective[
        ["platform_norm", "campaign_name", "objective"]
    ].drop_duplicates()
    out["objective_counts_by_platform"] = (
        campaign.groupby(["platform_norm", "objective"], as_index=False).size().rename(columns={"size": "campaign_count"})
    )

    expected = {
        "Meta": ["Follows", "Leads", "Traffic"],
        "LinkedIn": ["Follows", "Leads", "Traffic", "Article"],
        "Google": ["Traffic"],
    }
    combos = []
    for platform, objectives in expected.items():
        for obj in objectives:
            combos.append({"platform_norm": platform, "objective": obj})
    expected_df = pd.DataFrame(combos)
    activity = campaign.groupby(["platform_norm", "objective"], as_index=False).agg(cost=("cost", "sum"))
    out["platform_objective_no_activity"] = expected_df.merge(activity, on=["platform_norm", "objective"], how="left")
    out["platform_objective_no_activity"] = out["platform_objective_no_activity"][
        out["platform_objective_no_activity"]["cost"].fillna(0) <= 0
    ]

    mapped_keys = campaign[["platform_norm", "campaign_key"]].drop_duplicates()
    lp_keys = lp[["platform_norm", "campaign_key", "sessions"]].copy()
    unmatched = lp_keys.merge(mapped_keys, on=["platform_norm", "campaign_key"], how="left", indicator=True)
    out["lp_unmatched_for_objective"] = unmatched[unmatched["_merge"] == "left_only"].drop(columns=["_merge"])
    return out
