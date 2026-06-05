"""
Module 1 — 核心指标看板
Embedded via render() in app.py
"""

import datetime as dt
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt


@st.cache_data
def generate_mock_data(seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n_days = 35
    end = dt.date.today()
    dates = [end - dt.timedelta(days=i) for i in range(n_days - 1, -1, -1)]

    t = np.arange(n_days)
    weekly = 1500 * (1 + 0.5 * np.sin(2 * np.pi * t / 7))
    trend = 30 * t
    new_reg = (weekly + trend + rng.normal(0, 400, n_days)).clip(min=200).round()

    base_cum = 1_120_000
    cum_reg = base_cum + np.cumsum(new_reg)

    new_act = (new_reg * rng.uniform(0.55, 0.72, n_days)).round()
    base_cum_act = int(base_cum * 0.63)
    cum_act = base_cum_act + np.cumsum(new_act)

    act_rate = cum_act / cum_reg

    dau = (40000 + 9000 * np.sin(2 * np.pi * (t + 2) / 7) +
           rng.normal(0, 2500, n_days) + 120 * t).clip(min=20000).round()

    active_rate = dau / cum_reg

    retention = (0.20 + 0.04 * np.sin(2 * np.pi * (t + 1) / 7) +
                 rng.normal(0, 0.012, n_days)).clip(0.1, 0.4)

    total_rounds = (dau * rng.uniform(35, 52, n_days)).round()
    avg_rounds_device = (total_rounds / dau).round(2)

    avg_duration_per_round = rng.uniform(2.0, 4.5, n_days)
    total_duration = (total_rounds * avg_duration_per_round).round().astype(int)
    avg_duration_device = (total_duration / dau).round(2)

    return pd.DataFrame({
        "date": pd.to_datetime(dates),
        "new_reg": new_reg.astype(int),
        "cum_reg": cum_reg.astype(int),
        "new_act": new_act.astype(int),
        "cum_act": cum_act.astype(int),
        "act_rate": act_rate,
        "dau": dau.astype(int),
        "active_rate": active_rate,
        "retention": retention,
        "total_rounds": total_rounds.astype(int),
        "avg_rounds_device": avg_rounds_device,
        "total_duration": total_duration,
        "avg_duration_device": avg_duration_device,
    })


def aggregate(frame: pd.DataFrame, gran: str) -> pd.DataFrame:
    if gran == "日":
        out = frame.copy()
        out["bucket"] = out["date"]
        return out

    f = frame.copy()
    f["bucket"] = f["date"].dt.to_period("W-SUN").apply(lambda p: p.start_time)
    agg = f.groupby("bucket").agg(
        new_reg=("new_reg", "sum"),
        cum_reg=("cum_reg", "last"),
        new_act=("new_act", "sum"),
        cum_act=("cum_act", "last"),
        dau=("dau", "mean"),
        retention=("retention", "mean"),
        total_rounds=("total_rounds", "sum"),
        avg_rounds_device=("avg_rounds_device", "mean"),
        total_duration=("total_duration", "sum"),
        avg_duration_device=("avg_duration_device", "mean"),
    ).reset_index()
    agg["act_rate"] = agg["cum_act"] / agg["cum_reg"]
    agg["active_rate"] = agg["dau"] / agg["cum_reg"]
    agg["dau"] = agg["dau"].round().astype(int)
    agg["avg_rounds_device"] = agg["avg_rounds_device"].round(2)
    agg["avg_duration_device"] = agg["avg_duration_device"].round(2)
    agg["date"] = agg["bucket"]
    return agg


def line_chart(frame, y_field, y_title, tooltip_fields, color="#2563eb",
               y_format=None, height=140):
    base = alt.Chart(frame).encode(
        x=alt.X("date:T", title=None, axis=alt.Axis(format="%m-%d", labelColor="#9ca3af")),
    )
    line = base.mark_line(color=color, point=False).encode(
        y=alt.Y(f"{y_field}:Q", title=y_title,
                axis=alt.Axis(labelColor="#9ca3af", titleColor="#9ca3af",
                              format=y_format) if y_format else
                alt.Axis(labelColor="#9ca3af", titleColor="#9ca3af")),
    )
    points = base.mark_circle(size=45, color=color, opacity=0).encode(
        y=alt.Y(f"{y_field}:Q"),
        tooltip=tooltip_fields,
    )
    return (line + points).properties(height=height).configure_view(strokeWidth=0)


def pct(x):
    return f"{x*100:.1f}%"


def fmt_num(x):
    return f"{int(x):,}"


def render():
    FULL_DF = generate_mock_data()

    # ── Controls ──────────────────────────────────────────────────────────────
    min_date = FULL_DF["date"].min().date()
    max_date = FULL_DF["date"].max().date()
    default_start = max_date - dt.timedelta(days=13)

    c1, c2, _ = st.columns([3, 2, 5])
    with c1:
        date_range = st.date_input(
            "时间范围",
            value=(default_start, max_date),
            min_value=min_date,
            max_value=max_date,
            help="控制横轴铺多宽（可观察区间，限制在近两周内）",
        )
    with c2:
        granularity = st.radio(
            "按颗粒度聚合",
            options=["日", "周"],
            horizontal=True,
            help="控制每个数据点怎么算",
        )

    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = default_start, max_date

    mask = (FULL_DF["date"].dt.date >= start_date) & (FULL_DF["date"].dt.date <= end_date)
    df = FULL_DF.loc[mask].copy().reset_index(drop=True)

    adf = aggregate(df, granularity)
    x_label = "日期" if granularity == "日" else "周起始日"

    # ── 设备规模 ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">设备规模</div>', unsafe_allow_html=True)
    row1 = st.columns(2)

    with row1[0]:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                cur_cum_reg = adf["cum_reg"].iloc[-1]
                delta_reg = (adf["cum_reg"].iloc[-1] - adf["cum_reg"].iloc[-2]) / adf["cum_reg"].iloc[-2] if len(adf) > 1 else 0
                st.markdown('<div class="metric-label">累计注册设备</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-big">{fmt_num(cur_cum_reg)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="delta-up" style="font-size:15px">↗ {delta_reg*100:.1f}%</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-sub">今日新增 +{fmt_num(adf["new_reg"].iloc[-1])}</div>', unsafe_allow_html=True)
            with right:
                tip = [
                    alt.Tooltip("date:T", title=x_label, format="%Y-%m-%d"),
                    alt.Tooltip("new_reg:Q", title="单日新增注册设备量", format=","),
                ]
                st.altair_chart(
                    line_chart(adf, "new_reg", "单日新增注册", tip, color="#2563eb"),
                    use_container_width=True,
                )

    with row1[1]:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                cur_cum_act = adf["cum_act"].iloc[-1]
                delta_act = (adf["cum_act"].iloc[-1] - adf["cum_act"].iloc[-2]) / adf["cum_act"].iloc[-2] if len(adf) > 1 else 0
                cur_ar = adf["act_rate"].iloc[-1]
                st.markdown('<div class="metric-label">累计激活设备</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-big">{fmt_num(cur_cum_act)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="delta-up" style="font-size:15px">↗ {delta_act*100:.1f}%</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-sub">激活率 {pct(cur_ar)}</div>', unsafe_allow_html=True)
            with right:
                tip = [
                    alt.Tooltip("date:T", title=x_label, format="%Y-%m-%d"),
                    alt.Tooltip("new_act:Q", title="单日新增激活设备量", format=","),
                    alt.Tooltip("act_rate:Q", title="当日激活率", format=".1%"),
                ]
                st.altair_chart(
                    line_chart(adf, "new_act", "单日新增激活", tip, color="#16a34a"),
                    use_container_width=True,
                )

    # ── 活跃 ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">活跃</div>', unsafe_allow_html=True)
    row2 = st.columns(2)

    with row2[0]:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                daily = df.sort_values("date")
                last_dau = daily["dau"].iloc[-1]
                dod = (daily["dau"].iloc[-1] / daily["dau"].iloc[-2] - 1) if len(daily) > 1 else 0
                wow = (daily["dau"].iloc[-1] / daily["dau"].iloc[-8] - 1) if len(daily) > 7 else None
                st.markdown('<div class="metric-label">昨日 DAU</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-big">{fmt_num(last_dau)}</div>', unsafe_allow_html=True)
                dod_cls = "delta-up" if dod >= 0 else "delta-down"
                arrow = "↗" if dod >= 0 else "↘"
                st.markdown(f'<div class="{dod_cls}">日环比 DoD {arrow} {dod*100:.1f}%</div>', unsafe_allow_html=True)
                if wow is not None:
                    wow_cls = "delta-up" if wow >= 0 else "delta-down"
                    warrow = "↗" if wow >= 0 else "↘"
                    st.markdown(f'<div class="{wow_cls}">周同比 WoW {warrow} {wow*100:.1f}%</div>', unsafe_allow_html=True)
            with right:
                tip = [
                    alt.Tooltip("date:T", title=x_label, format="%Y-%m-%d"),
                    alt.Tooltip("dau:Q", title="当日 DAU", format=","),
                ]
                st.altair_chart(
                    line_chart(adf, "dau", "DAU", tip, color="#2563eb"),
                    use_container_width=True,
                )

    with row2[1]:
        with st.container(border=True):
            active_label = "周活率" if granularity == "周" else "活跃率"
            left, right = st.columns([1, 2])
            with left:
                cur_active = adf["active_rate"].iloc[-1]
                st.markdown(f'<div class="metric-label">{active_label}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-big">{pct(cur_active)}</div>', unsafe_allow_html=True)
            with right:
                tip = [
                    alt.Tooltip("date:T", title=x_label, format="%Y-%m-%d"),
                    alt.Tooltip("active_rate:Q", title=active_label, format=".2%"),
                ]
                st.altair_chart(
                    line_chart(adf, "active_rate", active_label, tip,
                               color="#0891b2", y_format="%"),
                    use_container_width=True,
                )

    # ── 留存与互动 ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">互动深度</div>', unsafe_allow_html=True)
    row3 = st.columns(2)

    with row3[0]:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                last_rounds = df.sort_values("date")["total_rounds"].iloc[-1]
                st.markdown('<div class="metric-label">昨日总对话轮数</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-big">{fmt_num(last_rounds)}</div>', unsafe_allow_html=True)
            with right:
                tip = [
                    alt.Tooltip("date:T", title=x_label, format="%Y-%m-%d"),
                    alt.Tooltip("total_rounds:Q", title="对话轮数", format=","),
                ]
                st.altair_chart(
                    line_chart(adf, "total_rounds", "日均对话轮数", tip, color="#2563eb"),
                    use_container_width=True,
                )

    with row3[1]:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                last_avg = df.sort_values("date")["avg_rounds_device"].iloc[-1]
                st.markdown('<div class="metric-label">昨日设备平均对话轮次</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-big">{last_avg:.2f}</div>', unsafe_allow_html=True)
            with right:
                tip = [
                    alt.Tooltip("date:T", title=x_label, format="%Y-%m-%d"),
                    alt.Tooltip("avg_rounds_device:Q", title="日均设备对话轮次", format=".2f"),
                ]
                st.altair_chart(
                    line_chart(adf, "avg_rounds_device", "日均设备对话轮次", tip, color="#2563eb"),
                    use_container_width=True,
                )

    row4 = st.columns(2)
    with row4[0]:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                last_total_dur = df.sort_values("date")["total_duration"].iloc[-1]
                st.markdown('<div class="metric-label">昨日总对话时长</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="metric-big">{fmt_num(last_total_dur)}'
                    f'<span style="font-size:14px;color:#94a3b8"> 分钟</span></div>',
                    unsafe_allow_html=True,
                )
            with right:
                tip = [
                    alt.Tooltip("date:T", title=x_label, format="%Y-%m-%d"),
                    alt.Tooltip("total_duration:Q", title="总对话时长(分钟)", format=","),
                ]
                st.altair_chart(
                    line_chart(adf, "total_duration", "日总对话时长", tip, color="#0891b2"),
                    use_container_width=True,
                )

    with row4[1]:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                last_avg_dur = df.sort_values("date")["avg_duration_device"].iloc[-1]
                st.markdown('<div class="metric-label">昨日设备平均对话时长</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="metric-big">{last_avg_dur:.1f}'
                    f'<span style="font-size:14px;color:#94a3b8"> 分钟</span></div>',
                    unsafe_allow_html=True,
                )
            with right:
                tip = [
                    alt.Tooltip("date:T", title=x_label, format="%Y-%m-%d"),
                    alt.Tooltip("avg_duration_device:Q", title="设备平均对话时长(分钟)", format=".1f"),
                ]
                st.altair_chart(
                    line_chart(adf, "avg_duration_device", "设备平均对话时长", tip, color="#ea580c"),
                    use_container_width=True,
                )

    # ── 统计汇总 ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">统计汇总</div>', unsafe_allow_html=True)

    table = df.sort_values("date", ascending=False).copy()
    table_out = pd.DataFrame({
        "日期": table["date"].dt.strftime("%Y-%m-%d"),
        "累计注册设备量": table["cum_reg"],
        "单日新增注册设备量": table["new_reg"],
        "累计激活设备量": table["cum_act"],
        "单日新增激活设备量": table["new_act"],
        "激活率": (table["act_rate"] * 100).round(2).astype(str) + "%",
        "DAU": table["dau"],
        "活跃率": (table["active_rate"] * 100).round(2).astype(str) + "%",
        "次日留存率": (table["retention"] * 100).round(2).astype(str) + "%",
        "总对话轮数": table["total_rounds"],
        "设备平均对话轮次": table["avg_rounds_device"],
        "总对话时长(分钟)": table["total_duration"],
        "设备平均对话时长(分钟)": table["avg_duration_device"],
    })

    st.dataframe(table_out, use_container_width=True, hide_index=True)

    csv = table_out.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇ 导出 CSV",
        data=csv,
        file_name=f"module_1_{start_date}_{end_date}.csv",
        mime="text/csv",
    )
