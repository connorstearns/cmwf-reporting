from __future__ import annotations

import pandas as pd
import streamlit as st

from utils import charts, classification, config, insights, metrics, qa, ui
from utils.data_loader import load_data

st.set_page_config(page_title="CMWF Monthly Paid Media", layout="wide")
ui.inject_styles()
st.title("Commonwealth Fund Monthly Paid Media Report")
st.caption("Executive dashboard for monthly leadership reporting.")

sheet_url = st.secrets.get("google_sheet_url", config.GOOGLE_SHEET_URL_DEFAULT)

try:
    data = load_data(sheet_url)
except Exception as exc:
    st.error(f"Failed to load Google Sheets data: {exc}")
    st.stop()

campaign_raw = data["Campaign Master Feed"]
ga4 = data["GA4 Master Feed"]
lp_raw = data["LP Master Feed (Weekly)"]
campaign, lp = classification.add_classifications(campaign_raw, lp_raw)

all_months = sorted([m for m in campaign["month_key"].dropna().unique() if m != "NaT"], reverse=True)
if not all_months:
    st.error("No valid month data found in Campaign Master Feed.")
    st.stop()

today = pd.Timestamp.utcnow()
current_month = str(today.to_period("M"))
default_month = next((m for m in all_months if m < current_month), all_months[0])

with st.sidebar:
    st.header("Report Controls")
    selected_month = st.selectbox("Reporting Month", options=all_months, index=all_months.index(default_month))
    comparison_mode = st.selectbox("Comparison Mode", options=config.COMPARISON_MODES, index=0)

selected_campaign = metrics.month_slice(campaign, selected_month)
selected_lp = metrics.month_slice(lp, selected_month)

exec_now = metrics.aggregate_exec(selected_campaign, selected_lp)
if comparison_mode == "Previous Month":
    base_month = str(pd.Period(selected_month, "M") - 1)
else:
    base_month = "Trailing 3-Month Avg"

if comparison_mode == "Previous Month":
    exec_base = metrics.aggregate_exec(
        metrics.month_slice(campaign, str(pd.Period(selected_month, "M") - 1)),
        metrics.month_slice(lp, str(pd.Period(selected_month, "M") - 1)),
    )
else:
    months = metrics.trailing_months(selected_month, 3)
    rows = [
        metrics.aggregate_exec(metrics.month_slice(campaign, m), metrics.month_slice(lp, m)) for m in months
    ]
    exec_base = {k: pd.Series([r.get(k) for r in rows], dtype="float").mean() for k in rows[0].keys()} if rows else {}

platform_tabs = st.tabs(["Executive Summary", "Meta", "LinkedIn", "Google", "Data QA"])

with platform_tabs[0]:
    st.subheader(f"Executive Summary — {selected_month}")
    st.markdown(f"<span class='subtle'>Comparison baseline: {comparison_mode} ({base_month})</span>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Spend", ui.fmt_currency(exec_now["spend"]), metrics.delta_text(exec_now["spend"], exec_base.get("spend")))
    c2.metric("Impressions", ui.fmt_num(exec_now["impressions"]), metrics.delta_text(exec_now["impressions"], exec_base.get("impressions")))
    c3.metric("Clicks", ui.fmt_num(exec_now["clicks"]), metrics.delta_text(exec_now["clicks"], exec_base.get("clicks")))
    c4.metric("CTR", ui.fmt_pct(exec_now["ctr"]), metrics.delta_text(exec_now["ctr"], exec_base.get("ctr")))
    c5.metric("CPC", ui.fmt_currency(exec_now["cpc"]), metrics.delta_text(exec_now["cpc"], exec_base.get("cpc")))
    c6.metric("Leads", ui.fmt_num(exec_now["leads"]), metrics.delta_text(exec_now["leads"], exec_base.get("leads")))

    platform_compare = selected_campaign.groupby("platform_norm", as_index=False).agg(
        cost=("cost", "sum"), clicks=("clicks", "sum"), leads=("leads_newsletter", "sum"), impressions=("impressions", "sum")
    )
    st.plotly_chart(charts.spend_mix(platform_compare), use_container_width=True)
    st.plotly_chart(charts.monthly_trend(campaign, "cost", "Spend Trend"), use_container_width=True)
    e_bullets = insights.executive_insights(exec_now, exec_base)
    e_recs = insights.recommendations(None)
    ui.render_bullets("Executive insights", e_bullets)
    ui.render_bullets("Executive recommendations", e_recs)
    txt = insights.slide_text("Monthly Executive Summary", selected_month, e_bullets, e_recs)
    st.download_button("Download slide-ready summary text", txt, file_name=f"executive_summary_{selected_month}.txt")


