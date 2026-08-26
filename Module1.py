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

    retention = (0.52 + 0.03 * np.sin(2 * np.pi * (t + 1) / 7) +
                 rng.normal(0, 0.012, n_days)).clip(0.42, 0.62)
    retention_3d = (0.41 + 0.028 * np.sin(2 * np.pi * (t + 2) / 7) +
                    rng.normal(0, 0.012, n_days)).clip(0.32, 0.50)
    retention_7d = (0.31 + 0.025 * np.sin(2 * np.pi * (t + 3) / 7) +
                    rng.normal(0, 0.012, n_days)).clip(0.22, 0.40)
    active_retention = (0.785 + 0.02 * np.sin(2 * np.pi * (t + 2) / 7) +
                        rng.normal(0, 0.008, n_days)).clip(0.72, 0.84)

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
        "retention_3d": retention_3d,
        "retention_7d": retention_7d,
        "active_retention": active_retention,
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


def line_chart(frame, y_field, y_title, tooltip_fields, color="#5eead4",
               y_format=None, height=140):
    base = alt.Chart(frame).encode(
        x=alt.X("date:T", title=None, axis=alt.Axis(format="%m-%d", labelColor="#8b95a5")),
    )
    line = base.mark_line(color=color, point=False).encode(
        y=alt.Y(f"{y_field}:Q", title=y_title,
                axis=alt.Axis(labelColor="#8b95a5", titleColor="#8b95a5",
                              gridColor="#1f2733",
                              format=y_format) if y_format else
                alt.Axis(labelColor="#8b95a5", titleColor="#8b95a5", gridColor="#1f2733")),
    )
    points = base.mark_circle(size=45, color=color, opacity=0).encode(
        y=alt.Y(f"{y_field}:Q"),
        tooltip=tooltip_fields,
    )
    return (line + points).properties(height=height).configure_view(strokeWidth=0)


