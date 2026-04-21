"""Application configuration for the CMWF paid media dashboard."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    data_source: str = "google_sheets"
    google_sheet_url: str = (
        "https://docs.google.com/spreadsheets/d/11-pQ2uFJkz5UgY5Tf2sPdc_K12-o0VGbb-whWGtxUpw/edit?gid=924758410#gid=924758410"
    )
    excel_file_path: str = "CMWF - Master Data File.xlsx"


DATA_SOURCE = os.getenv("DATA_SOURCE", "google_sheets")
GOOGLE_SHEET_URL = os.getenv(
    "GOOGLE_SHEET_URL",
    "https://docs.google.com/spreadsheets/d/11-pQ2uFJkz5UgY5Tf2sPdc_K12-o0VGbb-whWGtxUpw/edit?gid=924758410#gid=924758410",
)
EXCEL_FILE_PATH = os.getenv("EXCEL_FILE_PATH", "CMWF - Master Data File.xlsx")

REQUIRED_TABS = [
    "Campaign Master Feed",
    "GA4 Master Feed",
    "LP Master Feed (Weekly)",
]

CAMPAIGN_NUMERIC_COLUMNS = [
    "cost",
    "impressions",
    "clicks",
    "leads_newsletter",
    "shares",
    "follows_page_likes",
]

GA4_NUMERIC_COLUMNS = [
    "paid_traffic",
    "direct_referral_traffic",
    "organic_traffic",
    "scrolls",
    "shares",
    "newsletter_signups",
    "file_downloads",
]

LP_NUMERIC_COLUMNS = ["sessions", "active_users", "engaged_sessions", "views"]

KNOWN_DATE_COLUMNS = ["date", "week_start"]

PLATFORM_DISPLAY_ORDER = ["Meta", "LinkedIn", "Google"]