def render_platform_tab(platform: str, tab_idx: int) -> None:
    with platform_tabs[tab_idx]:
        st.subheader(f"{platform} Campaign Performance — {selected_month}")
        p_now = metrics.aggregate_platform(selected_campaign, selected_lp, platform)
        p_base = {}
        for mname in p_now.keys():
            cur, base = metrics.comparison_value(
                mname, p_now, campaign, lp, selected_month, comparison_mode, platform=platform
            )
            p_base[mname] = base

        if platform == "Meta":
            cards = [
                ("Page Likes Gained", "page_likes_gained"),
                ("Cost per Page Like", "cost_per_page_like"),
                ("Cost per Outbound Click", "cost_per_outbound_click"),
                ("Website Visits", "website_visits"),
                ("Cost per Website Visit", "cp_visit"),
                ("Cost per Lead", "cpl"),
                ("Lead Conversion Rate", "lead_conversion_rate"),
            ]
        elif platform == "LinkedIn":
            cards = [
                ("Followers Gained", "followers_gained"),
                ("Cost per Follower", "cost_per_follower"),
                ("Cost per Click", "cpc"),
                ("Engagement Rate", "engagement_rate"),
                ("Cost per Lead", "cpl"),
                ("Lead Conversion Rate", "lead_conversion_rate"),
            ]
        else:
            cards = [
                ("Impressions", "impressions"),
                ("CPM", "cpm"),
                ("CPC", "cpc"),
                ("Website Visits", "website_visits"),
                ("Cost per Website Visit", "cp_visit"),
            ]

        cols = st.columns(min(4, len(cards)))
        for i, (label, key) in enumerate(cards):
            val = p_now.get(key)
            baseline = p_base.get(key)
            delta = metrics.delta_text(val, baseline)
            if "rate" in key or key == "ctr":
                display = ui.fmt_pct(val)
            elif "cost" in key or key in {"cpc", "cpl", "cpm", "cp_visit"}:
                display = ui.fmt_currency(val)
            else:
                display = ui.fmt_num(val)
            cols[i % len(cols)].metric(label, display, delta)

        p_campaign = selected_campaign[selected_campaign["platform_norm"] == platform].copy()
        p_lp = selected_lp[selected_lp["platform_norm"] == platform].copy()
        st.plotly_chart(charts.monthly_trend(campaign[campaign["platform_norm"] == platform], "cost", f"{platform} Spend Trend"), use_container_width=True)

        if platform == "Meta":
            st.plotly_chart(charts.campaign_breakdown(p_campaign, "leads_newsletter", "Top Meta Lead-Generating Ad/Creative", name_col="ad_creative_id"), use_container_width=True)
        if platform == "Google":
            p_campaign["topic_bucket"] = p_campaign["campaign_name"].apply(classification.classify_google_topic)
            st.plotly_chart(charts.topic_breakdown(p_campaign), use_container_width=True)

        st.plotly_chart(charts.campaign_breakdown(p_campaign, "cost", f"{platform} Campaign Spend Breakdown"), use_container_width=True)
        st.dataframe(p_campaign.sort_values("cost", ascending=False), use_container_width=True)

        p_bullets = insights.platform_insights(platform, p_now, p_base)
        p_recs = insights.recommendations(platform)
        ui.render_bullets("Key insights", p_bullets)
        ui.render_bullets("Recommendations", p_recs)
        ptxt = insights.slide_text(f"{platform} Campaign Performance", selected_month, p_bullets, p_recs)
        st.download_button(f"Download {platform} slide-ready text", ptxt, file_name=f"{platform.lower()}_{selected_month}.txt")


render_platform_tab("Meta", 1)
render_platform_tab("LinkedIn", 2)
render_platform_tab("Google", 3)

with platform_tabs[4]:
    st.subheader("Data QA")
    unclassified = selected_lp[selected_lp["platform_norm"] == "Unclassified"]
    qa_summary = qa.build_qa_summary(data, selected_month, unclassified)
    st.write({"selected_reporting_month": qa_summary["selected_month"], "unclassified_lp_rows": qa_summary["unclassified_count"]})
    st.markdown("**Worksheet Health**")
    st.dataframe(pd.DataFrame(qa_summary["sheets"]).T, use_container_width=True)
    st.markdown("**Missing Required Columns**")
    st.json(qa_summary["missing_required_columns"])
    st.markdown("**Date Parsing Issues (NaT count)**")
    st.json(qa_summary["date_parsing_issues"])
    st.markdown("**Unclassified LP rows (sample)**")
    st.dataframe(unclassified.head(50), use_container_width=True)

    warnings = qa.denominator_warnings(exec_now)
    if warnings:
        st.markdown("**Null/Zero-denominator warnings**")
        for w in warnings:
            st.warning(w)