def multi_line_chart(frame, series, x_label, y_format=None, height=140):
    """series: list of (field, label, color). Renders multiple lines with a legend."""
    long_rows = []
    for field, label, _color in series:
        sub = frame[["date", field]].rename(columns={field: "value"})
        sub["series"] = label
        long_rows.append(sub)
    long_df = pd.concat(long_rows, ignore_index=True)

    labels = [s[1] for s in series]
    colors = [s[2] for s in series]
    color_scale = alt.Scale(domain=labels, range=colors)

    base = alt.Chart(long_df).encode(
        x=alt.X("date:T", title=None, axis=alt.Axis(format="%m-%d", labelColor="#8b95a5")),
        color=alt.Color("series:N", scale=color_scale,
                        legend=alt.Legend(title=None, orient="top", labelColor="#8b95a5")),
    )
    y_axis = (alt.Axis(labelColor="#8b95a5", titleColor="#8b95a5", gridColor="#1f2733", format=y_format)
              if y_format else
              alt.Axis(labelColor="#8b95a5", titleColor="#8b95a5", gridColor="#1f2733"))
    line = base.mark_line(point=False).encode(
        y=alt.Y("value:Q", title=None, axis=y_axis),
    )
    fmt = y_format if y_format else ",.0f"
    points = base.mark_circle(size=45, opacity=0).encode(
        y=alt.Y("value:Q"),
        tooltip=[
            alt.Tooltip("date:T", title=x_label, format="%Y-%m-%d"),
            alt.Tooltip("series:N", title="指标"),
            alt.Tooltip("value:Q", title="留存率", format=fmt),
        ],
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

    # 生效范围存于 session_state,点“查询”才应用
    if "m1_start" not in st.session_state:
        st.session_state["m1_start"] = default_start
        st.session_state["m1_end"] = max_date

    c1, c2, c3, _ = st.columns([3, 1, 1, 5])
    with c1:
        date_range = st.date_input(
            "时间范围",
            value=(st.session_state["m1_start"], st.session_state["m1_end"]),
            min_value=min_date,
            max_value=max_date,
            key="m1_picker",
            help="控制横轴铺多宽（可观察区间，限制在近两周内）",
        )
    with c2:
        st.markdown('<div style="height:1.75rem"></div>', unsafe_allow_html=True)
        query_clicked = st.button("查询", use_container_width=True, type="primary", key="m1_query")
    with c3:
        st.markdown('<div style="height:1.75rem"></div>', unsafe_allow_html=True)
        reset_clicked = st.button("重置", use_container_width=True, key="m1_reset")

    if query_clicked and isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        st.session_state["m1_start"], st.session_state["m1_end"] = date_range

    if reset_clicked:
        st.session_state["m1_start"] = default_start
        st.session_state["m1_end"] = max_date
        st.rerun()

    start_date = st.session_state["m1_start"]
    end_date = st.session_state["m1_end"]

    # ── 折线图区域筛选:App ID / 标签(占位,数据联动后续接入) ──────────────
    APP_ID_OPTIONS = ["全部", "app_1001", "app_1002", "app_1003", "app_1004"]
    TAG_OPTIONS = ["智能音箱", "车载", "手表", "耳机", "大屏"]

    f1, f2, f3, _ = st.columns([3, 3, 3, 3])
    with f1:
        sel_app_ids = st.multiselect(
            "App ID",
            options=APP_ID_OPTIONS,
            key="m1_app_ids",
            placeholder="选择 App ID",
        )
    with f2:
        sel_tags = st.multiselect(
            "标签",
            options=TAG_OPTIONS,
            key="m1_tags",
            placeholder="选择标签",
        )
    with f3:
        sel_unique_entry = st.selectbox(
            "是否唯一入口",
            options=["全部", "唯一入口", "其他"],
            index=0,
            key="m1_unique_entry",
        )

    mask = (FULL_DF["date"].dt.date >= start_date) & (FULL_DF["date"].dt.date <= end_date)
    df = FULL_DF.loc[mask].copy().reset_index(drop=True)

    # 保存给「统计汇总」使用(该表已挪至页面底部,分产品统计汇总正上方)
    st.session_state["m1_summary_df"] = df
    st.session_state["m1_summary_start"] = start_date
    st.session_state["m1_summary_end"] = end_date

    adf = aggregate(df, "日")
    x_label = "日期"

    # ── 设备规模 ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">设备规模</div>', unsafe_allow_html=True)
    row1 = st.columns(2)

    with row1[0]:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                cur_cum_reg = adf["cum_reg"].iloc[-1]
                delta_reg = (adf["cum_reg"].iloc[-1] - adf["cum_reg"].iloc[-2]) / adf["cum_reg"].iloc[-2] if len(adf) > 1 else 0
                yest_new_reg = adf["new_reg"].iloc[-1]
                dod_reg = (adf["new_reg"].iloc[-1] / adf["new_reg"].iloc[-2] - 1) if len(adf) > 1 and adf["new_reg"].iloc[-2] != 0 else 0
                st.markdown('<div class="metric-label">累计注册设备</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-big">{fmt_num(cur_cum_reg)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-sub">新增注册设备 {fmt_num(48327)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-sub">昨日新增 +{fmt_num(yest_new_reg)}</div>', unsafe_allow_html=True)
                if dod_reg >= 0:
                    st.markdown(f'<div class="metric-sub">日环比DoD <span class="delta-up">↗ {dod_reg*100:.2f}%</span></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="metric-sub">日环比DoD <span class="delta-down">↘ {abs(dod_reg)*100:.2f}%</span></div>', unsafe_allow_html=True)
            with right:
                tip = [
                    alt.Tooltip("date:T", title=x_label, format="%Y-%m-%d"),
                    alt.Tooltip("new_reg:Q", title="单日新增注册设备量", format=","),
                ]
                st.altair_chart(
                    line_chart(adf, "new_reg", "单日新增注册", tip, color="#3b82f6"),
                    use_container_width=True,
                )

    with row1[1]:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                cur_cum_act = adf["cum_act"].iloc[-1]
                cur_ar = adf["act_rate"].iloc[-1]
                st.markdown('<div class="metric-label">累计激活设备</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-big">{fmt_num(cur_cum_act)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-sub">新增激活设备 {fmt_num(33415)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-sub">激活率 {pct(cur_ar)}</div>', unsafe_allow_html=True)
            with right:
                tip = [
                    alt.Tooltip("date:T", title=x_label, format="%Y-%m-%d"),
                    alt.Tooltip("new_act:Q", title="单日新增激活设备量", format=","),
                    alt.Tooltip("act_rate:Q", title="当日激活率", format=".1%"),
                ]
                st.altair_chart(
                    line_chart(adf, "new_act", "单日新增激活", tip, color="#5eead4"),
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
                    line_chart(adf, "dau", "DAU", tip, color="#a855f7"),
                    use_container_width=True,
                )

    with row2[1]:
        with st.container(border=True):
            active_label = "活跃率"
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
                               color="#22d3ee", y_format="%"),
                    use_container_width=True,
                )

    # ── 留存 ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">留存</div>', unsafe_allow_html=True)
    row_ret = st.columns(2)

    with row_ret[0]:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                cur_ret_d1 = adf["retention"].iloc[-1]
                cur_ret_d7 = adf["retention_7d"].iloc[-1]
                st.markdown('<div class="metric-label">新增设备留存</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="delta-up" style="color:var(--text)">次日 {pct(cur_ret_d1)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="delta-up" style="color:var(--text)">7日 {pct(cur_ret_d7)}</div>', unsafe_allow_html=True)
            with right:
                st.altair_chart(
                    multi_line_chart(
                        adf,
                        [("retention", "次日留存", "#38bdf8"),
                         ("retention_7d", "7日留存", "#fb923c")],
                        x_label, y_format="%",
                    ),
                    use_container_width=True,
                )

    with row_ret[1]:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                cur_act_ret = adf["active_retention"].iloc[-1]
                st.markdown('<div class="metric-label">活跃设备留存</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="delta-up" style="color:var(--text)">次日 {pct(cur_act_ret)}</div>', unsafe_allow_html=True)
            with right:
                tip = [
                    alt.Tooltip("date:T", title=x_label, format="%Y-%m-%d"),
                    alt.Tooltip("active_retention:Q", title="活跃设备次日留存", format=".1%"),
                ]
                st.altair_chart(
                    line_chart(adf, "active_retention", "活跃设备次日留存", tip,
                               color="#a855f7", y_format="%"),
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
                    line_chart(adf, "total_rounds", "日均对话轮数", tip, color="#ec4899"),
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
                    line_chart(adf, "avg_rounds_device", "日均设备对话轮次", tip, color="#22d3ee"),
                    use_container_width=True,
                )

    row4 = st.columns(2)
    with row4[0]:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                last_total_dur = df.sort_values("date")["total_duration"].iloc[-1] / 60
                st.markdown('<div class="metric-label">昨日总对话时长</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="metric-big">{fmt_num(last_total_dur)}'
                    f'<span style="font-size:14px;color:#94a3b8"> 小时</span></div>',
                    unsafe_allow_html=True,
                )
            with right:
                dur_df = adf.assign(total_duration_h=adf["total_duration"] / 60)
                tip = [
                    alt.Tooltip("date:T", title=x_label, format="%Y-%m-%d"),
                    alt.Tooltip("total_duration_h:Q", title="总对话时长(小时)", format=",.1f"),
                ]
                st.altair_chart(
                    line_chart(dur_df, "total_duration_h", "日总对话时长(小时)", tip, color="#22d3ee"),
                    use_container_width=True,
                )

    with row4[1]:
        with st.container(border=True):
            left, right = st.columns([1, 2])
            with left:
                last_avg_dur = df.sort_values("date")["avg_duration_device"].iloc[-1] / 60
                st.markdown('<div class="metric-label">昨日设备平均对话时长</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="metric-big">{last_avg_dur:.2f}'
                    f'<span style="font-size:14px;color:#94a3b8"> 小时</span></div>',
                    unsafe_allow_html=True,
                )
            with right:
                avgdur_df = adf.assign(avg_duration_device_h=adf["avg_duration_device"] / 60)
                tip = [
                    alt.Tooltip("date:T", title=x_label, format="%Y-%m-%d"),
                    alt.Tooltip("avg_duration_device_h:Q", title="设备平均对话时长(小时)", format=".2f"),
                ]
                st.altair_chart(
                    line_chart(avgdur_df, "avg_duration_device_h", "设备平均对话时长(小时)", tip, color="#fb923c"),
                    use_container_width=True,
                )


