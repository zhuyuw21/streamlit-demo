"""
Module 2 — 周对比分析 & 明细下钻
Embedded via render() and render_drilldown() in app.py
"""

import datetime as dt
import hashlib
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

# ── Constants ──────────────────────────────────────────────────────────────────
SEGMENTS = ["整体", "唯一入口"]

ENTERPRISES = [
    ("FUZOZO上海", "10057", "10057_芙崽"),
    ("文曲星", "10045", "10045_文曲星-Joy"),
    ("卢卡(杭州)科技", "10463", "10463_卢卡hero"),
    ("杭州千亿灵机", "10151", "10151_汤姆猫"),
    ("汕头市欣鸿科技", "10493", "10493_机器狗-小酷"),
    ("京东京造产品", "10461", "10461_小狗【JZ-01】"),
    ("北京学而思", "10141", "10141_学而思摩比"),
    ("卢卡(杭州)科技", "10460", "10460_卢卡"),
    ("京东京造产品", "10372", "10372_云朵兔【J】"),
    ("汕头市集思", "10779", "10779_星云宝贝"),
    ("商汤科技", "10000", "10000_元萝卜五合一下棋机"),
    ("深圳市优必选", "10288", "10288_悟空机器人"),
    ("科大讯飞", "10333", "10333_阿尔法蛋"),
    ("小米生态链", "10412", "10412_米兔故事机"),
    ("好未来", "10199", "10199_小思AI"),
]

JINGZAO_APPS = [e for e in ENTERPRISES if e[0] == "京东京造产品"]

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


@st.cache_data
def gen_app_detail(the_dt: dt.date) -> pd.DataFrame:
    rows = []
    for name, app_id, app_name in ENTERPRISES:
        k = (the_dt.isoformat(), app_id)
        cum_reg = _stable_int(k, "creg", lo=7000, hi=210000)
        new_reg_y = _stable_int(k, "nregy", lo=1, hi=1500)
        new_reg_7 = _stable_int(k, "nreg7", lo=new_reg_y, hi=new_reg_y * 9 + 10)
        act_y = _stable_int(k, "act_y", lo=1100, hi=13000)
        act_7 = _stable_int(k, "act7", lo=int(act_y * 0.5), hi=act_y)
        cum_act = _stable_int(k, "cact", lo=2900, hi=68000)
        new_act_y = int(new_reg_y * (_stable_int(k, "ar", lo=550, hi=720) / 1000))
        new_act_7 = int(new_reg_7 * (_stable_int(k, "ar7", lo=550, hi=720) / 1000))
        rows.append({
            "企业名称": name,
            "应用ID": app_id,
            "应用名称": app_name,
            "昨日新增注册设备量": new_reg_y,
            "累计注册设备量": cum_reg,
            "近7天新增注册设备量": new_reg_7,
            "昨日活跃设备量": act_y,
            "近7天活跃设备量": act_7,
            "昨日新增激活设备量": new_act_y,
            "累计激活设备量": cum_act,
            "近7天新增激活设备量": new_act_7,
        })
    return pd.DataFrame(rows).sort_values("近7天活跃设备量", ascending=False).reset_index(drop=True)


@st.cache_data
def gen_bot_detail(the_dt: dt.date, app_label: str) -> pd.DataFrame:
    name, app_id, app_name = next(
        (e for e in ENTERPRISES if f"{e[1]}_{e[2].split('_',1)[-1]}" == app_label or e[2] == app_label),
        ("商汤科技", "10000", "10000_元萝卜五合一下棋机"),
    )
    n = 200
    rows = []
    for i in range(n):
        k = (the_dt.isoformat(), app_id, i)
        rounds = _stable_int(k, "r", lo=1, hi=420)
        dev_hash = hashlib.md5("_".join(map(str, (app_id, i, the_dt))).encode()).hexdigest()[:28]
        rows.append({
            "日期": the_dt.strftime("%Y-%m-%d"),
            "企业名称": name,
            "应用ID": app_id,
            "应用名称": app_name,
            "设备ID": dev_hash,
            "是否活跃": 1 if rounds > 0 else 0,
            "对话轮次": float(rounds),
        })
    return pd.DataFrame(rows).sort_values("对话轮次", ascending=False).reset_index(drop=True)


