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
def gen_app_detail(the_dt: dt.date) -> pd.DataFrame:
    rows = []
    for name, app_id, app_name in ENTERPRISES:
        k = (the_dt.isoformat(), app_id)
        cum_reg = _si(k, "creg", lo=7000, hi=210000)
        new_reg_y = _si(k, "nregy", lo=1, hi=1500)
        new_reg_7 = _si(k, "nreg7", lo=new_reg_y, hi=new_reg_y * 9 + 10)
        act_y = _si(k, "act_y", lo=1100, hi=13000)
        act_7 = _si(k, "act7", lo=int(act_y * 0.5), hi=act_y)
        cum_act = _si(k, "cact", lo=2900, hi=68000)
        new_act_y = int(new_reg_y * (_si(k, "ar", lo=550, hi=720) / 1000))
        new_act_7 = int(new_reg_7 * (_si(k, "ar7", lo=550, hi=720) / 1000))
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
def gen_product_retention(start: dt.date, end: dt.date) -> pd.DataFrame:
    rk = (start.isoformat(), end.isoformat())
    rows = []
    for name, app_id, app_name in ENTERPRISES:
        new_act = _si(rk, app_id, "na", lo=200, hi=14000)
        r1 = _sf(rk, app_id, "r1", lo=18.0, hi=28.0, nd=1)
        r3 = _sf(rk, app_id, "r3", lo=10.0, hi=r1 - 2, nd=1)
        r7 = _sf(rk, app_id, "r7", lo=6.0, hi=r3 - 1, nd=1)
        rows.append({
            "app_id": app_id,
            "app_name": app_name,
            "新增激活": new_act,
            "次日留存率": r1,
            "3日留存率": r3,
            "7日留存率": r7,
        })
    return pd.DataFrame(rows).sort_values("新增激活", ascending=False).reset_index(drop=True)


_HM_DAYS   = [0,  1,  2,  3,  4,  5,  6,  7,  14,  30]
_HM_LABELS = ["当天(Day 0)", "第1天", "第2天", "第3天", "第4天",
              "第5天", "第6天", "第7天", "第14天", "第30天"]
_HM_RANGES = {
    1:  (28.0, 52.0), 2:  (22.0, 42.0), 3:  (17.0, 35.0),
    4:  (13.0, 30.0), 5:  (10.0, 25.0), 6:  (8.0,  22.0),
    7:  (7.0,  20.0), 14: (4.0,  14.0), 30: (3.0,   8.0),
}


@st.cache_data
def gen_retention_heatmap(start: dt.date, end: dt.date, today: dt.date) -> pd.DataFrame:
    rows = []
    for i in range(max((end - start).days + 1, 1)):
        d = start + dt.timedelta(days=i)
        base = _si(d.isoformat(), "hm_base", lo=1200, hi=5000)
        age = (today - d).days
        for day_num, day_label in zip(_HM_DAYS, _HM_LABELS):
            if day_num == 0:
                count, rate = base, 100.0
            elif age < day_num:
                count, rate = 0, 0.0
            else:
                lo, hi = _HM_RANGES[day_num]
                rate = _sf(d.isoformat(), str(day_num), "hm_r", lo=lo, hi=hi, nd=1)
                count = int(base * rate / 100)
            rows.append({
                "注册日期": d.strftime("%m-%d"),
                "day_label": day_label,
                "day_num": day_num,
                "count": count,
                "rate": rate,
                "label": f"{count} ({rate:.1f}%)",
            })
    return pd.DataFrame(rows)


