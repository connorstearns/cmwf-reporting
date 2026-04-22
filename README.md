# CMWF Monthly Paid Media Dashboard

## Local setup instructions
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run the dashboard:
   ```bash
   streamlit run app.py
   ```

## Streamlit secrets setup instructions
Create `.streamlit/secrets.toml` with:

```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."

google_sheet_url = "https://docs.google.com/spreadsheets/d/11-pQ2uFJkz5UgY5Tf2sPdc_K12-o0VGbb-whWGtxUpw/edit?gid=924758410#gid=924758410"
```

## Google Sheets sharing instructions
Share the source Google Sheet with the service account `client_email` in your secrets file. Viewer access is sufficient for this app.

## How the reporting month is determined
- The app computes available month keys from the Campaign Master Feed parsed dates.
- It defaults to the most recent **complete** month by choosing the latest month prior to the current calendar month.
- If no prior month exists, it falls back to the latest month in the data.

## Assumptions used for platform classification
- Campaign Master Feed platform mapping normalizes variants (`meta/facebook/fb/instagram`, `linkedin/linked in`, `google/google ads/adwords/pmax`).
- LP weekly traffic is classified with editable rules in `utils/config.py`, using `source`, `medium`, plus campaign/content context and exclusions for organic/referral signals.
- Any row not matching paid-platform criteria is assigned to `Unclassified` and surfaced in Data QA.

---

Production Streamlit dashboard for automating Commonwealth Fund monthly paid media reporting across:
1. Executive Summary
2. Meta Campaign Performance
3. LinkedIn Campaign Performance
4. Google Campaign Performance
5. Data QA

## Data source
Google Sheets only (no Excel fallback logic).

Target sheet:
`https://docs.google.com/spreadsheets/d/11-pQ2uFJkz5UgY5Tf2sPdc_K12-o0VGbb-whWGtxUpw/edit?gid=924758410#gid=924758410`

Required tabs:
- Campaign Master Feed
- GA4 Master Feed
- LP Master Feed (Weekly)

## Features
- Service-account authentication from Streamlit secrets.
- Defensive worksheet matching and clear failures when required tabs are missing.
- Column normalization, date parsing, numeric coercion, blank-row removal.
- Most-recent-complete-month default selection.
- Comparison mode: Previous Month or Trailing 3-Month Average.
- Executive KPI cards, platform KPI cards, trend and breakdown charts (Plotly).
- Rule-based insights and recommendations with slide-ready text download.
- Data QA panel for row counts, latest dates, parsing issues, missing columns, and unclassified traffic.