@st.cache_data
def gen_jingzao_sales(start: dt.date, end: dt.date) -> pd.DataFrame:
    rows = []
    current = start
    while current <= end:
        for name, app_id, app_name in JINGZAO_APPS:
            k = (current.isoformat(), app_id)
            daily_sales = _stable_int(k, "jz_sales", lo=80, hi=950)
            rows.append({
                "日期": current.strftime("%Y-%m-%d"),
                "企业名称": name,
                "应用ID": app_id,
                "应用名称": app_name,
                "日销量": daily_sales,
            })
        current += dt.timedelta(days=1)
    df = pd.DataFrame(rows)
    df["_ts"] = pd.to_datetime(df["日期"])
    return df


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
    c1, _ = st.columns([2, 6])
    with c1:
        sel_dt = st.date_input(
            "选择日期 (dt)",
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


# ── Drill-down detail (rendered in the 多维下钻 tab) ──────────────────────────
def render_drilldown():
    tab_app, tab_bot, tab_jz = st.tabs(["app维度明细", "Bot单日明细", "京造产品销量"])

    with tab_app:
        ca1, _ = st.columns([2, 6])
        with ca1:
            app_dt = st.date_input("选择日期 (dt)", value=dt.date(2026, 6, 2), key="app_dt")

        app_df = gen_app_detail(app_dt)
        col_order = [
            "企业名称", "应用ID", "应用名称",
            "昨日新增注册设备量", "累计注册设备量", "近7天新增注册设备量",
            "昨日新增激活设备量", "累计激活设备量", "近7天新增激活设备量",
            "昨日活跃设备量", "近7天活跃设备量",
        ]
        app_df = app_df[col_order]

        st.caption(f"共 {len(app_df)} 条")
        st.dataframe(
            app_df,
            use_container_width=True,
            hide_index=True,
            height=430,
            column_config={
                "应用ID": st.column_config.TextColumn("应用ID"),
                "昨日新增注册设备量": st.column_config.NumberColumn(format="%d"),
                "累计注册设备量": st.column_config.NumberColumn(format="%d"),
                "近7天新增注册设备量": st.column_config.NumberColumn(format="%d"),
                "昨日新增激活设备量": st.column_config.NumberColumn(format="%d"),
                "累计激活设备量": st.column_config.NumberColumn(format="%d"),
                "近7天新增激活设备量": st.column_config.NumberColumn(format="%d"),
                "昨日活跃设备量": st.column_config.NumberColumn(format="%d"),
                "近7天活跃设备量": st.column_config.NumberColumn(format="%d"),
            },
        )
        st.download_button(
            "⬇ 导出 app明细 CSV",
            data=app_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"module_2_app_detail_{app_dt}.csv",
            mime="text/csv",
            key="dl_app",
        )

    with tab_bot:
        cb1, cb2, _ = st.columns([2, 3, 3])
        with cb1:
            bot_dt = st.date_input("选择日期 (dt)", value=dt.date(2026, 6, 2), key="bot_dt")
        with cb2:
            app_options = [e[2] for e in ENTERPRISES]
            sel_app = st.selectbox(
                "选择应用",
                options=app_options,
                index=app_options.index("10000_元萝卜五合一下棋机"),
            )

        bot_df = gen_bot_detail(bot_dt, sel_app)

        st.caption(f"共 {len(bot_df):,} 条")
        st.dataframe(
            bot_df,
            use_container_width=True,
            hide_index=True,
            height=430,
            column_config={
                "应用ID": st.column_config.TextColumn("应用ID"),
                "是否活跃": st.column_config.NumberColumn(format="%d"),
                "对话轮次": st.column_config.NumberColumn(format="%.2f"),
            },
        )
        st.download_button(
            "⬇ 导出 Bot单日明细 CSV",
            data=bot_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"module_2_bot_detail_{bot_dt}_{sel_app}.csv",
            mime="text/csv",
            key="dl_bot",
        )

    with tab_jz:
        jz_c1, jz_c2, _ = st.columns([2, 3, 3])
        with jz_c1:
            jz_range = st.date_input(
                "时间范围",
                value=(dt.date(2026, 5, 20), dt.date(2026, 6, 2)),
                key="jz_range",
            )
        with jz_c2:
            jz_app_options = ["全部"] + [e[2] for e in JINGZAO_APPS]
            jz_sel_app = st.selectbox("选择应用", options=jz_app_options, key="jz_app")

        if isinstance(jz_range, (list, tuple)) and len(jz_range) == 2:
            jz_start, jz_end = jz_range
        else:
            jz_start = jz_end = dt.date(2026, 6, 2)

        jz_df = gen_jingzao_sales(jz_start, jz_end)
        if jz_sel_app != "全部":
            jz_df = jz_df[jz_df["应用名称"] == jz_sel_app].reset_index(drop=True)

        # ── Summary metrics ───────────────────────────────────────────────────
        summary = jz_df.groupby("应用名称", sort=False)["日销量"].sum().reset_index()
        summary.columns = ["应用名称", "区间总销量"]
        metric_cols = st.columns(max(len(summary), 1))
        for i, row in summary.iterrows():
            with metric_cols[i]:
                with st.container(border=True):
                    st.markdown(f'<div class="metric-label">{row["应用名称"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-big">{fmt_int(row["区间总销量"])}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-sub">区间总销量</div>', unsafe_allow_html=True)

        # ── Trend chart ───────────────────────────────────────────────────────
        trend_chart = (
            alt.Chart(jz_df)
            .mark_line(point=alt.OverlayMarkDef(size=40))
            .encode(
                x=alt.X("_ts:T", title=None,
                        axis=alt.Axis(format="%m-%d", labelColor="#9ca3af")),
                y=alt.Y("日销量:Q", title="日销量",
                        axis=alt.Axis(labelColor="#9ca3af", titleColor="#9ca3af")),
                color=alt.Color("应用名称:N",
                                legend=alt.Legend(title=None, orient="top")),
                tooltip=[
                    alt.Tooltip("_ts:T", title="日期", format="%Y-%m-%d"),
                    alt.Tooltip("应用名称:N", title="应用"),
                    alt.Tooltip("日销量:Q", title="日销量", format=","),
                ],
            )
            .properties(height=260)
            .configure_view(strokeWidth=0)
        )
        st.altair_chart(trend_chart, use_container_width=True)

        # ── Detail table ──────────────────────────────────────────────────────
        display_df = jz_df.drop(columns=["_ts"])
        st.caption(f"共 {len(display_df)} 条")
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=360,
            column_config={
                "应用ID": st.column_config.TextColumn("应用ID"),
                "日销量": st.column_config.NumberColumn(format="%d"),
            },
        )
        st.download_button(
            "⬇ 导出京造销量 CSV",
            data=display_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"module_2_jingzao_sales_{jz_start}_{jz_end}.csv",
            mime="text/csv",
            key="dl_jz",
        )
