"""KPI calculations and comparison utilities."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def safe_div(n: float, d: float) -> float | None:
    if d is None or pd.isna(d) or float(d) == 0:
        return None
    if n is None or pd.isna(n):
        return None
    return float(n) / float(d)


def month_slice(df: pd.DataFrame, month_key: str) -> pd.DataFrame:
    return df[df["month_key"] == month_key].copy()


def trailing_months(month_key: str, n: int = 3) -> list[str]:
    period = pd.Period(month_key, freq="M")
    return [str(period - i) for i in range(1, n + 1)]


def aggregate_exec(campaign: pd.DataFrame, lp: pd.DataFrame) -> dict:
    spend = campaign.get("cost", pd.Series(dtype=float)).sum()
    impressions = campaign.get("impressions", pd.Series(dtype=float)).sum()
    clicks = campaign.get("clicks", pd.Series(dtype=float)).sum()
    leads = campaign.get("leads_newsletter", pd.Series(dtype=float)).sum()
    traffic = lp.get("sessions", pd.Series(dtype=float)).sum()
    return {
        "spend": spend,
        "impressions": impressions,
        "clicks": clicks,
        "ctr": safe_div(clicks, impressions),
        "cpc": safe_div(spend, clicks),
        "leads": leads,
        "traffic": traffic,
    }


def aggregate_platform(campaign: pd.DataFrame, lp: pd.DataFrame, platform: str) -> dict:
    c = campaign[campaign["platform_norm"] == platform]
    l = lp[lp["platform_norm"] == platform]

    spend = c.get("cost", pd.Series(dtype=float)).sum()
    impressions = c.get("impressions", pd.Series(dtype=float)).sum()
    clicks = c.get("clicks", pd.Series(dtype=float)).sum()
    leads = c.get("leads_newsletter", pd.Series(dtype=float)).sum()
    follows = c.get("follows_page_likes", pd.Series(dtype=float)).sum()
    shares = c.get("shares", pd.Series(dtype=float)).sum()
    visits = l.get("sessions", pd.Series(dtype=float)).sum()

    base = {
        "spend": spend,
        "impressions": impressions,
        "clicks": clicks,
        "leads": leads,
        "follows": follows,
        "shares": shares,
        "website_visits": visits,
        "ctr": safe_div(clicks, impressions),
        "cpc": safe_div(spend, clicks),
        "cpl": safe_div(spend, leads),
        "cp_visit": safe_div(spend, visits),
        "lead_conversion_rate": safe_div(leads, visits),
    }
    if platform == "Meta":
        base.update(
            {
                "page_likes_gained": follows,
                "cost_per_page_like": safe_div(spend, follows),
                "cost_per_outbound_click": safe_div(spend, clicks),
            }
        )
    if platform == "LinkedIn":
        base.update(
            {
                "followers_gained": follows,
                "cost_per_follower": safe_div(spend, follows),
                "engagement_rate": safe_div(shares, impressions),
            }
        )
    if platform == "Google":
        base.update({"cpm": safe_div(spend * 1000, impressions)})
    return base


def comparison_value(
    metric_name: str,
    selected: dict,
    campaign_all: pd.DataFrame,
    lp_all: pd.DataFrame,
    selected_month: str,
    comparison_mode: str,
    platform: str | None = None,
) -> tuple[float | None, float | None]:
    selected_value = selected.get(metric_name)
    if comparison_mode == "Previous Month":
        comp_month = str(pd.Period(selected_month, "M") - 1)
        if platform:
            baseline = aggregate_platform(month_slice(campaign_all, comp_month), month_slice(lp_all, comp_month), platform)
        else:
            baseline = aggregate_exec(month_slice(campaign_all, comp_month), month_slice(lp_all, comp_month))
        baseline_value = baseline.get(metric_name)
    else:
        months = trailing_months(selected_month, 3)
        values = []
        for m in months:
            if platform:
                cur = aggregate_platform(month_slice(campaign_all, m), month_slice(lp_all, m), platform)
            else:
                cur = aggregate_exec(month_slice(campaign_all, m), month_slice(lp_all, m))
            val = cur.get(metric_name)
            if val is not None and not (isinstance(val, float) and math.isnan(val)):
                values.append(val)
        baseline_value = float(np.mean(values)) if values else None
    return selected_value, baseline_value


def delta_text(current: float | None, baseline: float | None) -> str:
    if current is None or baseline is None:
        return "n/a"
    if baseline == 0:
        return "n/a"
    return f"{((current-baseline)/baseline):+.1%}"
