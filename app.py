from __future__ import annotations

import pandas as pd
import streamlit as st

from utils import classification, config, insights, metrics
from utils.charts import campaign_scatter, spend_by_platform_chart
from utils.data_loader import load_data

st.set_page_config(page_title="CMWF Paid Media Dashboard", layout="wide")
st.title("Commonwealth Fund Monthly Paid Media Dashboard")
st.caption("Executive-ready monthly reporting for Meta, LinkedIn, and Google.")

with st.sidebar:
    st.header("Configuration")
    source = st.selectbox(
        "Data Source",
        options=["google_sheets", "excel"],
        index=0 if config.DATA_SOURCE == "google_sheets" else 1,
        help="Google Sheets is the production default. Excel is a fallback.",
    )
    sheet_url = st.text_input("Google Sheet URL", value=config.GOOGLE_SHEET_URL)
    excel_path = st.text_input("Excel File Path", value=config.EXCEL_FILE_PATH)

try:
    data, source_used = load_data(source=source, sheet_url=sheet_url, excel_file_path=excel_path)
except Exception as exc:
    st.error(f"Failed to load reporting data: {exc}")
    st.stop()

st.success(f"Loaded data from: {source_used}")

campaign = data["Campaign Master Feed"].copy()
ga4 = data["GA4 Master Feed"].copy()
lp_weekly = data["LP Master Feed (Weekly)"].copy()

if "platform" in campaign.columns:
    campaign["platform_norm"] = campaign["platform"].apply(classification.normalize_platform_name)
else:
    campaign["platform_norm"] = "Unknown"

campaign = classification.add_month_key(campaign, "date")
ga4 = classification.add_month_key(ga4, "date")
lp_weekly = classification.add_month_key(lp_weekly, "week_start")

available_months = sorted([m for m in campaign.get("month_key", pd.Series(dtype=str)).dropna().unique()], reverse=True)
if not available_months:
    st.warning("No valid monthly data found after parsing dates.")
    st.stop()

selected_month = st.selectbox("Reporting Month", options=available_months, index=0)
prev_month = available_months[1] if len(available_months) > 1 else None

campaign_month = campaign[campaign["month_key"] == selected_month].copy()
ga4_month = ga4[ga4["month_key"] == selected_month].copy()
lp_month = lp_weekly[lp_weekly["month_key"] == selected_month].copy()

overall = metrics.summarize_campaign_month(campaign_month)
platform_summary = metrics.summarize_platform(campaign_month)
ga4_summary = metrics.summarize_ga4_month(ga4_month)

st.header("1) Monthly Executive Summary")
kpi_cols = st.columns(5)
kpi_cols[0].metric("Spend", f"${overall['spend']:,.0f}")
kpi_cols[1].metric("Impressions", f"{overall['impressions']:,.0f}")
kpi_cols[2].metric("Clicks", f"{overall['clicks']:,.0f}")
kpi_cols[3].metric("CTR", f"{overall['ctr']:.2%}")
kpi_cols[4].metric("CPC", f"${overall['cpc']:.2f}")

if prev_month:
    prev_campaign = campaign[campaign["month_key"] == prev_month]
    prev_overall = metrics.summarize_campaign_month(prev_campaign)
    mo_cols = st.columns(3)
    mo_cols[0].metric("MoM Spend", f"${overall['spend'] - prev_overall['spend']:,.0f}")
    mo_cols[1].metric("MoM Clicks", f"{overall['clicks'] - prev_overall['clicks']:,.0f}")
    mo_cols[2].metric("MoM Leads", f"{overall['leads'] - prev_overall['leads']:,.0f}")

st.plotly_chart(spend_by_platform_chart(platform_summary), use_container_width=True)
exec_text = insights.executive_insights(selected_month, overall, platform_summary, ga4_summary)
st.markdown("**Executive Insight**")
st.write(exec_text)
st.download_button(
    "Download Executive Summary Text",
    data=exec_text,
    file_name=f"executive_summary_{selected_month}.txt",
)

for idx, platform_name in enumerate(["Meta", "LinkedIn", "Google"], start=2):
    st.header(f"{idx}) {platform_name} Campaign Performance")
    pf = platform_summary[platform_summary["platform_norm"] == platform_name]
    if pf.empty:
        st.info(f"No data for {platform_name} in {selected_month}.")
        continue
    row = pf.iloc[0].to_dict()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Spend", f"${row['spend']:,.0f}")
    c2.metric("Clicks", f"{row['clicks']:,.0f}")
    c3.metric("CTR", f"{row['ctr']:.2%}")
    c4.metric("CPL", f"${row['cpl']:.2f}")

    st.plotly_chart(campaign_scatter(campaign_month, platform_name), use_container_width=True)
    p_text = insights.platform_insights(platform_name, selected_month, row)
    st.write(p_text)
    st.download_button(
        f"Download {platform_name} Slide Text",
        data=p_text,
        file_name=f"{platform_name.lower()}_summary_{selected_month}.txt",
    )

with st.expander("Supporting Data Tables"):
    st.subheader("Campaign Master Feed (Selected Month)")
    st.dataframe(campaign_month, use_container_width=True)
    st.subheader("GA4 Master Feed (Selected Month)")
    st.dataframe(ga4_month, use_container_width=True)
    st.subheader("LP Master Feed Weekly (Selected Month)")
    st.dataframe(lp_month, use_container_width=True)