@st.cache_data
def gen_overview_retention(start: dt.date, end: dt.date, today: dt.date) -> pd.DataFrame:
    rows = []
    for i in range(max((end - start).days + 1, 1)):
        d = start + dt.timedelta(days=i)
        active = _si(d.isoformat(), "ovret_act", lo=8000, hi=65000)
        r1 = _sf(d.isoformat(), "ovret_r1", lo=18.0, hi=26.0, nd=1)
        r3 = _sf(d.isoformat(), "ovret_r3", lo=10.0, hi=16.0, nd=1)
        r7 = _sf(d.isoformat(), "ovret_r7", lo=6.0, hi=11.0, nd=1)
        age = (today - d).days
        rows.append({
            "周期": d.strftime("%Y-%m-%d"),
            "活跃设备数": active,
            "次日留存率": f"{r1:.1f}%" if age >= 1 else "—",
            "3日留存率": f"{r3:.1f}%" if age >= 3 else "—",
            "7日留存率": f"{r7:.1f}%" if age >= 7 else "—",
        })
    return pd.DataFrame(rows)


@st.cache_data
def gen_new_device_retention(start: dt.date, end: dt.date, today: dt.date) -> pd.DataFrame:
    rows = []
    for i in range(max((end - start).days + 1, 1)):
        d = start + dt.timedelta(days=i)
        new_act = _si(d.isoformat(), "ndret_act", lo=200, hi=3500)
        r1 = _sf(d.isoformat(), "ndret_r1", lo=18.0, hi=28.0, nd=1)
        r3 = _sf(d.isoformat(), "ndret_r3", lo=10.0, hi=16.0, nd=1)
        r7 = _sf(d.isoformat(), "ndret_r7", lo=6.0, hi=11.0, nd=1)
        age = (today - d).days
        rows.append({
            "周期": d.strftime("%Y-%m-%d"),
            "新增激活设备数": new_act,
            "次日留存率": f"{r1:.1f}%" if age >= 1 else "—",
            "3日留存率": f"{r3:.1f}%" if age >= 3 else "—",
            "7日留存率": f"{r7:.1f}%" if age >= 7 else "—",
        })
    return pd.DataFrame(rows)


# ── Product overview helpers ───────────────────────────────────────────────────

def _m3_line_chart(frame, y_field, y_title, tooltip_fields, color="#2563eb", height=130):
    df = frame.copy()
    df["date"] = pd.to_datetime(df["date"])
    base = alt.Chart(df).encode(
        x=alt.X("date:T", title=None, axis=alt.Axis(format="%m-%d", labelColor="#9ca3af")),
    )
    line = base.mark_line(color=color, point=False).encode(
        y=alt.Y(f"{y_field}:Q", title=y_title,
                axis=alt.Axis(labelColor="#9ca3af", titleColor="#9ca3af")),
    )
    points = base.mark_circle(size=45, color=color, opacity=0).encode(
        y=alt.Y(f"{y_field}:Q"),
        tooltip=tooltip_fields,
    )
    return (line + points).properties(height=height).configure_view(strokeWidth=0)


@st.cache_data
def gen_funnel(start: dt.date, end: dt.date, app_filter: str) -> pd.DataFrame:
    STEPS = [
        "首次进入小程序", "首次开始配网", "蓝牙链接成功",
        "WiFi链接成功", "首次配网成功", "首次对话",
        "D1留存", "D3留存", "D7留存",
    ]
    STEP_RATES = [
        (0.55, 0.80), (0.65, 0.90), (0.70, 0.95),
        (0.75, 0.95), (0.60, 0.90), (0.20, 0.50),
        (0.50, 0.80), (0.45, 0.75),
    ]
    lo_base, hi_base = (5000, 80000) if app_filter == "全部" else (200, 5000)
    base = _si(start.isoformat(), end.isoformat(), app_filter, "fn_base", lo=lo_base, hi=hi_base)
    counts = [base]
    for i, (lo, hi) in enumerate(STEP_RATES):
        r = _sf(start.isoformat(), end.isoformat(), app_filter, str(i), "fn_r", lo=lo, hi=hi, nd=3)
        counts.append(int(counts[-1] * r))
    rows = []
    for step, count in zip(STEPS, counts):
        cum_rate = count / base * 100 if base > 0 else 0.0
        rows.append({"关键漏斗指标": step, "用户数": count, "转化率": f"{cum_rate:.1f}%"})
    return pd.DataFrame(rows)


