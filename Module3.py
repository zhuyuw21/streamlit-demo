"""
Module 3 — 注册激活与留存
Embedded via render() in app.py
"""

import datetime as dt
import hashlib
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

# ── Shared mock universe ───────────────────────────────────────────────────────
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

ROUND_BUCKETS = ["10以下", "10_29", "30_49", "50_99", "100_149",
                 "150_199", "200_249", "250_500", "500以上"]


def _si(*parts, lo, hi):
    h = hashlib.md5("_".join(str(p) for p in parts).encode()).hexdigest()
    return lo + int(h[:8], 16) % (hi - lo + 1)


def _sf(*parts, lo, hi, nd=2):
    h = hashlib.md5("_".join(str(p) for p in parts).encode()).hexdigest()
    frac = int(h[8:16], 16) / 0xFFFFFFFF
    return round(lo + frac * (hi - lo), nd)


def range_label(start, end):
    return f"{start.strftime('%m月%d日')}~{end.strftime('%m月%d日')}"


def fmt_int(x):
    return f"{int(round(x)):,}"


# ── Data generators ────────────────────────────────────────────────────────────
@st.cache_data
def gen_weekly_top(the_dt: dt.date) -> pd.DataFrame:
    rows = []
    for name, app_id, app_name in ENTERPRISES:
        v_this = _si(the_dt, app_id, "wt", lo=200, hi=26000)
        v_prev = _si(the_dt, app_id, "wp", lo=200, hi=26000)
        v_pprev = _si(the_dt, app_id, "wpp", lo=200, hi=26000)
        delta = v_this - v_prev
        delta_pct = (delta / v_prev * 100) if v_prev else 0.0
        rows.append({
            "app_id": app_id,
            "app_name": app_name,
            "_this": v_this,
            "_prev": v_prev,
            "_pprev": v_pprev,
            "环比增量（绝对Δ）": delta,
            "环比增量%（百分比Δ）": round(delta_pct, 1),
        })
    return pd.DataFrame(rows)


@st.cache_data
def gen_activation_quality(the_dt: dt.date) -> pd.DataFrame:
    rows = []
    for name, app_id, app_name in ENTERPRISES:
        cum_reg = _si(the_dt, app_id, "creg", lo=8000, hi=210000)
        rate = _sf(the_dt, app_id, "ar", lo=0.55, hi=0.72, nd=4)
        cum_act = int(cum_reg * rate)
        n7_reg = _si(the_dt, app_id, "n7r", lo=50, hi=13000)
        n7_act = int(n7_reg * _sf(the_dt, app_id, "n7ar", lo=0.55, hi=0.72, nd=4))
        rows.append({
            "app_id": app_id,
            "app_name": app_name,
            "累计注册": cum_reg,
            "累计激活": cum_act,
            "激活率": round(rate * 100, 1),
            "近7日新增注册": n7_reg,
            "近7日新增激活": n7_act,
        })
    return pd.DataFrame(rows).sort_values("累计激活", ascending=False).reset_index(drop=True)


@st.cache_data
def gen_round_distribution(the_dt: dt.date) -> pd.DataFrame:
    rows = []
    base_7 = [73000, 27000, 10000, 12000, 6000, 6500, 6500, 6800, 7000]
    for i, b in enumerate(ROUND_BUCKETS):
        v7 = int(base_7[i] * _sf(the_dt, b, "7", lo=0.85, hi=1.15, nd=3))
        vy = int(v7 * _sf(the_dt, b, "y", lo=0.05, hi=0.4, nd=3))
        rows.append({"分层": b, "周期": "近7日", "设备数": v7})
        rows.append({"分层": b, "周期": "昨日", "设备数": vy})
    return pd.DataFrame(rows)


