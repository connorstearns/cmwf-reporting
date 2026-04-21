"""Metric calculations for executive and platform reporting."""

from __future__ import annotations

import numpy as np
import pandas as pd


def safe_divide(a: float, b: float) -> float:
    if b in (0, None) or (isinstance(b, float) and np.isnan(b)):
        return 0.0
    return float(a) / float(b)


def summarize_campaign_month(df_campaign: pd.DataFrame) -> dict:
    totals = {
        "spend": float(df_campaign.get("cost", pd.Series(dtype=float)).sum()),
        "impressions": float(df_campaign.get("impressions", pd.Series(dtype=float)).sum()),
        "clicks": float(df_campaign.get("clicks", pd.Series(dtype=float)).sum()),
        "leads": float(df_campaign.get("leads_newsletter", pd.Series(dtype=float)).sum()),
        "shares": float(df_campaign.get("shares", pd.Series(dtype=float)).sum()),
        "follows": float(df_campaign.get("follows_page_likes", pd.Series(dtype=float)).sum()),
    }
    totals["ctr"] = safe_divide(totals["clicks"], totals["impressions"])
    totals["cpc"] = safe_divide(totals["spend"], totals["clicks"])
    totals["cpl"] = safe_divide(totals["spend"], totals["leads"])
    return totals


def summarize_platform(df_campaign_month: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df_campaign_month.groupby("platform_norm", dropna=False)
        .agg(
            spend=("cost", "sum"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            leads=("leads_newsletter", "sum"),
            shares=("shares", "sum"),
            follows=("follows_page_likes", "sum"),
        )
        .reset_index()
    )
    grouped["ctr"] = grouped.apply(lambda r: safe_divide(r["clicks"], r["impressions"]), axis=1)
    grouped["cpc"] = grouped.apply(lambda r: safe_divide(r["spend"], r["clicks"]), axis=1)
    grouped["cpl"] = grouped.apply(lambda r: safe_divide(r["spend"], r["leads"]), axis=1)
    return grouped.sort_values("spend", ascending=False)


def summarize_ga4_month(df_ga4_month: pd.DataFrame) -> dict:
    return {
        "paid_traffic": float(df_ga4_month.get("paid_traffic", pd.Series(dtype=float)).sum()),
        "direct_referral_traffic": float(df_ga4_month.get("direct_referral_traffic", pd.Series(dtype=float)).sum()),
        "organic_traffic": float(df_ga4_month.get("organic_traffic", pd.Series(dtype=float)).sum()),
        "scrolls": float(df_ga4_month.get("scrolls", pd.Series(dtype=float)).sum()),
        "shares": float(df_ga4_month.get("shares", pd.Series(dtype=float)).sum()),
        "newsletter_signups": float(df_ga4_month.get("newsletter_signups", pd.Series(dtype=float)).sum()),
        "file_downloads": float(df_ga4_month.get("file_downloads", pd.Series(dtype=float)).sum()),
    }
