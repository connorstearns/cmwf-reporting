"""Application configuration for the CMWF paid media dashboard."""

from __future__ import annotations

import os


GOOGLE_SHEET_URL = os.getenv(
    "GOOGLE_SHEET_URL",
    "https://docs.google.com/spreadsheets/d/11-pQ2uFJkz5UgY5Tf2sPdc_K12-o0VGbb-whWGtxUpw/edit?gid=924758410#gid=924758410",
)

REQUIRED_TABS = [
    "Campaign Master Feed",
    "GA4 Master Feed",
    "LP Master Feed (Weekly)",
]

KNOWN_DATE_COLUMNS = ["date", "week_start"]

PLATFORM_DISPLAY_ORDER = ["Meta", "LinkedIn", "Google"]