@st.cache_data
def gen_active_quality(start: dt.date, end: dt.date) -> pd.DataFrame:
    rk = (start.isoformat(), end.isoformat())
    rows = []
    for name, app_id, app_name in ENTERPRISES:
        dau = _si(rk, app_id, "dau", lo=800, hi=13000)
        active_rate = _sf(rk, app_id, "actr", lo=2.0, hi=18.0, nd=2)
        active_days = _sf(rk, app_id, "ad", lo=1.5, hi=7.0, nd=1)
        daily_rounds = _si(rk, app_id, "dr", lo=900000, hi=2900000)
        dev_rounds = _sf(rk, app_id, "devr", lo=20.0, hi=60.0, nd=2)
        dur = _sf(rk, app_id, "dur", lo=8.0, hi=22.0, nd=1)
        rows.append({
            "app_id": app_id,
            "app_name": app_name,
            "活跃设备(DAU)": dau,
            "活跃率": active_rate,
            "周活跃天数": active_days,
            "日均对话轮数": daily_rounds,
            "设备日均轮次": dev_rounds,
            "设备日均使用时长": dur,
        })
    return pd.DataFrame(rows).sort_values("活跃设备(DAU)", ascending=False).reset_index(drop=True)


@st.cache_data
def gen_retention_trend(start: dt.date, end: dt.date) -> pd.DataFrame:
    days = (end - start).days + 1
    rows = []
    for i in range(max(days, 1)):
        d = start + dt.timedelta(days=i)
        r1 = _sf(d, "r1", lo=0.18, hi=0.26, nd=4)
        r3 = _sf(d, "r3", lo=0.10, hi=0.16, nd=4)
        r7 = _sf(d, "r7", lo=0.06, hi=0.11, nd=4)
        rows.append({"date": pd.Timestamp(d), "留存类型": "次日留存", "留存率": r1})
        rows.append({"date": pd.Timestamp(d), "留存类型": "3日留存", "留存率": r3})
        rows.append({"date": pd.Timestamp(d), "留存类型": "7日留存", "留存率": r7})
    return pd.DataFrame(rows)


@st.cache_data
def gen_product_retention(start: dt.date, end: dt.date) -> pd.DataFrame:
    rk = (start.isoformat(), end.isoformat())
    rows = []
    for name, app_id, app_name in ENTERPRISES:
        new_act = _si(rk, app_id, "na", lo=200, hi=14000)
        r1 = _sf(rk, app_id, "r1", lo=18.0, hi=28.0, nd=1)
        r3 = _sf(rk, app_id, "r3", lo=10.0, hi=r1 - 2, nd=1)
        r7 = _sf(rk, app_id, "r7", lo=6.0, hi=r3 - 1, nd=1)
        rm = _sf(rk, app_id, "rm", lo=3.0, hi=r7, nd=1)
        rows.append({
            "app_id": app_id,
            "app_name": app_name,
            "新增激活": new_act,
            "次日留存率": r1,
            "3日留存率": r3,
            "7日留存率": r7,
            "次月留存率": rm,
        })
    return pd.DataFrame(rows).sort_values("新增激活", ascending=False).reset_index(drop=True)


