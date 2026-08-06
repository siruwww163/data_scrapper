"""Pipeline, reproducibility, and documentation page."""
import pandas as pd
import streamlit as st

from ui.style import configure_page

configure_page("Data Pipeline and Documentation")
st.title("Data Pipeline and Documentation")
st.caption("A reproducible boundary between official API collection and offline presentation.")
st.markdown('<div class="pipeline">API Authentication → API Request → Pagination → Raw JSON Storage → '
            'Schema Extraction → Data Cleaning → Validation → Processed CSV / SQLite → Streamlit Presentation → '
            'Research-ready dataset for EDA</div>', unsafe_allow_html=True)

st.header("Implementation controls")
controls = [
    ("Credential management", "Secrets are read from environment variables; tokens are never logged or committed."),
    ("Storage separation", "Immutable raw JSON and processed tables use separate directories."),
    ("Provenance", "Every record retains collected_at and source/API metadata."),
    ("Idempotency", "Unique IDs remove duplicates, enabling collection scripts to be rerun."),
    ("Time standard", "All parseable timestamps are normalized to UTC."),
    ("Unavailable content", "Deleted, removed, disabled, and unavailable content receives an explicit status."),
    ("Resilience", "429 and selected 5xx responses use bounded retries with exponential backoff."),
    ("Skipped objects", "Objects whose comments cannot be accessed are logged without stopping the full run."),
    ("Presentation boundary", "Streamlit reads pre-collected files and never calls an API during page rendering."),
]
st.dataframe(pd.DataFrame(controls, columns=["Control", "Implementation"]), hide_index=True, width="stretch")

st.header("Run sequence")
st.code("""# 1. Configure credentials only for collectors you intend to run
copy .env.example .env

# 2. Run a collector separately (example imports)
python -m collectors.youtube_collector

# 3. Transform raw data with the corresponding processor
python generate_sample_data.py

# 4. Present pre-collected local files
streamlit run app.py""", language="powershell")

st.header("Research readiness")
st.write(
    "The processed layer has stable field names, UTC timestamps, unique identifiers, explicit missing-content flags, "
    "and collection provenance. It is prepared for later cleaning and exploratory analysis, but this demo does not "
    "interpret platform content or make inferential claims."
)
