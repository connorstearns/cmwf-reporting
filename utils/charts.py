"""Chart helpers for the paid media dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px


def spend_by_platform_chart(df_platform: pd.DataFrame):
    chart_df = df_platform.copy()
    if chart_df.empty:
        return px.bar(title="No platform data available")
    return px.bar(
        chart_df,
        x="platform_norm",
        y="spend",
        text_auto=".2s",
        title="Monthly Spend by Platform",
        labels={"platform_norm": "Platform", "spend": "Spend ($)"},
    )


def campaign_scatter(df_campaign: pd.DataFrame, platform_name: str):
    subset = df_campaign[df_campaign["platform_norm"] == platform_name].copy()
    if subset.empty:
        return px.scatter(title=f"No campaign data available for {platform_name}")

    grouped = (
        subset.groupby("campaign_name", dropna=False)
        .agg(spend=("cost", "sum"), clicks=("clicks", "sum"), impressions=("impressions", "sum"), leads=("leads_newsletter", "sum"))
        .reset_index()
    )
    return px.scatter(
        grouped,
        x="spend",
        y="clicks",
        size="impressions",
        color="leads",
        hover_name="campaign_name",
        title=f"{platform_name}: Campaign Spend vs Clicks",
    )
