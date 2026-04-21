"""Data loading utilities for Google Sheets."""

from __future__ import annotations

import json
import os
import re
from difflib import get_close_matches
from typing import Any
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import streamlit as st

from utils import config


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names for robust downstream usage."""

    normalized = []
    for col in df.columns:
        clean = re.sub(r"[^a-zA-Z0-9]+", "_", str(col).strip().lower())
        clean = re.sub(r"_+", "_", clean).strip("_")
        normalized.append(clean)
    df = df.copy()
    df.columns = normalized
    return df


def parse_date_columns(df, date_cols):
    for col in date_cols:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed")
            except TypeError:
                df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _normalize_tab_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _resolve_tab_names(available_tabs: list[str], required_tabs: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    avail_normalized = {_normalize_tab_name(tab): tab for tab in available_tabs}

    for required in required_tabs:
        required_norm = _normalize_tab_name(required)
        if required_norm in avail_normalized:
            mapping[required] = avail_normalized[required_norm]
            continue

        candidates = get_close_matches(required_norm, list(avail_normalized.keys()), n=1, cutoff=0.7)
        if candidates:
            mapping[required] = avail_normalized[candidates[0]]
            st.warning(
                f"Using close tab match for '{required}': found '{avail_normalized[candidates[0]]}'."
            )
        else:
            raise ValueError(
                f"Required tab '{required}' was not found. Available tabs: {', '.join(available_tabs)}"
            )

    return mapping


def _get_google_credentials() -> dict[str, Any]:
    if "gcp_service_account" in st.secrets:
        return dict(st.secrets["gcp_service_account"])

    env_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if env_json:
        return json.loads(env_json)

    raise ValueError(
        "Google credentials not found. Set st.secrets['gcp_service_account'] or GOOGLE_SERVICE_ACCOUNT_JSON."
    )


def _extract_spreadsheet_id(sheet_url_or_id: str) -> str:
    if "/spreadsheets/d/" not in sheet_url_or_id:
        return sheet_url_or_id

    parsed = urlparse(sheet_url_or_id)
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", parsed.path)
    if not match:
        raise ValueError(f"Could not parse spreadsheet ID from URL: {sheet_url_or_id}")
    return match.group(1)


@st.cache_data(show_spinner=False, ttl=1800)
def load_from_google_sheets(sheet_url: str) -> dict[str, pd.DataFrame]:
    """Load required tabs from Google Sheets with service-account authentication."""

    import gspread
    from google.oauth2.service_account import Credentials

    credentials_info = _get_google_credentials()
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    creds = Credentials.from_service_account_info(credentials_info, scopes=scopes)
    client = gspread.authorize(creds)

    spreadsheet_id = _extract_spreadsheet_id(sheet_url)
    workbook = client.open_by_key(spreadsheet_id)

    worksheets = workbook.worksheets()
    available_tabs = [ws.title for ws in worksheets]
    tab_map = _resolve_tab_names(available_tabs, config.REQUIRED_TABS)

    out: dict[str, pd.DataFrame] = {}
    for required_tab, actual_tab in tab_map.items():
        worksheet = workbook.worksheet(actual_tab)
        rows = worksheet.get_all_values()
        if not rows:
            out[required_tab] = pd.DataFrame()
            continue

        header = [str(c).strip() for c in rows[0]]
        values = rows[1:]
        df = pd.DataFrame(values, columns=header)
        df = df.replace(r"^\s*$", np.nan, regex=True).dropna(how="all")
        out[required_tab] = _postprocess_dataframe(df)

    return out


def _postprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    processed = standardize_columns(df)
    processed = parse_date_columns(processed, config.KNOWN_DATE_COLUMNS)

    for col in processed.columns:
        if col not in config.KNOWN_DATE_COLUMNS and processed[col].dtype == object:
            stripped = (
                processed[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.strip()
            )
            numeric = pd.to_numeric(stripped, errors="coerce")
            non_null_ratio = numeric.notna().mean() if len(numeric) else 0
            if non_null_ratio > 0.7:
                processed[col] = numeric

    if "date" in processed.columns:
        processed["month"] = processed.get("month", processed["date"].dt.month_name().str[:3])
        processed["year"] = processed.get("year", processed["date"].dt.year)
    if "week_start" in processed.columns and "month" not in processed.columns:
        processed["month"] = processed["week_start"].dt.month_name().str[:3]
        processed["year"] = processed["week_start"].dt.year

    return processed


def load_data(sheet_url: str) -> tuple[dict[str, pd.DataFrame], str]:
    """Primary entrypoint for production Google Sheets loading."""

    return load_from_google_sheets(sheet_url), "google_sheets"
