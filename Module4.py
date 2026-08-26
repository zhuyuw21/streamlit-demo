"""
Module 4 — 周新增注册设备量变化 Top 产品
Embedded via render() in app.py
"""

import datetime as dt
import hashlib
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt


# ── Mock product pool ──────────────────────────────────────────────────────────
PRODUCTS = [
    (11366, "11366_小鸡球球8711"),
    (11691, "11691_ROSELINK-TEST"),
    (10057, "10057_芙崽"),
    (10231, "10231_豆包学习机"),
    (11402, "11402_悟空识字"),
    (10988, "10988_小度学习伴侣"),
    (11055, "11055_叫叫阅读"),
    (10774, "10774_凯叔讲故事"),
    (11810, "11810_火火兔"),
    (10346, "10346_洪恩识字"),
    (11523, "11523_伴鱼绘本"),
    (10692, "10692_多纳学英语"),
    (11279, "11279_宝宝巴士"),
    (10118, "10118_叽里呱啦"),
    (11934, "11934_斑马 AI"),
]


def _stable_int(*parts, lo, hi):
    """Deterministic pseudo-random int from string parts, for reproducible mock data."""
    h = hashlib.md5("_".join(str(p) for p in parts).encode()).hexdigest()
    return lo + int(h[:8], 16) % (hi - lo + 1)


@st.cache_data
def gen_top_products(week_end: dt.date) -> pd.DataFrame:
    key = week_end.isoformat()
    rows =[]
    for app_id, app_name in PRODUCTS:
        # 本周 / 上周 / 上上周 三个 7 天窗口的新增注册设备量
        this_week = _stable_int(key, app_id, "w0", lo=0, hi=45000)
        last_week = _stable_int(key, app_id, "w1", lo=0, hi=40000)
        prev_week = _stable_int(key, app_id, "w2", lo=0, hi=38000)
        rows.append({
            "app_id": app_id,
            "app_name": app_name,
            "this_week": this_week,
            "last_week": last_week,
            "prev_week": prev_week,
        })
    df = pd.DataFrame(rows)
    df["delta_abs"] = df["this_week"] - df["last_week"]
    df["delta_pct"] = np.where(
        df["last_week"] == 0,
        np.nan,
        (df["this_week"] - df["last_week"]) / df["last_week"] * 100,
    )
    return df


def _week_label(start, end):
    return f"{start.month}月{start.day}日~{end.month}月{end.day}日"


def _fmt_int(x):
    return f"{int(x):,}"


def _fmt_delta(x):
    sign = "+" if x >= 0 else ""
    cls = "up" if x >= 0 else "down"
    return f'<span class="{cls}">{sign}{int(x):,}</span>'


def _fmt_delta_pct(x):
    if pd.isna(x):
        return '<span class="up">—</span>'
    sign = "+" if x >= 0 else ""
    cls = "up" if x >= 0 else "down"
    return f'<span class="{cls}">{sign}{x:.1f}%</span>'


