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
