"""
Main dashboard entry point.
Run with:  streamlit run app.py
"""

import streamlit as st
import Module1
import Module2
import Module4

st.set_page_config(page_title="数据看板", layout="wide", page_icon="📊")

st.markdown(
    """
    <style>
        /* ── Theme tokens ──────────────────────────────────────── */
        :root {
            --bg: #0a0e14;
            --panel: #121821;
            --panel-border: #1f2733;
            --accent: #5eead4;
            --accent-soft: #2dd4bf;
            --text: #e6edf3;
            --text-dim: #8b95a5;
        }

        /* ── Base ──────────────────────────────────────────────── */
        .stApp { background-color: var(--bg); color: var(--text); }
        .block-container { padding-top: 3.5rem; padding-bottom: 3rem; }
        [data-testid="stHeader"] { background: transparent; }

        /* ── Bordered card containers ───────────────────────────── */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--panel);
            border: 1px solid var(--panel-border) !important;
            border-radius: 10px;
        }

        /* ── Equal-height card rows ─────────────────────────────── */
        div[data-testid="stHorizontalBlock"] { align-items: stretch; }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            display: flex; flex-direction: column;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stVerticalBlock"] {
            flex: 1; display: flex; flex-direction: column;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
            flex: 1;
        }

        /* ── Tab bar ────────────────────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {
            background: transparent;
            border-bottom: 1px solid var(--panel-border);
            gap: 0;
            padding: 0 2px;
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: 0;
            color: var(--text-dim);
            font-size: 14px;
            font-weight: 500;
            padding: 12px 22px;
            border-bottom: 2px solid transparent;
            margin-bottom: -1px;
        }
        .stTabs [aria-selected="true"] {
            color: var(--text);
            border-bottom: 2px solid var(--accent);
            font-weight: 600;
        }

        /* ── Metric card content ────────────────────────────────── */
        .metric-big { font-size: 36px; font-weight: 700; color: var(--text); line-height: 1.15; }
        .metric-label {
            font-size: 13px; color: var(--text-dim); font-weight: 500;
            text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px;
        }
        .metric-sub { font-size: 13px; color: var(--text-dim); }
        .delta-up { color: #f87171; font-size: 13px; font-weight: 500; }
        .delta-down { color: var(--accent); font-size: 13px; font-weight: 500; }
        .rate-line { font-size: 14px; }

        /* ── Section headings ───────────────────────────────────── */
        .section-title {
            font-size: 14px; font-weight: 600; color: var(--text);
            margin: 1.4rem 0 0.7rem;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--panel-border);
            letter-spacing: 0.02em;
        }
        .section-title::before {
            content: ""; display: inline-block;
            width: 3px; height: 13px; margin-right: 8px;
            background: var(--accent); border-radius: 2px;
            vertical-align: -1px;
        }
        .sub-title {
            font-size: 13px; font-weight: 600; color: var(--text-dim);
            margin: 1rem 0 0.4rem;
        }

        /* ── Weekly comparison table ────────────────────────────── */
        .wk-table { border-collapse: collapse; width: 100%; font-size: 13px; color: var(--text); }
        .wk-table th, .wk-table td {
            padding: 10px 14px;
            text-align: right;
            border-bottom: 1px solid var(--panel-border);
        }
        .wk-table thead th {
            background: #14261b; color: var(--accent);
            font-weight: 600; text-align: right;
            border-bottom: none; white-space: nowrap;
        }
        .wk-table thead th.left { text-align: left; }
        .wk-table td.group {
            text-align: left; font-weight: 600; color: var(--text);
            vertical-align: top; background: var(--panel);
        }
        .wk-table td.metric { text-align: left; color: var(--text-dim); }
        .up { color: var(--accent); }
        .down { color: #f87171; }
        .grp-sep td { border-top: 2px solid var(--panel-border); }

        /* ── Layout ─────────────────────────────────────────────── */
        div[data-testid="stHorizontalBlock"] { gap: 1rem; }

        /* ── Inputs ─────────────────────────────────────────────── */
        div[data-baseweb="input"] input,
        div[data-baseweb="select"] > div {
            background: var(--panel) !important;
            border-color: var(--panel-border) !important;
            color: var(--text) !important;
        }
        .stDateInput label, .stRadio label, .stSelectbox label { color: var(--text-dim) !important; }

        /* ── Primary button (查询等) ─────────────────────────────── */
        .stButton > button {
            background: var(--accent) !important;
            border: 1px solid var(--accent) !important;
            color: #06110a !important;
            font-weight: 600 !important;
        }
        .stButton > button:hover {
            background: var(--accent-soft) !important;
            border-color: var(--accent-soft) !important;
        }

        /* ── Dataframe ──────────────────────────────────────────── */
        [data-testid="stDataFrame"] {
            background: var(--panel);
            border: 1px solid var(--panel-border);
            border-radius: 8px;
        }

        /* ── Download button ────────────────────────────────────── */
        .stDownloadButton > button {
            background: transparent !important;
            border: 1px solid var(--panel-border) !important;
            color: var(--text-dim) !important;
            font-size: 12px !important;
            padding: 5px 14px !important;
            border-radius: 6px !important;
            font-weight: 500 !important;
        }
        .stDownloadButton > button:hover {
            border-color: var(--accent) !important;
            color: var(--accent) !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div style="font-size:22px;font-weight:700;color:#e6edf3;margin-bottom:1.4rem;letter-spacing:-0.02em;">数据看板</div>',
    unsafe_allow_html=True,
)

tabs = st.tabs(["业务总览"])

with tabs[0]:
    Module1.render()
    Module2.render()
    Module4.render()