def render():
    st.markdown(
        '<div class="section-title">周新增注册设备量变化 Top 产品</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([2, 2, 4])
    with c1:
        week_end = st.date_input(
            "本周结束日",
            value=dt.date(2026, 8, 25),
            help="以该日为本周最后一天，向前推 3 个 7 天窗口作对比",
            key="m4_week_end",
        )
    with c2:
        order = st.radio(
            "排序",
            ["降序", "升序"],
            horizontal=True,
            key="m4_order",
        )

    # 三个 7 天窗口区间
    w0_end = week_end
    w0_start = w0_end - dt.timedelta(days=6)
    w1_end = w0_start - dt.timedelta(days=1)
    w1_start = w1_end - dt.timedelta(days=6)
    w2_end = w1_start - dt.timedelta(days=1)
    w2_start = w2_end - dt.timedelta(days=6)

    hdr_w0 = f"{_week_label(w0_start, w0_end)}（本周）"
    hdr_w1 = f"{_week_label(w1_start, w1_end)}（上周）"
    hdr_w2 = f"{_week_label(w2_start, w2_end)}（上上周）"

    df = gen_top_products(week_end).copy()
    df = df.sort_values("delta_abs", ascending=(order == "升序")).head(10)

    columns = [
        "app_id", "app_name", hdr_w0, hdr_w1, hdr_w2,
        "环比增量（绝对Δ）", "环比增量%（百分比Δ）",
    ]
    thead = (
        f"<th class='left'>app_id</th>"
        f"<th class='left'>app_name</th>"
        f"<th>{hdr_w0}</th><th>{hdr_w1}</th><th>{hdr_w2}</th>"
        f"<th>环比增量（绝对Δ）</th><th>环比增量%（百分比Δ）</th>"
    )
    body = []
    for _, r in df.iterrows():
        body.append(
            "<tr>"
            f"<td class='metric'>{r['app_id']}</td>"
            f"<td class='metric'>{r['app_name']}</td>"
            f"<td>{_fmt_int(r['this_week'])}</td>"
            f"<td>{_fmt_int(r['last_week'])}</td>"
            f"<td>{_fmt_int(r['prev_week'])}</td>"
            f"<td>{_fmt_delta(r['delta_abs'])}</td>"
            f"<td>{_fmt_delta_pct(r['delta_pct'])}</td>"
            "</tr>"
        )

    html = (
        '<table class="wk-table">'
        f"<thead><tr>{thead}</tr></thead>"
        f'<tbody>{"".join(body)}</tbody>'
        "</table>"
    )
    st.markdown(html, unsafe_allow_html=True)

    export_df = pd.DataFrame({
        "app_id": df["app_id"],
        "app_name": df["app_name"],
        hdr_w0: df["this_week"],
        hdr_w1: df["last_week"],
        hdr_w2: df["prev_week"],
        "环比增量（绝对Δ）": df["delta_abs"],
        "环比增量%（百分比Δ）": df["delta_pct"].round(1),
    })
    st.download_button(
        "⬇ 导出 CSV",
        data=export_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"module_4_top_products_{week_end}.csv",
        mime="text/csv",
    )

    render_dau_ranking()


# ── 全产品 DAU 排行表 ───────────────────────────────────────────────────────────
COMPANIES = [
    "北京字节跳动科技有限公司",
    "深圳市腾讯计算机系统有限公司",
    "广州小鸡快跑网络科技有限公司",
    "杭州网易雷火科技有限公司",
    "上海米哈游网络科技股份有限公司",
    "北京猿力教育科技有限公司",
    "深圳市洪恩教育科技有限公司",
    "北京凯叔讲故事科技有限公司",
    "上海企鹅童话文化传播有限公司",
    "广州趣丸网络科技有限公司",
]


def _company_of(app_id):
    return COMPANIES[app_id % len(COMPANIES)]


@st.cache_data
def gen_dau_ranking(ref_day: dt.date) -> pd.DataFrame:
    key = ref_day.isoformat()
    rows = []
    for app_id, app_name in PRODUCTS:
        dau = _stable_int(key, app_id, "dau", lo=200, hi=52000)
        new_reg_d = _stable_int(key, app_id, "nrd", lo=0, hi=6000)
        new_reg_7d = _stable_int(key, app_id, "nr7", lo=new_reg_d, hi=new_reg_d * 7 + 1)
        new_act_d = int(new_reg_d * _stable_int(key, app_id, "ar", lo=55, hi=72) / 100)
        new_act_7d = int(new_reg_7d * _stable_int(key, app_id, "ar7", lo=55, hi=72) / 100)
        active_7d = _stable_int(key, app_id, "a7", lo=dau, hi=dau * 4 + 1)
        avg_active_days = round(_stable_int(key, app_id, "aad", lo=110, hi=700) / 100, 2)
        rows.append({
            "app_id": app_id,
            "app_name": app_name,
            "company": _company_of(app_id),
            "dau": dau,
            "new_reg_d": new_reg_d,
            "new_reg_7d": new_reg_7d,
            "new_act_d": new_act_d,
            "new_act_7d": new_act_7d,
            "active_7d": active_7d,
            "avg_active_days": avg_active_days,
        })
    return pd.DataFrame(rows)


def render_dau_ranking():
    st.markdown(
        '<div class="section-title">全产品 DAU 排行表</div>',
        unsafe_allow_html=True,
    )

    c1, _ = st.columns([2, 6])
    with c1:
        ref_day = st.date_input(
            "统计日期",
            value=dt.date(2026, 8, 25),
            help="以该日为“当日”，并统计其近 7 天数据",
            key="m4_dau_day",
        )

    df = gen_dau_ranking(ref_day).copy()
    df = df.sort_values("dau", ascending=False).head(10)

    thead = (
        "<th class='left'>app_id</th>"
        "<th class='left'>app_name</th>"
        "<th class='left'>企业名称</th>"
        "<th>当日活跃设备量</th>"
        "<th>当日新增注册设备量</th>"
        "<th>近7天新增注册设备量</th>"
        "<th>当日新增激活设备量</th>"
        "<th>近7天新增激活设备量</th>"
        "<th>近7天活跃设备量</th>"
        "<th>近7天设备平均活跃天数</th>"
    )
    body = []
    for _, r in df.iterrows():
        body.append(
            "<tr>"
            f"<td class='metric'>{r['app_id']}</td>"
            f"<td class='metric'>{r['app_name']}</td>"
            f"<td class='metric'>{r['company']}</td>"
            f"<td>{_fmt_int(r['dau'])}</td>"
            f"<td>{_fmt_int(r['new_reg_d'])}</td>"
            f"<td>{_fmt_int(r['new_reg_7d'])}</td>"
            f"<td>{_fmt_int(r['new_act_d'])}</td>"
            f"<td>{_fmt_int(r['new_act_7d'])}</td>"
            f"<td>{_fmt_int(r['active_7d'])}</td>"
            f"<td>{r['avg_active_days']:.2f}</td>"
            "</tr>"
        )

    html = (
        '<table class="wk-table">'
        f"<thead><tr>{thead}</tr></thead>"
        f'<tbody>{"".join(body)}</tbody>'
        "</table>"
    )
    st.markdown(html, unsafe_allow_html=True)

    export_df = pd.DataFrame({
        "app_id": df["app_id"],
        "app_name": df["app_name"],
        "企业名称": df["company"],
        "当日活跃设备量": df["dau"],
        "当日新增注册设备量": df["new_reg_d"],
        "近7天新增注册设备量": df["new_reg_7d"],
        "当日新增激活设备量": df["new_act_d"],
        "近7天新增激活设备量": df["new_act_7d"],
        "近7天活跃设备量": df["active_7d"],
        "近7天设备平均活跃天数": df["avg_active_days"],
    })
    st.download_button(
        "⬇ 导出 CSV",
        data=export_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"module_4_dau_ranking_{ref_day}.csv",
        mime="text/csv",
        key="m4_dau_dl",
    )

    render_retention_heatmap()


# ── 新增设备留存热力图 ──────────────────────────────────────────────────────────
def _sf(*parts, lo, hi, nd=2):
    h = hashlib.md5("_".join(str(p) for p in parts).encode()).hexdigest()
    frac = int(h[8:16], 16) / 0xFFFFFFFF
    return round(lo + frac * (hi - lo), nd)


_HM_DAYS = [0, 1, 2, 3, 4, 5, 6, 7, 14, 30]
_HM_LABELS = ["当天(Day 0)", "第1天", "第2天", "第3天", "第4天",
          "第5天", "第6天", "第7天", "第14天", "第30天"]
_HM_RANGES = {
    1: (28.0, 52.0), 2: (22.0, 42.0), 3: (17.0, 35.0),
    4: (13.0, 30.0), 5: (10.0, 25.0), 6: (8.0, 22.0),
    7: (7.0, 20.0), 14: (4.0, 14.0), 30: (3.0, 8.0),
}


@st.cache_data
def gen_retention_heatmap(start: dt.date, end: dt.date, today: dt.date) -> pd.DataFrame:
    rows = []
    for i in range(max((end - start).days + 1, 1)):
        d = start + dt.timedelta(days=i)
        base = _stable_int(d.isoformat(), "hm_base", lo=1200, hi=5000)
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


def render_retention_heatmap():
    st.markdown(
        '<div class="section-title">新增设备留存热力图</div>',
        unsafe_allow_html=True,
    )

    today = dt.date.today()
    hm_range = st.date_input(
        "时间范围",
        value=(today - dt.timedelta(days=30), today),
        key="m4_hm_range",
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
                axis=alt.Axis(labelAngle=0, labelColor="#8b95a5", titleColor="#8b95a5")),
        y=alt.Y("注册日期:N", sort=date_order, title="新增注册日期",
                axis=alt.Axis(labelColor="#8b95a5", titleColor="#8b95a5")),
        color=alt.Color("rate:Q",
                        scale=alt.Scale(scheme="teals", domain=[0, 100]),
                        legend=alt.Legend(title="留存率(%)", gradientLength=200,
                                          labelColor="#8b95a5", titleColor="#8b95a5")),
    )
    text_lyr = alt.Chart(hm_df).mark_text(fontSize=9).encode(
        x=alt.X("day_label:N", sort=_HM_LABELS),
        y=alt.Y("注册日期:N", sort=date_order),
        text=alt.Text("label:N"),
        color=alt.condition(
            alt.datum.rate > 45,
            alt.value("white"),
            alt.value("#cbd5e1"),
        ),
    )
    hm_chart = (rect + text_lyr).properties(
        height=max(300, n_rows * 26)
    ).configure_view(strokeWidth=0)
    st.altair_chart(hm_chart, use_container_width=True)

    render_product_summary()


