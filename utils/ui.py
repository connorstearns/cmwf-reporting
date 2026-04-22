"""UI components and formatting helpers."""

from __future__ import annotations

import streamlit as st

from utils import config


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
        .kpi-card {background: #ffffff; border: 1px solid #e9ecef; border-radius: 12px; padding: 14px;}
        .subtle {color: #6c757d; font-size: 0.9rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def fmt_num(v) -> str:
    return "n/a" if v is None else f"{v:,.0f}"


def fmt_pct(v) -> str:
    return "n/a" if v is None else f"{v:.2%}"


def fmt_currency(v) -> str:
    return "n/a" if v is None else f"${v:,.2f}"


def metric_delta_color(metric: str, current: float | None, baseline: float | None) -> str:
    if current is None or baseline is None:
        return "gray"
    if current == baseline:
        return "gray"
    better_up = metric in config.HIGHER_IS_BETTER
    better_down = metric in config.LOWER_IS_BETTER
    if (better_up and current > baseline) or (better_down and current < baseline):
        return "green"
    return "red"


def render_bullets(title: str, bullets: list[str]) -> None:
    st.markdown(f"**{title}**")
    for b in bullets:
        st.markdown(f"- {b}")
