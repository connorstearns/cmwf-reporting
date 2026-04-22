"""Google Sheets-only data loader with normalization and parsing."""

from __future__ import annotations

import re
from difflib import get_close_matches

import gspread
import numpy as np
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

from utils import config


def standardize_text(value: str) -> str:
    value = str(value).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_")


def parse_date_columns(df, date_cols):
    for col in date_cols:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed")
            except TypeError:
                df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _normalize_tab(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _resolve_tabs(sheet_tabs: list[str], required_tabs: list[str]) -> dict[str, str]:
    norm_to_actual = {_normalize_tab(t): t for t in sheet_tabs}
    resolved: dict[str, str] = {}
    for req in required_tabs:
        req_norm = _normalize_tab(req)
        if req_norm in norm_to_actual:
            resolved[req] = norm_to_actual[req_norm]
            continue
        match = get_close_matches(req_norm, norm_to_actual.keys(), n=1, cutoff=0.7)
        if not match:
            raise ValueError(
                f"Required worksheet '{req}' not found. Available tabs: {', '.join(sheet_tabs)}"
            )
        resolved[req] = norm_to_actual[match[0]]
    return resolved


def _coerce_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col in out.columns:
            cleaned = (
                out[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.strip()
            )
            out[col] = pd.to_numeric(cleaned, errors="coerce")
    return out


def _clean_df(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    out = df.copy()
    out.columns = [standardize_text(c) for c in out.columns]
    out = out.replace(r"^\s*$", np.nan, regex=True).dropna(how="all")
    out = parse_date_columns(out, config.KNOWN_DATE_COLUMNS)
    out = _coerce_numeric(out, config.NUMERIC_COLUMNS.get(sheet_name, []))

    if "date" in out.columns:
        out["month"] = out.get("month", out["date"].dt.month)
        out["year"] = out.get("year", out["date"].dt.year)
    if "week_start" in out.columns:
        out["month"] = out.get("month", out["week_start"].dt.month)
        out["year"] = out.get("year", out["week_start"].dt.year)

    out["month"] = pd.to_numeric(out.get("month"), errors="coerce")
    out["year"] = pd.to_numeric(out.get("year"), errors="coerce")
    return out


def _month_key_from_parts(df: pd.DataFrame) -> pd.Series:
    if "date" in df.columns:
        return df["date"].dt.to_period("M").astype(str)
    if "week_start" in df.columns:
        return df["week_start"].dt.to_period("M").astype(str)
    return pd.to_datetime(
        dict(year=df["year"], month=df["month"], day=1), errors="coerce"
    ).dt.to_period("M").astype(str)


def _build_client() -> gspread.Client:
    if "gcp_service_account" not in st.secrets:
        raise ValueError("Missing st.secrets['gcp_service_account'] credentials.")
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ],
    )
    return gspread.authorize(creds)


@st.cache_data(ttl=1800, show_spinner=False)
def load_data(sheet_url: str) -> dict[str, pd.DataFrame]:
    client = _build_client()
    book = client.open_by_url(sheet_url)
    available_tabs = [w.title for w in book.worksheets()]
    tab_map = _resolve_tabs(available_tabs, config.REQUIRED_TABS)

    data: dict[str, pd.DataFrame] = {}
    for required, actual in tab_map.items():
        ws = book.worksheet(actual)
        records = ws.get_all_records(expected_headers=ws.row_values(1))
        raw = pd.DataFrame(records)
        data[required] = _clean_df(raw, required)
        data[required]["month_key"] = _month_key_from_parts(data[required])
    return data
