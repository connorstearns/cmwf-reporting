"""Insight and recommendation engine."""

from __future__ import annotations

from utils import metrics


def _trend_line(name: str, current: float | None, baseline: float | None) -> str:
    d = metrics.delta_text(current, baseline)
    if d == "n/a":
        return f"{name} is unavailable versus the selected baseline."
    return f"{name} changed {d} versus baseline."


def executive_insights(exec_now: dict, exec_base: dict) -> list[str]:
    bullets = [
        _trend_line("Total spend", exec_now.get("spend"), exec_base.get("spend")),
        _trend_line("Traffic volume", exec_now.get("traffic"), exec_base.get("traffic")),
        _trend_line("Lead volume", exec_now.get("leads"), exec_base.get("leads")),
        _trend_line("CPC efficiency", exec_now.get("cpc"), exec_base.get("cpc")),
    ]
    bullets.append(
        "Cross-platform delivery indicates where budget is concentrating; verify concentration aligns to strategic priorities."
    )
    return bullets[:5]


def platform_insights(platform: str, now: dict, base: dict) -> list[str]:
    lines = [
        _trend_line("Spend", now.get("spend"), base.get("spend")),
        _trend_line("Website visits", now.get("website_visits"), base.get("website_visits")),
        _trend_line("Leads", now.get("leads"), base.get("leads")),
        _trend_line("Cost per lead", now.get("cpl"), base.get("cpl")),
    ]
    if platform == "LinkedIn":
        lines.append(
            "Assess follower growth alongside lead output to confirm top-of-funnel investment remains balanced."
        )
    if platform == "Google":
        lines.append(
            "Search activity concentrated in limited topics suggests testing adjacent themes to diversify performance."
        )
    return lines[:5]


def objective_insights(platform: str, objective_df) -> list[str]:
    if objective_df is None or objective_df.empty:
        return [f"No objective-level activity found for {platform} in this period."]

    lines: list[str] = []
    spend_leader = objective_df.sort_values("spend", ascending=False).head(1)
    visits_leader = objective_df.sort_values("website_visits", ascending=False).head(1)
    leads_pool = objective_df[objective_df.get("leads", 0) > 0].copy()

    if not spend_leader.empty:
        row = spend_leader.iloc[0]
        lines.append(f"{row['objective']} consumed the largest share of {platform} spend this month.")
    if not visits_leader.empty:
        row = visits_leader.iloc[0]
        lines.append(f"{row['objective']} generated the most website visitors for {platform}.")
    if not leads_pool.empty:
        best_lead = leads_pool.sort_values("cpl", ascending=True).head(1).iloc[0]
        lines.append(f"{best_lead['objective']} delivered the strongest lead efficiency (lowest cost per lead).")

    if "Traffic" in objective_df["objective"].values:
        traffic = objective_df[objective_df["objective"] == "Traffic"].iloc[0]
        if traffic.get("website_visits", 0) > 0 and (traffic.get("lead_conversion_rate") or 0) < 0.02:
            lines.append("Traffic activity drove visits but low conversion, suggesting a landing-page and audience alignment review.")
    return lines[:5]


def objective_recommendations(platform: str, objective_df) -> list[str]:
    if objective_df is None or objective_df.empty:
        return [f"Maintain current {platform} strategy while objective tagging and attribution data accrues."]
    recs: list[str] = []
    if "Leads" in objective_df["objective"].values:
        leads = objective_df[objective_df["objective"] == "Leads"].iloc[0]
        if (leads.get("cpl") or 10**9) < (objective_df["cpl"].replace(0, float("nan")).mean(skipna=True) or 10**9):
            recs.append("Lead objective efficiency is favorable; test incremental budget scaling and additional creative variants.")
    if "Follows" in objective_df["objective"].values:
        follows = objective_df[objective_df["objective"] == "Follows"].iloc[0]
        if (follows.get("cost_per_follow") or 0) > 0:
            recs.append("If follow growth remains strategically important, refine messaging and creative before reducing investment.")
    recs.append("Review objective mix monthly to ensure upper-funnel spend is supporting downstream conversion outcomes.")
    return recs[:3]


def recommendations(platform: str | None = None) -> list[str]:
    if platform is None:
        return [
            "Shift incremental budget toward channels maintaining lead volume with stable or improving efficiency.",
            "Set monthly guardrails for CPC/CPL drift and trigger creative refresh when thresholds are exceeded.",
        ]
    return [
        f"Prioritize {platform} campaigns with stronger lead efficiency and sustain testing in underperforming segments.",
        "Refresh audience/creative combinations where traffic quality has softened relative to baseline.",
    ]


def slide_text(title: str, month_key: str, bullets: list[str], recs: list[str]) -> str:
    lines = [f"{title} — {month_key}", "", "Key insights:"]
    lines.extend([f"- {b}" for b in bullets])
    lines.append("")
    lines.append("Recommendations:")
    lines.extend([f"- {r}" for r in recs])
    return "\n".join(lines)