@st.cache_data
def gen_prod_ts(start: dt.date, end: dt.date, app_filter: str) -> pd.DataFrame:
    rows = []
    for i in range(max((end - start).days + 1, 1)):
        d = start + dt.timedelta(days=i)
        if app_filter == "全部":
            new_reg = _si(d.isoformat(), "pov_nr", lo=500, hi=3500)
            active = _si(d.isoformat(), "pov_ac", lo=8000, hi=65000)
            avg_rnd = _si(d.isoformat(), "pov_ar", lo=2500, hi=6000) / 100.0
        else:
            new_reg = _si(d.isoformat(), app_filter, "pov_nr", lo=30, hi=400)
            active = _si(d.isoformat(), app_filter, "pov_ac", lo=200, hi=8000)
            avg_rnd = _si(d.isoformat(), app_filter, "pov_ar", lo=1000, hi=7000) / 100.0
        rows.append({"date": d, "new_reg": new_reg, "active": active, "avg_rounds": avg_rnd})
    return pd.DataFrame(rows)


@st.cache_data
def gen_prod_active_table(the_dt: dt.date, app_filter: str) -> pd.DataFrame:
    rows = []
    apps = ENTERPRISES if app_filter == "全部" else [e for e in ENTERPRISES if e[1] == app_filter]
    for name, app_id, app_name in apps:
        active = _si(the_dt.isoformat(), app_id, "pat_act", lo=100, hi=8000)
        rounds = _si(the_dt.isoformat(), app_id, "pat_rnd", lo=active * 5, hi=active * 80)
        avg_rnd = round(rounds / active, 2) if active > 0 else 0.0
        rows.append({
            "app_id": app_id,
            "app_name": app_name.split("_", 1)[-1] if "_" in app_name else app_name,
            "活跃设备": active,
            "对话轮次": rounds,
            "平均对话轮次": avg_rnd,
        })
    return pd.DataFrame(rows).sort_values("活跃设备", ascending=False).reset_index(drop=True)


@st.cache_data
def gen_prod_round_dist(start: dt.date, end: dt.date, app_filter: str) -> pd.DataFrame:
    BUCKETS = ["10以下", "10_29", "30_49", "50_99", "100_149", "150_249", "250_500", "500以上"]
    base = [73000, 27000, 10000, 12000, 6000, 6500, 6800, 7000]
    if app_filter != "全部":
        base = [max(1, int(b * 0.08)) for b in base]
    rows = []
    for i, bucket in enumerate(BUCKETS):
        v = int(base[i] * _sf(start.isoformat(), end.isoformat(), app_filter, bucket, "rd", lo=0.8, hi=1.2, nd=3))
        rows.append({"分层": bucket, "设备数": v})
    return pd.DataFrame(rows)


@st.cache_data
def gen_prod_active_days_dist(start: dt.date, end: dt.date, app_filter: str) -> pd.DataFrame:
    BUCKETS = ["1-2天", "3-4天", "5-6天", "7-8天", "9-10天", "11-13天", "14-17天", "18-20天", "21-30天"]
    base = [45000, 28000, 18000, 14000, 10000, 8000, 6000, 4000, 3000]
    if app_filter != "全部":
        base = [max(1, int(b * 0.08)) for b in base]
    rows = []
    for i, bucket in enumerate(BUCKETS):
        v = int(base[i] * _sf(start.isoformat(), end.isoformat(), app_filter, bucket, "ad", lo=0.75, hi=1.25, nd=3))
        rows.append({"分层": bucket, "设备数": v})
    return pd.DataFrame(rows)


