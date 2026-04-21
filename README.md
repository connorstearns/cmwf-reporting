# CMWF Monthly Paid Media Dashboard

A production-ready Streamlit app for automating the Commonwealth Fund monthly paid media report across four reporting sections:

1. Monthly executive summary
2. Meta campaign performance
3. LinkedIn campaign performance
4. Google campaign performance

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Google Sheets API setup

1. Create a Google Cloud project.
2. Enable Google Sheets API and Google Drive API.
3. Create a **Service Account** and generate a JSON key.
4. Share the target Google Sheet with the service account email (Editor or Viewer access is sufficient for reads).

## Credentials in Streamlit

You can provide credentials in either of two ways:

### Option A: Streamlit secrets (recommended)

Add this to `.streamlit/secrets.toml`:

```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

### Option B: Environment variable

Set `GOOGLE_SERVICE_ACCOUNT_JSON` as a JSON string containing the same service account fields.

## Data source

This app uses **Google Sheets as the sole production data source**.

- Default Google Sheet URL is configurable in `utils/config.py`.
- The sidebar allows overriding the sheet URL for testing.

Expected tabs:

- `Campaign Master Feed`
- `GA4 Master Feed`
- `LP Master Feed (Weekly)`

The loader includes defensive fuzzy tab-name matching with clear warnings.
