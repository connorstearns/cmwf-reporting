"""Normalization and platform/topic classification helpers."""

from __future__ import annotations

import re

import pandas as pd

from utils import config


def normalize_text(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = text.strip().lower()
    text = re.sub(r"[\W_]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_platform_name(value: object) -> str:
    text = normalize_text(value)
    for platform, aliases in config.PLATFORM_ALIASES.items():
        if any(alias in text for alias in aliases):
            return platform
    return "Unclassified"


def normalize_campaign_key(value: object) -> str:
    """Normalize campaign identifiers for cross-feed matching."""
    return normalize_text(value)


def classify_campaign_objective(platform: object, campaign_name: object) -> str:
    """Classify campaign objective based on platform + campaign naming conventions."""
    p = normalize_platform_name(platform)
    c = normalize_text(campaign_name)
    c_pad = f" {c} "

    if p == "Google":
        return "Traffic"

    if p == "Meta":
        lead_signals = ["leadgen", "lead gen", "newsletter leads", "mirror mirror leads", " leads "]
        follow_signals = ["follower", "page growth", "profile visits", "audience growth"]
        if any(sig in c_pad for sig in lead_signals):
            return "Leads"
        if any(sig in c for sig in follow_signals):
            return "Follows"
        return "Traffic"

    if p == "LinkedIn":
        article_signals = ["article boost", "engagement website", "pageengager"]
        lead_signals = ["leadgen", "lead gen", "mirror mirror leads", " leads "]
        follow_signals = ["follower ads", "follower"]
        if any(sig in c for sig in article_signals):
            return "Article"
        if any(sig in c_pad for sig in lead_signals):
            return "Leads"
        if any(sig in c for sig in follow_signals):
            return "Follows"
        return "Traffic"

    return "Unclassified"


def classify_lp_row(row: pd.Series) -> str:
    src = normalize_text(row.get("source"))
    med = normalize_text(row.get("medium"))
    camp = normalize_text(row.get("campaign"))
    content = normalize_text(row.get("content"))
    joined = " ".join([src, med, camp, content])

    for platform, rules in config.LP_CLASSIFICATION_RULES.items():
        if any(x in joined for x in rules["exclude_any"]):
            continue
        source_hit = any(x in src for x in rules["source_any"])
        medium_hit = any(x in med for x in rules["medium_any"])
        campaign_hint = any(x in joined for x in rules["source_any"])
        if source_hit and (medium_hit or campaign_hint):
            return platform
    return "Unclassified"


def add_classifications(campaign_df: pd.DataFrame, lp_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    campaign = campaign_df.copy()
    lp = lp_df.copy()
    if "platform" in campaign.columns:
        campaign["platform_norm"] = campaign["platform"].apply(normalize_platform_name)
    else:
        campaign["platform_norm"] = "Unclassified"
    if "campaign_name" in campaign.columns:
        campaign["campaign_key"] = campaign["campaign_name"].apply(normalize_campaign_key)
    else:
        campaign["campaign_key"] = ""
    campaign["objective"] = campaign.apply(
        lambda row: classify_campaign_objective(row.get("platform_norm", row.get("platform")), row.get("campaign_name")),
        axis=1,
    )

    lp["platform_norm"] = lp.apply(classify_lp_row, axis=1)
    if "campaign" in lp.columns:
        lp["campaign_key"] = lp["campaign"].apply(normalize_campaign_key)
    else:
        lp["campaign_key"] = ""
    return campaign, lp


def classify_google_topic(campaign_name: object) -> str:
    text = normalize_text(campaign_name)
    for bucket, terms in config.TOPIC_BUCKET_RULES.items():
        if any(term in text for term in terms):
            return bucket
    return "other"