def render_prod_overview():
    c1, c2, _ = st.columns([2, 3, 3])
    with c1:
        app_opts = ["全部"] + [e[1] for e in ENTERPRISES]
        sel_app = st.selectbox("app_id", options=app_opts, index=0, key="po_app")
    with c2:
        today = dt.date.today()
        default_start = today - dt.timedelta(days=30)
        date_rng = st.date_input("时间范围", value=(default_start, today), key="po_range")

    if isinstance(date_rng, (list, tuple)) and len(date_rng) == 2:
        start_date, end_date = date_rng
    else:
        start_date = end_date = dt.date.today()

    ts = gen_prod_ts(start_date, end_date, sel_app)
    cum_reg = 1_120_000 + int(ts["new_reg"].sum())
    last_active = int(ts["active"].iloc[-1])
    period_active = int(ts["active"].sum())
    last_avg = float(ts["avg_rounds"].iloc[-1])

    st.markdown('<div class="section-title">大盘指标</div>', unsafe_allow_html=True)
    row = st.columns(3)

    with row[0]:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                st.markdown('<div class="metric-label">累计注册设备量</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-big" style="font-size:26px">{cum_reg:,}</div>', unsafe_allow_html=True)
            with right:
                tip = [
                    alt.Tooltip("date:T", title="日期", format="%Y-%m-%d"),
                    alt.Tooltip("new_reg:Q", title="单日新增注册", format=","),
                ]
                st.altair_chart(_m3_line_chart(ts, "new_reg", "单日新增注册设备量", tip), use_container_width=True)

    with row[1]:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                st.markdown('<div class="metric-label">昨日活跃设备量</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-big" style="font-size:26px">{last_active:,}</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-sub">近30日活跃设备量</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-big" style="font-size:26px">{period_active:,}</div>', unsafe_allow_html=True)
            with right:
                tip = [
                    alt.Tooltip("date:T", title="日期", format="%Y-%m-%d"),
                    alt.Tooltip("active:Q", title="活跃设备量", format=","),
                ]
                st.altair_chart(_m3_line_chart(ts, "active", "单日活跃设备量", tip, color="#16a34a"), use_container_width=True)

    with row[2]:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                st.markdown('<div class="metric-label">昨日设备平均轮次</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-big" style="font-size:26px">{last_avg:.2f}</div>', unsafe_allow_html=True)
            with right:
                tip = [
                    alt.Tooltip("date:T", title="日期", format="%Y-%m-%d"),
                    alt.Tooltip("avg_rounds:Q", title="设备平均轮次", format=".2f"),
                ]
                st.altair_chart(_m3_line_chart(ts, "avg_rounds", "单日设备平均轮次", tip, color="#ea580c"), use_container_width=True)

    bot_left, bot_right = st.columns(2)

    with bot_left:
        act_tbl = gen_prod_active_table(end_date, sel_app)
        total_active = int(act_tbl["活跃设备"].sum())
        with st.container(border=True):
            st.markdown('<div class="metric-label">今日活跃设备总量</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-big" style="font-size:28px">{total_active:,}</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-title">今日活跃app</div>', unsafe_allow_html=True)
        st.dataframe(
            act_tbl,
            use_container_width=True,
            hide_index=True,
            height=350,
            column_config={
                "app_id": st.column_config.TextColumn("app_id"),
                "活跃设备": st.column_config.NumberColumn(format="%d"),
                "对话轮次": st.column_config.NumberColumn(format="%d"),
                "平均对话轮次": st.column_config.NumberColumn(format="%.2f"),
            },
        )

    with bot_right:
        ROUND_ORDER = ["10以下", "10_29", "30_49", "50_99", "100_149", "150_249", "250_500", "500以上"]
        AD_ORDER = ["1-2天", "3-4天", "5-6天", "7-8天", "9-10天", "11-13天", "14-17天", "18-20天", "21-30天"]
        tab_rd, tab_ad = st.tabs(["对话轮次详情", "设备活跃分层详情"])

        with tab_rd:
            rd_df = gen_prod_round_dist(start_date, end_date, sel_app)
            bar_rd = (
                alt.Chart(rd_df)
                .mark_bar(color="#4f7cf0")
                .encode(
                    x=alt.X("分层:N", sort=ROUND_ORDER, title="对话轮次分层",
                            axis=alt.Axis(labelAngle=0, labelColor="#6b7280", titleColor="#6b7280")),
                    y=alt.Y("设备数:Q", title="设备数",
                            axis=alt.Axis(labelColor="#6b7280", titleColor="#6b7280")),
                    tooltip=[
                        alt.Tooltip("分层:N", title="轮次分层"),
                        alt.Tooltip("设备数:Q", title="设备数", format=","),
                    ],
                )
                .properties(height=350)
                .configure_view(strokeWidth=0)
            )
            st.altair_chart(bar_rd, use_container_width=True)

        with tab_ad:
            ad_df = gen_prod_active_days_dist(start_date, end_date, sel_app)
            bar_ad = (
                alt.Chart(ad_df)
                .mark_bar(color="#16a34a")
                .encode(
                    x=alt.X("分层:N", sort=AD_ORDER, title="活跃天数",
                            axis=alt.Axis(labelAngle=0, labelColor="#6b7280", titleColor="#6b7280")),
                    y=alt.Y("设备数:Q", title="设备数",
                            axis=alt.Axis(labelColor="#6b7280", titleColor="#6b7280")),
                    tooltip=[
                        alt.Tooltip("分层:N", title="活跃天数"),
                        alt.Tooltip("设备数:Q", title="设备数", format=","),
                    ],
                )
                .properties(height=350)
                .configure_view(strokeWidth=0)
            )
            st.altair_chart(bar_ad, use_container_width=True)


