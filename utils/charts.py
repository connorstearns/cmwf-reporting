"""Plotly chart helpers for executive-style visuals."""

from __future__ import annotations

import pandas as pd
import plotly.express as px


def spend_mix(df: pd.DataFrame):
    if df.empty:
        return px.pie(title="No spend data")
    return px.pie(df, names="platform_norm", values="cost", hole=0.45, title="Spend Mix by Platform")


def monthly_trend(df: pd.DataFrame, y: str, title: str):
    if df.empty:
        return px.line(title=f"{title} (No data)")
    t = df.groupby("month_key", as_index=False)[y].sum().sort_values("month_key")
    return px.line(t, x="month_key", y=y, markers=True, title=title)


def campaign_breakdown(df: pd.DataFrame, value_col: str, title: str, name_col: str = "campaign_name"):
    if df.empty or name_col not in df.columns:
        return px.bar(title=f"{title} (No data)")
    top = df.groupby(name_col, as_index=False)[value_col].sum().sort_values(value_col, ascending=False).head(10)
    return px.bar(top, x=name_col, y=value_col, title=title)


def topic_breakdown(df: pd.DataFrame):
    if df.empty:
        return px.bar(title="Topic Breakdown (No data)")
    grouped = df.groupby("topic_bucket", as_index=False)["cost"].sum().sort_values("cost", ascending=False)
    return px.bar(grouped, x="topic_bucket", y="cost", title="Google Topic Spend Breakdown")


def objective_breakdown_chart(df: pd.DataFrame, value_col: str, title: str):
    if df.empty or "objective" not in df.columns or value_col not in df.columns:
        return px.bar(title=f"{title} (No data)")
    return px.bar(df, x="objective", y=value_col, title=title)
