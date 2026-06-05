"""
Main dashboard entry point.
Run with:  streamlit run app.py
"""

import streamlit as st
import Module1
import Module2
import Module3

st.set_page_config(page_title="数据看板", layout="wide", page_icon="📊")

st.markdown(
    """
    <style>
        /* ── Base ──────────────────────────────────────────────── */
        .stApp { background-color: #f8fafc; }
        .block-container { padding-top: 3.5rem; padding-bottom: 3rem; }

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
            border-bottom: 1px solid #e2e8f0;
            gap: 0;
            padding: 0 2px;
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: 0;
            color: #94a3b8;
            font-size: 14px;
            font-weight: 500;
            padding: 12px 22px;
            border-bottom: 2px solid transparent;
            margin-bottom: -1px;
        }
        .stTabs [aria-selected="true"] {
            color: #0f172a;
            border-bottom: 2px solid #2563eb;
            font-weight: 600;
        }

        /* ── Metric card content ────────────────────────────────── */
        .metric-big { font-size: 36px; font-weight: 700; color: #0f172a; line-height: 1.15; }
        .metric-label {
            font-size: 13px; color: #94a3b8; font-weight: 500;
            text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px;
        }
        .metric-sub { font-size: 13px; color: #94a3b8; }
        .delta-up { color: #16a34a; font-size: 13px; font-weight: 500; }
        .delta-down { color: #dc2626; font-size: 13px; font-weight: 500; }
        .rate-line { font-size: 14px; }

        /* ── Section headings ───────────────────────────────────── */
        .section-title {
            font-size: 14px; font-weight: 600; color: #334155;
            margin: 1.4rem 0 0.7rem;
            padding-bottom: 8px;
            border-bottom: 1px solid #f1f5f9;
            letter-spacing: 0.02em;
        }
        .sub-title {
            font-size: 13px; font-weight: 600; color: #64748b;
            margin: 1rem 0 0.4rem;
        }

        /* ── Weekly comparison table ────────────────────────────── */
        .wk-table { border-collapse: collapse; width: 100%; font-size: 13px; }
        .wk-table th, .wk-table td {
            padding: 10px 14px;
            text-align: right;
            border-bottom: 1px solid #f1f5f9;
        }
        .wk-table thead th {
            background: #1e3a5f; color: #e2e8f0;
            font-weight: 600; text-align: right;
            border-bottom: none; white-space: nowrap;
        }
        .wk-table thead th.left { text-align: left; }
        .wk-table td.group {
            text-align: left; font-weight: 600; color: #1e293b;
            vertical-align: top; background: #f8fafc;
        }
        .wk-table td.metric { text-align: left; color: #475569; }
        .up { color: #16a34a; }
        .down { color: #dc2626; }
        .grp-sep td { border-top: 2px solid #e2e8f0; }

        /* ── Layout ─────────────────────────────────────────────── */
        div[data-testid="stHorizontalBlock"] { gap: 1rem; }

        /* ── Download button ────────────────────────────────────── */
        .stDownloadButton > button {
            background: transparent !important;
            border: 1px solid #e2e8f0 !important;
            color: #64748b !important;
            font-size: 12px !important;
            padding: 5px 14px !important;
            border-radius: 6px !important;
            font-weight: 500 !important;
        }
        .stDownloadButton > button:hover {
            border-color: #2563eb !important;
            color: #2563eb !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div style="font-size:22px;font-weight:700;color:#0f172a;margin-bottom:1.4rem;letter-spacing:-0.02em;">数据看板</div>',
    unsafe_allow_html=True,
)

tabs = st.tabs(["大盘概况", "产品分析", "业务下钻"])

with tabs[0]:
    Module1.render()
    Module2.render()

with tabs[1]:
    Module3.render()

with tabs[2]:
    Module2.render_drilldown()