# ── 分产品统计汇总 ──────────────────────────────────────────────────────────────
@st.cache_data
def gen_product_summary(ref_day: dt.date) -> pd.DataFrame:
    key = ref_day.isoformat()
    rows = []
    for app_id, app_name in PRODUCTS:
        new_reg = _stable_int(key, app_id, "ps_nr", lo=0, hi=6000)
        cum_reg = _stable_int(key, app_id, "ps_cr", lo=new_reg * 30 + 1000, hi=new_reg * 120 + 200000)
        new_act = int(new_reg * _stable_int(key, app_id, "ps_ar", lo=55, hi=75) / 100)
        cum_act = int(cum_reg * _stable_int(key, app_id, "ps_car", lo=60, hi=82) / 100)
        act_rate = round(cum_act / cum_reg * 100, 2) if cum_reg else 0.0
        dau = _stable_int(key, app_id, "ps_dau", lo=200, hi=52000)
        retn_1d = _sf(key, app_id, "ps_r1", lo=28.0, hi=52.0, nd=1)
        retn_3d = _sf(key, app_id, "ps_r3", lo=17.0, hi=35.0, nd=1)
        retn_7d = _sf(key, app_id, "ps_r7", lo=7.0, hi=20.0, nd=1)
        active_rate = _sf(key, app_id, "ps_act", lo=8.0, hi=45.0, nd=1)
        avg_rounds = round(_stable_int(key, app_id, "ps_ar2", lo=200, hi=1500) / 100, 2)
        avg_dur = round(_stable_int(key, app_id, "ps_dur", lo=120, hi=1800) / 100, 2)
        rows.append({
            "app_id": app_id,
            "app_name": app_name,
            "company": _company_of(app_id),
            "new_reg": new_reg,
            "cum_reg": cum_reg,
            "new_act": new_act,
            "cum_act": cum_act,
            "act_rate": act_rate,
            "dau": dau,
            "retn_1d": retn_1d,
            "retn_3d": retn_3d,
            "retn_7d": retn_7d,
            "active_rate": active_rate,
            "avg_rounds": avg_rounds,
            "avg_dur": avg_dur,
        })
    return pd.DataFrame(rows)


