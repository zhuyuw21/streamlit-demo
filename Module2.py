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

JINGZAO_APPS = [
    ("京东京造产品", "10461", "10461_小狗【JZ-01】"),
    ("京东京造产品", "10372", "10372_云朵兔【J】"),
    ("京东京造产品", "10580", "10580_智能音箱【JZ-S1】"),
    ("京东京造产品", "10581", "10581_故事机【JZ-K1】"),
    ("京东京造产品", "10582", "10582_学习机【JZ-E1】"),
    ("京东京造产品", "10583", "10583_早教机器人【JZ-R1】"),
    ("京东京造产品", "10584", "10584_睡眠灯【JZ-L1】"),
    ("京东京造产品", "10585", "10585_点读机【JZ-P1】"),
    ("京东京造产品", "10586", "10586_词典笔【JZ-W1】"),
    ("京东京造产品", "10587", "10587_护眼台灯【JZ-D1】"),
]

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


# ── Overview data generators ───────────────────────────────────────────────────

@st.cache_data
def gen_overview_ts(end_dt: dt.date, n_days: int = 60) -> pd.DataFrame:
    rows = []
    for i in range(n_days):
        d = end_dt - dt.timedelta(days=n_days - 1 - i)
        new_reg = _stable_int(d.isoformat(), "ov_nr", lo=15, hi=90)
        active = _stable_int(d.isoformat(), "ov_ac", lo=70, hi=260)
        avg_rnd = _stable_int(d.isoformat(), "ov_ar", lo=1800, hi=5500) / 100.0
        rows.append({"date": d, "new_reg": new_reg, "active": active, "avg_rounds": avg_rnd})
    return pd.DataFrame(rows)