# ── Entry point ────────────────────────────────────────────────────────────────
def render():
    render_prod_overview()
    st.divider()

    # ── 新用户首次配网漏斗 ────────────────────────────────────────────────────
    st.markdown('<div class="section-title">新用户首次配网漏斗</div>', unsafe_allow_html=True)
    fn_c1, fn_c2, _ = st.columns([2, 3, 3])
    with fn_c1:
        fn_app_opts = ["全部"] + [e[1] for e in ENTERPRISES]
        fn_app = st.selectbox("app_id", options=fn_app_opts, index=0, key="fn_app")
    with fn_c2:
        fn_range = st.date_input("时间范围", value=(dt.date(2026, 5, 20), dt.date(2026, 6, 2)), key="fn_range")
    if isinstance(fn_range, (list, tuple)) and len(fn_range) == 2:
        fn_start, fn_end = fn_range
    else:
        fn_start = fn_end = dt.date(2026, 6, 2)

    fn_df = gen_funnel(fn_start, fn_end, fn_app)
    fn_col, _ = st.columns([1, 2])
    with fn_col:
        st.dataframe(
            fn_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "用户数": st.column_config.NumberColumn(format="%d"),
                "转化率": st.column_config.TextColumn("转化率"),
            },
        )

    st.divider()

    # ── app维度明细 ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">app维度明细</div>', unsafe_allow_html=True)

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
        file_name=f"module_3_app_detail_{app_dt}.csv",
        mime="text/csv",
        key="dl_app",
    )

    st.divider()

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

    st.divider()

    # ── Part 2: 活跃 / 粘性 / 时长 ──────────────────────────────────────────
    st.markdown('<div class="section-title">活跃 / 粘性 / 时长</div>', unsafe_allow_html=True)

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

    st.markdown('<div class="sub-title">大盘留存表</div>', unsafe_allow_html=True)

    ovret_range = st.date_input(
        "时间范围",
        value=(dt.date(2026, 5, 20), dt.date(2026, 6, 2)),
        key="ovret_range",
    )
    if isinstance(ovret_range, (list, tuple)) and len(ovret_range) == 2:
        ovret_start, ovret_end = ovret_range
    else:
        ovret_start = ovret_end = dt.date(2026, 6, 2)

    ovret_df = gen_overview_retention(ovret_start, ovret_end, dt.date.today())
    st.dataframe(
        ovret_df,
        use_container_width=True,
        hide_index=True,
        height=360,
        column_config={
            "活跃设备数": st.column_config.NumberColumn(format="%d"),
            "次日留存率": st.column_config.TextColumn("次日留存率"),
            "3日留存率": st.column_config.TextColumn("3日留存率"),
            "7日留存率": st.column_config.TextColumn("7日留存率"),
        },
    )
    st.download_button(
        "⬇ 导出大盘留存表 CSV",
        data=ovret_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"module_3_overview_retention_{ovret_start}_{ovret_end}.csv",
        mime="text/csv",
        key="dl_ovret",
    )

    st.markdown('<div class="sub-title">新增设备留存表</div>', unsafe_allow_html=True)
    st.caption("注：7日留存仅纳入激活满7天的设备，不足7天自动排除")

    ndret_range = st.date_input(
        "时间范围",
        value=(dt.date(2026, 5, 20), dt.date(2026, 6, 2)),
        key="ndret_range",
    )
    if isinstance(ndret_range, (list, tuple)) and len(ndret_range) == 2:
        ndret_start, ndret_end = ndret_range
    else:
        ndret_start = ndret_end = dt.date(2026, 6, 2)

    ndret_df = gen_new_device_retention(ndret_start, ndret_end, dt.date.today())
    st.dataframe(
        ndret_df,
        use_container_width=True,
        hide_index=True,
        height=360,
        column_config={
            "新增激活设备数": st.column_config.NumberColumn(format="%d"),
            "次日留存率": st.column_config.TextColumn("次日留存率"),
            "3日留存率": st.column_config.TextColumn("3日留存率"),
            "7日留存率": st.column_config.TextColumn("7日留存率"),
        },
    )
    st.download_button(
        "⬇ 导出新增设备留存表 CSV",
        data=ndret_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"module_3_new_device_retention_{ndret_start}_{ndret_end}.csv",
        mime="text/csv",
        key="dl_ndret",
    )

    st.markdown('<div class="sub-title">新增设备留存热力图</div>', unsafe_allow_html=True)

    today = dt.date.today()
    hm_range = st.date_input(
        "时间范围",
        value=(today - dt.timedelta(days=30), today),
        key="hm_range",
    )
    if isinstance(hm_range, (list, tuple)) and len(hm_range) == 2:
        hm_start, hm_end = hm_range
    else:
        hm_start = hm_end = today

    hm_df = gen_retention_heatmap(hm_start, hm_end, today)
    date_order = hm_df["注册日期"].unique().tolist()
    n_rows = len(date_order)

    rect = alt.Chart(hm_df).mark_rect().encode(
        x=alt.X("day_label:N", sort=_HM_LABELS, title="距离新增日的天数",
                axis=alt.Axis(labelAngle=0, labelColor="#6b7280", titleColor="#6b7280")),
        y=alt.Y("注册日期:N", sort=date_order, title="新增注册日期",
                axis=alt.Axis(labelColor="#6b7280", titleColor="#6b7280")),
        color=alt.Color("rate:Q",
                        scale=alt.Scale(scheme="blues", domain=[0, 100]),
                        legend=alt.Legend(title="留存率(%)", gradientLength=200,
                                          labelColor="#6b7280", titleColor="#6b7280")),
    )
    text_lyr = alt.Chart(hm_df).mark_text(fontSize=9).encode(
        x=alt.X("day_label:N", sort=_HM_LABELS),
        y=alt.Y("注册日期:N", sort=date_order),
        text=alt.Text("label:N"),
        color=alt.condition(
            alt.datum.rate > 45,
            alt.value("white"),
            alt.value("#374151"),
        ),
    )
    hm_chart = (rect + text_lyr).properties(
        height=max(300, n_rows * 26)
    ).configure_view(strokeWidth=0)
    st.altair_chart(hm_chart, use_container_width=True)

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
        },
    )
    st.download_button(
        "⬇ 导出分产品留存表 CSV",
        data=pret_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"module_3_product_retention_{pret_start}_{pret_end}.csv",
        mime="text/csv",
        key="dl_pret",
    )