def render_product_summary():
    st.markdown(
        '<div class="section-title">分产品统计汇总</div>',
        unsafe_allow_html=True,
    )

    ref_day = dt.date(2026, 8, 25)

    df = gen_product_summary(ref_day).copy()
    df = df.sort_values("new_reg", ascending=False).head(10)

    thead = (
        "<th class='left'>app_id</th>"
        "<th class='left'>app_name</th>"
        "<th class='left'>企业名称</th>"
        "<th>新增注册设备量</th>"
        "<th>累计注册设备量</th>"
        "<th>新增激活设备量</th>"
        "<th>累计激活设备量</th>"
        "<th>激活率</th>"
        "<th>日均DAU</th>"
        "<th>次日留存率</th>"
        "<th>3日留存率</th>"
        "<th>7日留存率</th>"
        "<th>活跃率</th>"
        "<th>设备平均对话轮次</th>"
        "<th>设备平均对话时长</th>"
    )
    body = []
    for _, r in df.iterrows():
        body.append(
            "<tr>"
            f"<td class='metric'>{r['app_id']}</td>"
            f"<td class='metric'>{r['app_name']}</td>"
            f"<td class='metric'>{r['company']}</td>"
            f"<td>{_fmt_int(r['new_reg'])}</td>"
            f"<td>{_fmt_int(r['cum_reg'])}</td>"
            f"<td>{_fmt_int(r['new_act'])}</td>"
            f"<td>{_fmt_int(r['cum_act'])}</td>"
            f"<td>{r['act_rate']:.2f}%</td>"
            f"<td>{_fmt_int(r['dau'])}</td>"
            f"<td>{r['retn_1d']:.1f}%</td>"
            f"<td>{r['retn_3d']:.1f}%</td>"
            f"<td>{r['retn_7d']:.1f}%</td>"
            f"<td>{r['active_rate']:.1f}%</td>"
            f"<td>{r['avg_rounds']:.2f}</td>"
            f"<td>{r['avg_dur']:.2f}</td>"
            "</tr>"
        )

    html = (
        '<table class="wk-table">'
        f"<thead><tr>{thead}</tr></thead>"
        f'<tbody>{"".join(body)}</tbody>'
        "</table>"
    )
    st.markdown(html, unsafe_allow_html=True)

    export_df = pd.DataFrame({
        "app_id": df["app_id"],
        "app_name": df["app_name"],
        "企业名称": df["company"],
        "新增注册设备量": df["new_reg"],
        "累计注册设备量": df["cum_reg"],
        "新增激活设备量": df["new_act"],
        "累计激活设备量": df["cum_act"],
        "激活率": df["act_rate"],
        "日均DAU": df["dau"],
        "次日留存率": df["retn_1d"],
        "3日留存率": df["retn_3d"],
        "7日留存率": df["retn_7d"],
        "活跃率": df["active_rate"],
        "设备平均对话轮次": df["avg_rounds"],
        "设备平均对话时长": df["avg_dur"],
    })
    st.download_button(
        "⬇ 导出 CSV",
        data=export_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"module_4_product_summary_{ref_day}.csv",
        mime="text/csv",
        key="m4_ps_dl",
    )