# ── Entry point ────────────────────────────────────────────────────────────────
def render():
    # ── Part 1: 新增注册与激活 ───────────────────────────────────────────────
    st.markdown('<div class="section-title">新增注册与激活</div>', unsafe_allow_html=True)

    st.markdown('<div class="sub-title">周新增设备量变化 Top 产品</div>', unsafe_allow_html=True)

    p1c1, p1c2, _ = st.columns([2, 2, 4])
    with p1c1:
        wk_dt = st.date_input("选择日期 (dt)", value=dt.date(2026, 6, 2), key="wk_dt")
    with p1c2:
        sort_dir = st.radio("排序", ["降序", "升序"], horizontal=True, key="wk_sort")

    wins = []
    for i in range(3):
        end = wk_dt - dt.timedelta(days=7 * i)
        start = end - dt.timedelta(days=6)
        wins.append((start, end))
    w_this, w_prev, w_pprev = wins
    h_this = range_label(*w_this)
    h_prev = range_label(*w_prev)
    h_pprev = range_label(*w_pprev)

    wk_df = gen_weekly_top(wk_dt).rename(columns={
        "_this": f"{h_this}（本周）",
        "_prev": f"{h_prev}（上周）",
        "_pprev": f"{h_pprev}（上上周）",
    })
    wk_df = wk_df.sort_values("环比增量（绝对Δ）", ascending=(sort_dir == "升序")).reset_index(drop=True)

    st.dataframe(
        wk_df,
        use_container_width=True,
        hide_index=True,
        height=360,
        column_config={
            "app_id": st.column_config.TextColumn("app_id"),
            f"{h_this}（本周）": st.column_config.NumberColumn(format="%d"),
            f"{h_prev}（上周）": st.column_config.NumberColumn(format="%d"),
            f"{h_pprev}（上上周）": st.column_config.NumberColumn(format="%d"),
            "环比增量（绝对Δ）": st.column_config.NumberColumn(format="%d"),
            "环比增量%（百分比Δ）": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )
    st.download_button(
        "⬇ 导出周新增Top表 CSV",
        data=wk_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"module_3_weekly_top_{wk_dt}.csv",
        mime="text/csv",
        key="dl_wk",
    )

    st.markdown('<div class="sub-title">激活质量表</div>', unsafe_allow_html=True)

    aq_dt = st.date_input("选择日期 (dt)", value=dt.date(2026, 6, 2), key="aq_dt")
    aq_df = gen_activation_quality(aq_dt)
    st.dataframe(
        aq_df,
        use_container_width=True,
        hide_index=True,
        height=360,
        column_config={
            "app_id": st.column_config.TextColumn("app_id"),
            "累计注册": st.column_config.NumberColumn(format="%d"),
            "累计激活": st.column_config.NumberColumn(format="%d"),
            "激活率": st.column_config.NumberColumn(format="%.1f%%"),
            "近7日新增注册": st.column_config.NumberColumn(format="%d"),
            "近7日新增激活": st.column_config.NumberColumn(format="%d"),
        },
    )
    st.download_button(
        "⬇ 导出激活质量表 CSV",
        data=aq_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"module_3_activation_quality_{aq_dt}.csv",
        mime="text/csv",
        key="dl_aq",
    )

    st.divider()

    # ── Part 2: 活跃 / 粘性 / 时长 ──────────────────────────────────────────
    st.markdown('<div class="section-title">活跃 / 粘性 / 时长</div>', unsafe_allow_html=True)

    st.markdown('<div class="sub-title">设备轮次分层分布</div>', unsafe_allow_html=True)

    rd_dt = st.date_input("选择日期 (dt)", value=dt.date(2026, 6, 2), key="rd_dt")
    rd_df = gen_round_distribution(rd_dt)

    chart = (
        alt.Chart(rd_df)
        .mark_bar()
        .encode(
            x=alt.X("分层:N", sort=ROUND_BUCKETS, title="对话轮次分层",
                    axis=alt.Axis(labelAngle=0, labelColor="#6b7280", titleColor="#6b7280")),
            xOffset=alt.XOffset("周期:N", sort=["近7日", "昨日"]),
            y=alt.Y("设备数:Q", title="设备数",
                    axis=alt.Axis(labelColor="#6b7280", titleColor="#6b7280")),
            color=alt.Color("周期:N", sort=["近7日", "昨日"],
                            scale=alt.Scale(domain=["近7日", "昨日"],
                                            range=["#4f7cf0", "#3cb371"]),
                            legend=alt.Legend(title=None, orient="top")),
            tooltip=[
                alt.Tooltip("分层:N", title="轮次分层"),
                alt.Tooltip("周期:N", title="周期"),
                alt.Tooltip("设备数:Q", title="设备数", format=","),
            ],
        )
        .properties(height=320)
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)

    st.markdown('<div class="sub-title">分产品活跃质量表</div>', unsafe_allow_html=True)

    aqt_range = st.date_input(
        "时间范围",
        value=(dt.date(2026, 5, 20), dt.date(2026, 6, 2)),
        key="aqt_range",
        help="活跃质量表的统计区间",
    )
    if isinstance(aqt_range, (list, tuple)) and len(aqt_range) == 2:
        aqt_start, aqt_end = aqt_range
    else:
        aqt_start = aqt_end = dt.date(2026, 6, 2)

    aqt_df = gen_active_quality(aqt_start, aqt_end)
    st.dataframe(
        aqt_df,
        use_container_width=True,
        hide_index=True,
        height=360,
        column_config={
            "app_id": st.column_config.TextColumn("app_id"),
            "活跃设备(DAU)": st.column_config.NumberColumn(format="%d"),
            "活跃率": st.column_config.NumberColumn(format="%.2f%%"),
            "周活跃天数": st.column_config.NumberColumn(format="%.1f"),
            "日均对话轮数": st.column_config.NumberColumn(format="%d"),
            "设备日均轮次": st.column_config.NumberColumn(format="%.2f"),
            "设备日均使用时长": st.column_config.NumberColumn(format="%.1f 分"),
        },
    )
    st.download_button(
        "⬇ 导出活跃质量表 CSV",
        data=aqt_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"module_3_active_quality_{aqt_start}_{aqt_end}.csv",
        mime="text/csv",
        key="dl_aqt",
    )

    st.divider()

    # ── Part 3: 留存 ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">留存</div>', unsafe_allow_html=True)

    st.markdown('<div class="sub-title">大盘留存趋势</div>', unsafe_allow_html=True)

    ret_range = st.date_input(
        "时间范围",
        value=(dt.date(2026, 5, 20), dt.date(2026, 6, 2)),
        key="ret_range",
    )
    if isinstance(ret_range, (list, tuple)) and len(ret_range) == 2:
        ret_start, ret_end = ret_range
    else:
        ret_start = ret_end = dt.date(2026, 6, 2)

    ret_df = gen_retention_trend(ret_start, ret_end)
    ret_chart = (
        alt.Chart(ret_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("date:T", title=None,
                    axis=alt.Axis(format="%m-%d", labelColor="#9ca3af")),
            y=alt.Y("留存率:Q", title="留存率",
                    axis=alt.Axis(format="%", labelColor="#9ca3af", titleColor="#9ca3af")),
            color=alt.Color("留存类型:N",
                            scale=alt.Scale(domain=["次日留存", "3日留存", "7日留存"],
                                            range=["#4f7cf0", "#f59e0b", "#ef4444"]),
                            legend=alt.Legend(title=None, orient="top")),
            tooltip=[
                alt.Tooltip("date:T", title="日期", format="%Y-%m-%d"),
                alt.Tooltip("留存类型:N", title="类型"),
                alt.Tooltip("留存率:Q", title="留存率", format=".1%"),
            ],
        )
        .properties(height=300)
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(ret_chart, use_container_width=True)

    st.markdown('<div class="sub-title">分产品留存表</div>', unsafe_allow_html=True)

    pret_range = st.date_input(
        "时间范围",
        value=(dt.date(2026, 5, 20), dt.date(2026, 6, 2)),
        key="pret_range",
    )
    if isinstance(pret_range, (list, tuple)) and len(pret_range) == 2:
        pret_start, pret_end = pret_range
    else:
        pret_start = pret_end = dt.date(2026, 6, 2)

    pret_df = gen_product_retention(pret_start, pret_end)
    st.dataframe(
        pret_df,
        use_container_width=True,
        hide_index=True,
        height=360,
        column_config={
            "app_id": st.column_config.TextColumn("app_id"),
            "新增激活": st.column_config.NumberColumn(format="%d"),
            "次日留存率": st.column_config.NumberColumn(format="%.1f%%"),
            "3日留存率": st.column_config.NumberColumn(format="%.1f%%"),
            "7日留存率": st.column_config.NumberColumn(format="%.1f%%"),
            "次月留存率": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )
    st.download_button(
        "⬇ 导出分产品留存表 CSV",
        data=pret_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"module_3_product_retention_{pret_start}_{pret_end}.csv",
        mime="text/csv",
        key="dl_pret",
    )