def render_summary():
    # ── 统计汇总 ──────────────────────────────────────────────────────────────
    df = st.session_state.get("m1_summary_df")
    if df is None:
        return
    start_date = st.session_state.get("m1_summary_start")
    end_date = st.session_state.get("m1_summary_end")

    st.markdown('<div class="section-title">统计汇总</div>', unsafe_allow_html=True)

    table = df.sort_values("date", ascending=False).copy()

    COLUMNS = [
        "日期", "新增注册设备量", "累计注册设备", "新增激活设备量", "累计激活设备",
        "激活率", "DAU", "次日留存率", "3日留存率", "7日留存率",
        "活跃率", "设备平均对话轮次", "设备平均对话时长",
    ]

    def _pct(s):
        return (s * 100).round(2).astype(str) + "%"

    # 明细行(按日期倒序)
    detail = pd.DataFrame({
        "日期": table["date"].dt.strftime("%Y-%m-%d"),
        "累计注册设备": table["cum_reg"].map(fmt_num),
        "新增注册设备量": table["new_reg"].map(fmt_num),
        "累计激活设备": table["cum_act"].map(fmt_num),
        "激活率": _pct(table["act_rate"]),
        "新增激活设备量": table["new_act"].map(fmt_num),
        "DAU": table["dau"].map(fmt_num),
        "次日留存率": _pct(table["retention"]),
        "3日留存率": _pct(table["retention_3d"]),
        "7日留存率": _pct(table["retention_7d"]),
        "活跃率": _pct(table["active_rate"]),
        "设备平均对话轮次": table["avg_rounds_device"].round(2).astype(str),
        "设备平均对话时长": (table["total_duration"] / 60).round(2).astype(str) + " 小时",
    })[COLUMNS].reset_index(drop=True)

    # 合计行:期末累计取最新值,新增/DAU 等取区间合计或均值
    total_row = {
        "日期": "合计",
        "累计注册设备": fmt_num(table["cum_reg"].iloc[0]),
        "新增注册设备量": fmt_num(table["new_reg"].sum()),
        "累计激活设备": fmt_num(table["cum_act"].iloc[0]),
        "激活率": f'{table["act_rate"].iloc[0] * 100:.2f}%',
        "新增激活设备量": fmt_num(table["new_act"].sum()),
        "DAU": fmt_num(round(table["dau"].mean())),
        "次日留存率": f'{table["retention"].mean() * 100:.2f}%',
        "3日留存率": f'{table["retention_3d"].mean() * 100:.2f}%',
        "7日留存率": f'{table["retention_7d"].mean() * 100:.2f}%',
        "活跃率": f'{table["active_rate"].mean() * 100:.2f}%',
        "设备平均对话轮次": f'{table["avg_rounds_device"].mean():.2f}',
        "设备平均对话时长": f'{(table["total_duration"].sum() / table["dau"].sum() / 60):.2f} 小时',
    }

    # ── 表格最多 10 行(合计行置顶 + 最近 9 天明细) ────────────────────────
    page_detail = detail.iloc[:9]

    # 组装 HTML 表格:合计行加粗置顶
    thead = "".join(f"<th>{c}</th>" for c in COLUMNS)
    total_cells = "".join(
        f'<td style="font-weight:700;color:var(--text)">{total_row[c]}</td>'
        for c in COLUMNS
    )
    body_rows = [f'<tr style="background:rgba(94,234,212,0.08)">{total_cells}</tr>']
    for _, r in page_detail.iterrows():
        cells = "".join(f"<td>{r[c]}</td>" for c in COLUMNS)
        body_rows.append(f"<tr>{cells}</tr>")

    html = (
        '<table class="wk-table">'
        f"<thead><tr>{thead}</tr></thead>"
        f'<tbody>{"".join(body_rows)}</tbody>'
        "</table>"
    )
    st.markdown(html, unsafe_allow_html=True)

    # 导出全部明细(含合计行置顶)
    export_df = pd.concat([pd.DataFrame([total_row])[COLUMNS], detail], ignore_index=True)
    csv = export_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇ 导出 CSV",
        data=csv,
        file_name=f"module_1_{start_date}_{end_date}.csv",
        mime="text/csv",
    )