@st.cache_data
def gen_overview_table(the_dt: dt.date) -> pd.DataFrame:
    rows = []
    for _ename, app_id, app_name in ENTERPRISES:
        k = (the_dt.isoformat(), app_id)
        total_dev = _stable_int(k, "ov_td", lo=40, hi=1900)
        cum_act = int(total_dev * _stable_int(k, "ov_car", lo=380, hi=720) / 1000)
        new_reg = _stable_int(k, "ov_nr2", lo=0, hi=40)
        active_dev = _stable_int(k, "ov_ad", lo=0, hi=max(1, total_dev // 8))
        act_rate = round(active_dev / total_dev, 2) if total_dev > 0 else 0.0
        new_act = _stable_int(k, "ov_na", lo=0, hi=max(1, new_reg + 1))
        r1 = _stable_int(k, "ov_r1", lo=0, hi=max(1, active_dev))
        r1_rate = round(r1 / max(active_dev, 1), 2)
        r3 = _stable_int(k, "ov_r3", lo=0, hi=max(1, r1))
        r3_rate = round(r3 / max(active_dev, 1), 2)
        r7 = _stable_int(k, "ov_r7", lo=0, hi=max(1, r3))
        r7_rate = round(r7 / max(active_dev, 1), 2)
        cum_rnd = _stable_int(k, "ov_cr", lo=800, hi=40000)
        daily_rnd = _stable_int(k, "ov_dr", lo=50, hi=2000)
        avg_rnd2 = round(daily_rnd / max(active_dev, 1), 2)
        rows.append({
            "app_id": app_id, "app_name": app_name,
            "设备总量": total_dev, "激活总量": cum_act,
            "新增注册": new_reg, "活跃设备": active_dev, "活跃率": act_rate,
            "新增活跃": new_act,
            "次留量": r1, "次留率": r1_rate,
            "三留量": r3, "三留率": r3_rate,
            "七留量": r7, "七留率": r7_rate,
            "累计轮次": cum_rnd, "对话轮次": daily_rnd, "平均轮次": avg_rnd2,
        })
    df = pd.DataFrame(rows)
    totals = {
        "app_id": "–", "app_name": "合计",
        "设备总量": df["设备总量"].sum(), "激活总量": df["激活总量"].sum(),
        "新增注册": df["新增注册"].sum(),
        "活跃设备": df["活跃设备"].sum(),
        "活跃率": round(df["活跃设备"].sum() / max(df["设备总量"].sum(), 1), 2),
        "新增活跃": df["新增活跃"].sum(),
        "次留量": df["次留量"].sum(),
        "次留率": round(df["次留量"].sum() / max(df["活跃设备"].sum(), 1), 2),
        "三留量": df["三留量"].sum(),
        "三留率": round(df["三留量"].sum() / max(df["活跃设备"].sum(), 1), 2),
        "七留量": df["七留量"].sum(),
        "七留率": round(df["七留量"].sum() / max(df["活跃设备"].sum(), 1), 2),
        "累计轮次": df["累计轮次"].sum(), "对话轮次": df["对话轮次"].sum(),
        "平均轮次": round(df["对话轮次"].sum() / max(df["活跃设备"].sum(), 1), 2),
    }
    return pd.concat([pd.DataFrame([totals]), df], ignore_index=True)


def _ov_line_chart(frame, y_field, y_title, tooltip_fields, color="#2563eb", height=130):
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


# ── 家群分析 render ────────────────────────────────────────────────────────────
def render_overview():
    c1, c2, _ = st.columns([2, 2, 4])
    with c1:
        app_opts = ["全部"] + [e[1] for e in ENTERPRISES]
        sel_app = st.selectbox("app_id", options=app_opts, index=0, key="ov_app")
    with c2:
        sel_dt = st.date_input("选择日期 (dt)", value=dt.date(2026, 6, 4), key="ov_dt")

    end_date = sel_dt
    ts = gen_overview_ts(end_date, n_days=30)

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
                st.altair_chart(
                    _ov_line_chart(ts, "new_reg", "单日新增注册设备量", tip),
                    use_container_width=True,
                )

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
                st.altair_chart(
                    _ov_line_chart(ts, "active", "单日活跃设备量", tip, color="#16a34a"),
                    use_container_width=True,
                )

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
                st.altair_chart(
                    _ov_line_chart(ts, "avg_rounds", "单日设备平均轮次", tip, color="#ea580c"),
                    use_container_width=True,
                )

    tbl = gen_overview_table(end_date)
    if sel_app != "全部":
        tbl = tbl[(tbl["app_id"] == sel_app) | (tbl["app_id"] == "–")]

    st.markdown('<div class="section-title">今日活跃app</div>', unsafe_allow_html=True)
    st.dataframe(
        tbl,
        use_container_width=True,
        hide_index=True,
        column_config={
            "app_id": st.column_config.TextColumn("app_id"),
            "活跃率": st.column_config.NumberColumn(format="%.2f"),
            "次留率": st.column_config.NumberColumn(format="%.2f"),
            "三留率": st.column_config.NumberColumn(format="%.2f"),
            "七留率": st.column_config.NumberColumn(format="%.2f"),
            "平均轮次": st.column_config.NumberColumn(format="%.2f"),
            "累计轮次": st.column_config.NumberColumn(format="%d"),
            "对话轮次": st.column_config.NumberColumn(format="%d"),
        },
    )
    st.download_button(
        "⬇ 导出今日活跃app CSV",
        data=tbl.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"overview_{sel_dt}.csv",
        mime="text/csv",
        key="dl_ov",
    )


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
    tab_bot, tab_ov, tab_jz = st.tabs(["Bot单日明细", "家群分析", "京造产品销量"])

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

    with tab_ov:
        render_overview()

    with tab_jz:
        jz_c1, jz_c2, _ = st.columns([2, 3, 3])
        with jz_c1:
            jz_dt = st.date_input("选择日期 (dt)", value=dt.date(2026, 6, 2), key="jz_dt")
        with jz_c2:
            jz_app_options = ["全部"] + [e[2] for e in JINGZAO_APPS]
            jz_sel_app = st.selectbox("选择应用", options=jz_app_options, key="jz_app")

        jz_df = gen_jingzao_sales(jz_dt, jz_dt)
        if jz_sel_app != "全部":
            jz_df = jz_df[jz_df["应用名称"] == jz_sel_app].reset_index(drop=True)

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
            file_name=f"module_2_jingzao_sales_{jz_dt}.csv",
            mime="text/csv",
            key="dl_jz",
        )
