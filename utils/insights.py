"""Insight and summary text generation for slide-ready exports."""

from __future__ import annotations

import pandas as pd


def executive_insights(month_key: str, overall: dict, platform_df: pd.DataFrame, ga4: dict) -> str:
    top_platform = "N/A"
    if not platform_df.empty:
        top_platform = platform_df.sort_values("spend", ascending=False).iloc[0]["platform_norm"]

    return (
        f"{month_key} paid media delivered {overall['impressions']:,.0f} impressions and "
        f"{overall['clicks']:,.0f} clicks on ${overall['spend']:,.0f} spend (CTR {overall['ctr']:.2%}, "
        f"CPC ${overall['cpc']:.2f}). Top spend platform was {top_platform}. "
        f"GA4 recorded {ga4['paid_traffic']:,.0f} paid sessions, {ga4['newsletter_signups']:,.0f} newsletter signups, "
        f"and {ga4['file_downloads']:,.0f} file downloads. Recommendation: prioritize creatives and audiences "
        "from the highest CTR campaigns while reducing budget on high-CPC, low-conversion segments."
    )


def platform_insights(platform_name: str, month_key: str, metrics: dict) -> str:
    return (
        f"{platform_name} in {month_key}: spend ${metrics['spend']:,.0f}, impressions {metrics['impressions']:,.0f}, "
        f"clicks {metrics['clicks']:,.0f}, leads/newsletter {metrics['leads']:,.0f}, CTR {metrics['ctr']:.2%}, "
        f"CPC ${metrics['cpc']:.2f}, CPL ${metrics['cpl']:.2f}. Recommendation: scale campaigns with strongest "
        "CTR and lead efficiency, and refresh low-engagement creative sets for next month."
    )
