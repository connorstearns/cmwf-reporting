"""Configuration constants and editable classification rules."""

from __future__ import annotations

GOOGLE_SHEET_URL_DEFAULT = (
    "https://docs.google.com/spreadsheets/d/11-pQ2uFJkz5UgY5Tf2sPdc_K12-o0VGbb-whWGtxUpw/edit?gid=924758410#gid=924758410"
)

REQUIRED_TABS = [
    "Campaign Master Feed",
    "GA4 Master Feed",
    "LP Master Feed (Weekly)",
]

KNOWN_DATE_COLUMNS = ["date", "week_start"]

EXPECTED_COLUMNS = {
    "Campaign Master Feed": [
        "date",
        "platform",
        "campaign_name",
        "ad_creative_id",
        "asset_group",
        "cost",
        "impressions",
        "clicks",
        "leads_newsletter",
        "shares",
        "follows_page_likes",
        "month",
        "year",
    ],
    "GA4 Master Feed": [
        "date",
        "paid_traffic",
        "direct_referral_traffic",
        "organic_traffic",
        "scrolls",
        "shares",
        "newsletter_signups",
        "file_downloads",
        "month",
        "year",
    ],
    "LP Master Feed (Weekly)": [
        "week_start",
        "month",
        "year",
        "source",
        "medium",
        "campaign",
        "content",
        "term",
        "sessions",
        "active_users",
        "engaged_sessions",
        "views",
    ],
}

NUMERIC_COLUMNS = {
    "Campaign Master Feed": ["cost", "impressions", "clicks", "leads_newsletter", "shares", "follows_page_likes"],
    "GA4 Master Feed": [
        "paid_traffic",
        "direct_referral_traffic",
        "organic_traffic",
        "scrolls",
        "shares",
        "newsletter_signups",
        "file_downloads",
    ],
    "LP Master Feed (Weekly)": ["sessions", "active_users", "engaged_sessions", "views"],
}

PLATFORM_ALIASES = {
    "Meta": ["meta", "facebook", "fb", "instagram"],
    "LinkedIn": ["linkedin", "linked in"],
    "Google": ["google", "google ads", "adwords", "pmax", "performance max"],
}

LP_CLASSIFICATION_RULES = {
    "Meta": {
        "source_any": ["facebook", "fb", "instagram", "meta"],
        "medium_any": ["paid", "paidsocial", "social", "cpc"],
        "exclude_any": ["organic", "referral"],
    },
    "LinkedIn": {
        "source_any": ["linkedin", "linked in"],
        "medium_any": ["paid", "social", "cpc"],
        "exclude_any": ["organic", "referral"],
    },
    "Google": {
        "source_any": ["google", "googleads", "adwords"],
        "medium_any": ["cpc", "ppc", "paidsearch", "search", "pmax", "performance max"],
        "exclude_any": ["organic"],
    },
}

COMPARISON_MODES = ["Previous Month", "Trailing 3-Month Average"]

LOWER_IS_BETTER = {"cpl", "cpc", "cpv", "cp_visit", "cpm", "cost_per_page_like", "cost_per_follower"}
HIGHER_IS_BETTER = {
    "leads",
    "clicks",
    "traffic",
    "impressions",
    "followers",
    "likes",
    "ctr",
    "lead_conversion_rate",
    "engagement_rate",
}

TOPIC_BUCKET_RULES = {
    "brand": ["brand", "commonwealth", "cmwf"],
    "performance max / always-on": ["pmax", "performance max", "always on", "always-on"],
    "house / rhythm / internal": ["house", "rhythm", "internal"],
}
