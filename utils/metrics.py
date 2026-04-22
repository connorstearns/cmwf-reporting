"""KPI calculations and comparison utilities."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

OBJECTIVES_BY_PLATFORM = {
    "Meta": ["Follows", "Leads", "Traffic"],
    "LinkedIn": ["Follows", "Leads", "Traffic", "Article"],
    "Google": ["Traffic"],
}


def safe_div(n: float, d: float) -> float | None:
    if d is None or pd.isna(d):
        return None
    try:
        if float(d) == 0:
            return None
    except (TypeError, ValueError):
        return None

    if n is None or pd.isna(n):
        return None

    try:
        return float(n) / float(d)
    except (TypeError, ValueError):
        return None


def month_slice(df: pd.DataFrame, month_key: str) -> pd.DataFrame:
    if df.empty or "month_key" not in df.columns:
        return df.iloc[0:0].copy()
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
    c = campaign[campaign["platform_norm"] == platform].copy()
    l = lp[lp["platform_norm"] == platform].copy()

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
    elif platform == "LinkedIn":
        base.update(
            {
                "followers_gained": follows,
                "cost_per_follower": safe_div(spend, follows),
                "engagement_rate": safe_div(shares, impressions),
            }
        )
    elif platform == "Google":
        base.update({"cpm": safe_div(spend * 1000, impressions)})

    return base


def _campaign_objective_rollup(campaign: pd.DataFrame, platform: str) -> pd.DataFrame:
    c = campaign[campaign["platform_norm"] == platform].copy()

    if c.empty:
        return pd.DataFrame(
            columns=[
                "objective",
                "campaign_name",
                "campaign_key",
                "spend",
                "impressions",
                "clicks",
                "leads",
                "follows",
                "shares",
            ]
        )

    grouped = (
        c.groupby(["objective", "campaign_name", "campaign_key"], as_index=False)
        .agg(
            spend=("cost", "sum"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            leads=("leads_newsletter", "sum"),
            follows=("follows_page_likes", "sum"),
            shares=("shares", "sum"),
        )
    )
    return grouped


def _lp_campaign_rollup(lp: pd.DataFrame, platform: str) -> pd.DataFrame:
    l = lp[lp["platform_norm"] == platform].copy()

    if l.empty:
        return pd.DataFrame(columns=["campaign_key", "website_visits"])

    return l.groupby("campaign_key", as_index=False).agg(
        website_visits=("sessions", "sum")
    )


def objective_breakdown(
    campaign: pd.DataFrame,
    lp: pd.DataFrame,
    platform: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build objective-level summary and campaign-detail tables.

    LP attribution assumption:
    join LP sessions to campaign feed by platform_norm + normalized campaign_key.
    """
    campaign_rollup = _campaign_objective_rollup(campaign, platform)
    lp_rollup = _lp_campaign_rollup(lp, platform)

    joined = campaign_rollup.merge(lp_rollup, on="campaign_key", how="left")
    joined["website_visits"] = joined["website_visits"].fillna(0.0)

    detail = joined.copy()

    summary = (
        joined.groupby("objective", as_index=False)
        .agg(
            spend=("spend", "sum"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            leads=("leads", "sum"),
            follows=("follows", "sum"),
            shares=("shares", "sum"),
            website_visits=("website_visits", "sum"),
        )
        .sort_values("spend", ascending=False)
    )

    summary["ctr"] = summary.apply(lambda row: safe_div(row["clicks"], row["impressions"]), axis=1)
    summary["cpc"] = summary.apply(lambda row: safe_div(row["spend"], row["clicks"]), axis=1)
    summary["cp_visit"] = summary.apply(lambda row: safe_div(row["spend"], row["website_visits"]), axis=1)
    summary["cpl"] = summary.apply(lambda row: safe_div(row["spend"], row["leads"]), axis=1)
    summary["lead_conversion_rate"] = summary.apply(
        lambda row: safe_div(row["leads"], row["website_visits"]), axis=1
    )
    summary["cost_per_follow"] = summary.apply(
        lambda row: safe_div(row["spend"], row["follows"]), axis=1
    )

    expected = OBJECTIVES_BY_PLATFORM.get(platform, [])
    if expected:
        idx = pd.DataFrame({"objective": expected})
        summary = idx.merge(summary, on="objective", how="left").fillna(
            {
                "spend": 0.0,
                "impressions": 0.0,
                "clicks": 0.0,
                "leads": 0.0,
                "follows": 0.0,
                "shares": 0.0,
                "website_visits": 0.0,
            }
        )

    return summary, detail


def objective_comparison(
    campaign_all: pd.DataFrame,
    lp_all: pd.DataFrame,
    selected_month: str,
    comparison_mode: str,
    platform: str,
) -> pd.DataFrame:
    selected_summary, _ = objective_breakdown(
        month_slice(campaign_all, selected_month),
        month_slice(lp_all, selected_month),
        platform,
    )

    if comparison_mode == "Previous Month":
        comp_months = [str(pd.Period(selected_month, "M") - 1)]
    else:
        comp_months = trailing_months(selected_month, 3)

    all_comp = []
    for month in comp_months:
        comp_summary, _ = objective_breakdown(
            month_slice(campaign_all, month),
            month_slice(lp_all, month),
            platform,
        )
        all_comp.append(comp_summary.assign(month_key=month))

    if all_comp:
        comp_df = pd.concat(all_comp, ignore_index=True)
        baseline = comp_df.groupby("objective", as_index=False).mean(numeric_only=True)
    else:
        baseline = pd.DataFrame(columns=selected_summary.columns)

    merged = selected_summary.merge(
        baseline.add_prefix("baseline_"),
        left_on="objective",
        right_on="baseline_objective",
        how="left",
    ).drop(columns=["baseline_objective"], errors="ignore")

    merged["spend_delta"] = merged.apply(
        lambda row: delta_text(row.get("spend"), row.get("baseline_spend")),
        axis=1,
    )
    merged["website_visits_delta"] = merged.apply(
        lambda row: delta_text(row.get("website_visits"), row.get("baseline_website_visits")),
        axis=1,
    )
    merged["cpl_delta"] = merged.apply(
        lambda row: delta_text(row.get("cpl"), row.get("baseline_cpl")),
        axis=1,
    )
    merged["cp_visit_delta"] = merged.apply(
        lambda row: delta_text(row.get("cp_visit"), row.get("baseline_cp_visit")),
        axis=1,
    )

    return merged


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
            baseline = aggregate_platform(
                month_slice(campaign_all, comp_month),
                month_slice(lp_all, comp_month),
                platform,
            )
        else:
            baseline = aggregate_exec(
                month_slice(campaign_all, comp_month),
                month_slice(lp_all, comp_month),
            )
        baseline_value = baseline.get(metric_name)
    else:
        months = trailing_months(selected_month, 3)
        values = []

        for month in months:
            if platform:
                current = aggregate_platform(
                    month_slice(campaign_all, month),
                    month_slice(lp_all, month),
                    platform,
                )
            else:
                current = aggregate_exec(
                    month_slice(campaign_all, month),
                    month_slice(lp_all, month),
                )

            value = current.get(metric_name)
            if value is not None and not (isinstance(value, float) and math.isnan(value)):
                values.append(value)

        baseline_value = float(np.mean(values)) if values else None

    return selected_value, baseline_value


def delta_text(current: float | None, baseline: float | None) -> str:
    if current is None or baseline is None:
        return "n/a"
    if baseline == 0:
        return "n/a"
    return f"{((current - baseline) / baseline):+.1%}"
