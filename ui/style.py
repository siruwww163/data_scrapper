"""Minimal academic presentation styling."""
import streamlit as st


def configure_page(title: str) -> None:
    st.set_page_config(page_title=title, page_icon="◫", layout="wide")
    st.markdown("""
    <style>
      .block-container {max-width: 1180px; padding-top: 2.2rem; padding-bottom: 4rem;}
      h1, h2, h3 {letter-spacing: -0.02em;}
      h1 {font-size: 2.25rem !important;}
      [data-testid="stMetric"] {border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px;}
      .platform-card {border:1px solid #e5e7eb; border-top:3px solid #385170; border-radius:8px;
        padding:18px; min-height:220px; background:#fff;}
      .eyebrow {color:#496078; font-weight:700; font-size:.78rem; text-transform:uppercase; letter-spacing:.08em;}
      .sample-note {border-left:4px solid #b7791f; background:#fffbeb; padding:12px 16px; margin:12px 0;}
      .pipeline {border:1px solid #dce2e8; background:#f8fafc; border-radius:8px; padding:18px;
        text-align:center; font-weight:600; line-height:2.2;}
      footer {visibility:hidden;}
    </style>
    """, unsafe_allow_html=True)


def sample_notice() -> None:
    st.markdown(
        '<div class="sample-note"><strong>Sample dataset.</strong> These fictional records are pre-generated '
        "for interface and schema demonstration. They are not live API responses and contain no real user data.</div>",
        unsafe_allow_html=True,
    )

