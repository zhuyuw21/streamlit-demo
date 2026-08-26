"""
Module 2 — 周对比分析
Embedded via render() in app.py
"""

import datetime as dt
import hashlib
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

# ── Constants ──────────────────────────────────────────────────────────────────
SEGMENTS = ["整体", "唯一入口"]

# ── Mock data helpers ──────────────────────────────────────────────────────────
def _stable_int(*parts, lo, hi):
    """Deterministic pseudo-random int from string parts, for reproducible mock data."""
    h = hashlib.md5("_".join(str(p) for p in parts).encode()).hexdigest()
    return lo + int(h[:8], 16) % (hi - lo + 1)


@st.cache_data
def gen_weekly(segment: str, week_start: dt.date) -> dict:
    key = (segment, week_start.isoformat())
    scale = 1.0 if segment == "整体" else 0.33
    dau = int(_stable_int(key, "dau", lo=24000, hi=36000) * scale)
    new_reg = int(_stable_int(key, "nreg", lo=12000, hi=27000) * scale)
    act_rate = _stable_int(key, "ar", lo=620, hi=695) / 1000
    new_act = int(new_reg * act_rate)
    rounds = _stable_int(key, "rnd", lo=33, hi=60)
    dur = _stable_int(key, "dur", lo=110, hi=200) / 10
    cum_reg = _stable_int(key, "creg", lo=1_000_000, hi=1_070_000)
    if segment == "唯一入口":
        cum_reg = int(cum_reg * 0.38)
    return {
        "DAU (周日平均)": dau,
        "周新增注册": new_reg,
        "周新增激活": new_act,
        "激活率": act_rate,
        "日均设备对话轮次": rounds,
        "设备日均使用时长(分)": dur,
        "累计注册设备": cum_reg,
    }


# ── Formatting helpers ─────────────────────────────────────────────────────────
def fmt_int(x):
    return f"{int(round(x)):,}"


def fmt_value(metric, v):
    if metric == "激活率":
        return f"{v*100:.1f}%"
    if metric == "设备日均使用时长(分)":
        return f"{v:.1f}"
    return fmt_int(v)


def pct_change(cur, prev):
    if prev == 0:
        return "—", ""
    diff = (cur - prev) / prev * 100
    cls = "up" if diff >= 0 else "down"
    sign = "+" if diff >= 0 else ""
    return f"{sign}{diff:.1f}%", cls


def pt_change(cur, prev):
    diff = (cur - prev) * 100
    cls = "up" if diff >= 0 else "down"
    sign = "+" if diff >= 0 else ""
    return f"{sign}{diff:.1f}pt", cls


METRIC_ORDER = [
    "DAU (周日平均)",
    "周新增注册",
    "周新增激活",
    "激活率",
    "日均设备对话轮次",
    "设备日均使用时长(分)",
    "累计注册设备",
]


# ── Weekly comparison table ────────────────────────────────────────────────────
def render():
    st.markdown('<div class="section-title">核心指标周对比</div>', unsafe_allow_html=True)

    c1, _ = st.columns([2, 6])
    with c1:
        sel_dt = st.date_input(
            "本周结束日",
            value=dt.date(2026, 6, 2),
            help="表格以该日所在周为最新周，依次向前推 3 个 7 天周期作对比",
        )

    windows = []
    for i in range(3):
        end = sel_dt - dt.timedelta(days=7 * i)
        start = end - dt.timedelta(days=6)
        windows.append((start, end))

    def range_label(start, end):
        return f"{start.strftime('%m/%d')} ~ {end.strftime('%m/%d')}"

    w1, w2, w3 = windows
    hdr_w1 = range_label(*w1)
    hdr_w2 = range_label(*w2)
    hdr_w3 = range_label(*w3)

    def seg_week_data(segment, window):
        return gen_weekly(segment, window[0])

    html = ['<table class="wk-table">']
    html.append(
        f"<thead><tr>"
        f"<th class='left'>人群</th>"
        f"<th class='left'>指标</th>"
        f"<th>{hdr_w1}</th><th>{hdr_w2}</th><th>{hdr_w3}</th>"
        f"<th>环比 {hdr_w2}</th><th>对比 {hdr_w3}</th>"
        f"</tr></thead><tbody>"
    )

    for si, seg in enumerate(SEGMENTS):
        d1 = seg_week_data(seg, w1)
        d2 = seg_week_data(seg, w2)
        d3 = seg_week_data(seg, w3)
        sep_cls = " grp-sep" if si > 0 else ""
        for mi, metric in enumerate(METRIC_ORDER):
            v1, v2, v3 = d1[metric], d2[metric], d3[metric]
            if metric == "激活率":
                mom_txt, mom_cls = pt_change(v1, v2)
                yoy_txt, yoy_cls = pt_change(v1, v3)
            else:
                mom_txt, mom_cls = pct_change(v1, v2)
                yoy_txt, yoy_cls = pct_change(v1, v3)

            row_sep = sep_cls if mi == 0 else ""
            group_cell = (
                f"<td class='group' rowspan='{len(METRIC_ORDER)}'>{seg}</td>"
                if mi == 0 else ""
            )
            html.append(
                f"<tr class='{row_sep.strip()}'>"
                f"{group_cell}"
                f"<td class='metric'>{metric}</td>"
                f"<td>{fmt_value(metric, v1)}</td>"
                f"<td>{fmt_value(metric, v2)}</td>"
                f"<td>{fmt_value(metric, v3)}</td>"
                f"<td class='{mom_cls}'>{mom_txt}</td>"
                f"<td class='{yoy_cls}'>{yoy_txt}</td>"
                f"</tr>"
            )

    html.append("</tbody></table>")
    st.markdown("".join(html), unsafe_allow_html=True)

    wk_rows = []
    for seg in SEGMENTS:
        d1 = seg_week_data(seg, w1)
        d2 = seg_week_data(seg, w2)
        d3 = seg_week_data(seg, w3)
        for metric in METRIC_ORDER:
            wk_rows.append({
                "人群": seg, "指标": metric,
                hdr_w1: fmt_value(metric, d1[metric]),
                hdr_w2: fmt_value(metric, d2[metric]),
                hdr_w3: fmt_value(metric, d3[metric]),
            })
    wk_export = pd.DataFrame(wk_rows)
    st.download_button(
        "⬇ 导出周对比表 CSV",
        data=wk_export.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"module_2_weekly_{sel_dt}.csv",
        mime="text/csv",
    )