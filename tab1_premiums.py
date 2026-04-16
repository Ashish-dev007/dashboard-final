"""
STIR Terminal — Tab 1: Meeting Premiums
Overlay chart: Market vs Scenario cases.
Charts: per-meeting cuts · cumulative cuts · implied rate path
Table: per-meeting cuts × cases
"""
from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import date
from typing import Dict, List

from config.fomc_dates import ALL_FOMC_MEETINGS
from ui.styles import bb_section, bb_subsection, build_table

# Bloomberg color palette for multiple cases
_CASE_COLORS = [
    "#FF8C00", "#00FF41", "#00BFFF", "#FF69B4",
    "#FFD700", "#7FFF00", "#FF6347", "#40E0D0",
    "#EE82EE", "#98FB98", "#FFA07A", "#87CEFA",
]
_MKT_COLOR = "#00BFFF"   # cyan = market data

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _plotly_base(height: int = 340) -> dict:
    return dict(
        paper_bgcolor="#000",
        plot_bgcolor="#000",
        font=dict(family="IBM Plex Mono, Courier New", color="#C0C0C0", size=10),
        margin=dict(l=52, r=16, t=36, b=70),
        height=height,
        legend=dict(
            bgcolor="#0D0800", bordercolor="#FF6600", borderwidth=1,
            font=dict(color="#C0C0C0", size=9), orientation="h",
            x=0, y=1.12,
        ),
        xaxis=dict(
            tickfont=dict(color="#FF6600", size=9),
            gridcolor="#111", showgrid=True,
            tickangle=-40,
        ),
        yaxis=dict(
            tickfont=dict(color="#FF6600", size=9),
            gridcolor="#111", showgrid=True,
            zeroline=True, zerolinecolor="#2A2A2A", zerolinewidth=1,
        ),
    )


def _build_meeting_series(
    cuts: Dict[date, float],
    all_meetings: list,
) -> tuple[list, list]:
    """
    Map a {effective_date: bps} dict to parallel (x_labels, y_values) using
    ALL_FOMC_MEETINGS ordering so all traces share the same x-axis.
    """
    xs, ys = [], []
    for m in all_meetings:
        eff = m["effective_date"]
        dec = m["decision_date"]
        sep = "⭐" if m["is_sep"] else ""
        xs.append(f"{dec.strftime('%b %d, %y')}{sep}")
        ys.append(cuts.get(eff, 0.0))
    return xs, ys


def _cumulative(ys: list) -> list:
    total, result = 0.0, []
    for y in ys:
        total += y
        result.append(round(total, 4))
    return result


def _implied_rate_path(
    base_rate: float,
    cuts: Dict[date, float],
    all_meetings: list,
) -> tuple[list, list]:
    """Build (x_labels, rate_levels) for the implied rate path."""
    xs, levels = [], []
    rate = base_rate
    for m in all_meetings:
        eff = m["effective_date"]
        dec = m["decision_date"]
        sep = "⭐" if m["is_sep"] else ""
        rate = round(rate + cuts.get(eff, 0.0) / 100.0, 6)
        xs.append(f"{dec.strftime('%b %d, %y')}{sep}")
        levels.append(rate)
    return xs, levels


# ─────────────────────────────────────────────────────────────────────────────
# Chart: Per-meeting cuts overlay
# ─────────────────────────────────────────────────────────────────────────────

def _chart_meeting_cuts(
    x_labels:      list,
    mkt_y:         list,
    case_data:     List[tuple],   # [(name, color, ys)]
    show_market:   bool,
    show_scenarios: bool,
) -> go.Figure:
    fig = go.Figure()

    if show_market:
        fig.add_trace(go.Bar(
            x=x_labels, y=mkt_y,
            name="Market",
            marker=dict(
                color=[_MKT_COLOR if v < -0.01 else ("#FF3131" if v > 0.01 else "#333")
                       for v in mkt_y],
                line=dict(color=_MKT_COLOR, width=0.5),
                opacity=0.7,
            ),
            hovertemplate="%{x}<br><b>Market: %{y:+.2f} bps</b><extra></extra>",
        ))

    if show_scenarios:
        for name, color, ys in case_data:
            fig.add_trace(go.Scatter(
                x=x_labels, y=ys,
                mode="lines+markers",
                name=name,
                line=dict(color=color, width=1.5),
                marker=dict(size=5, color=color),
                hovertemplate=f"%{{x}}<br><b>{name}: %{{y:+.2f}} bps</b><extra></extra>",
            ))

    fig.add_hline(y=0, line_color="#2A2A2A", line_width=1)
    fig.update_layout(
        **_plotly_base(320),
        title=dict(text="PER-MEETING CUTS / HIKES (bps)", font=dict(color="#FF8C00", size=11), x=0),
        barmode="overlay",
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Chart: Cumulative cuts
# ─────────────────────────────────────────────────────────────────────────────

def _chart_cumulative(
    x_labels:      list,
    mkt_y:         list,
    case_data:     List[tuple],
    show_market:   bool,
    show_scenarios: bool,
) -> go.Figure:
    fig = go.Figure()

    if show_market:
        mkt_cum = _cumulative(mkt_y)
        fig.add_trace(go.Scatter(
            x=x_labels, y=mkt_cum,
            mode="lines+markers",
            name="Market (cum.)",
            line=dict(color=_MKT_COLOR, width=2, dash="dot"),
            marker=dict(size=5, color=_MKT_COLOR, symbol="diamond"),
            fill="tozeroy",
            fillcolor="rgba(0,191,255,0.06)",
            hovertemplate="%{x}<br><b>Market: %{y:+.1f} bps cumulative</b><extra></extra>",
        ))

    if show_scenarios:
        for name, color, ys in case_data:
            cum = _cumulative(ys)
            fig.add_trace(go.Scatter(
                x=x_labels, y=cum,
                mode="lines+markers",
                name=name,
                line=dict(color=color, width=1.5),
                marker=dict(size=4, color=color),
                hovertemplate=f"%{{x}}<br><b>{name}: %{{y:+.1f}} bps cum.</b><extra></extra>",
            ))

    fig.add_hline(y=0, line_color="#2A2A2A", line_width=1)
    fig.update_layout(
        **_plotly_base(300),
        title=dict(text="CUMULATIVE CUTS (bps)", font=dict(color="#FF8C00", size=11), x=0),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Chart: Implied rate path
# ─────────────────────────────────────────────────────────────────────────────

def _chart_rate_path(
    x_labels:      list,
    base_sofr:     float,
    mkt_cuts:      Dict[date, float],
    case_list:     List[dict],        # raw cases
    all_meetings:  list,
    show_market:   bool,
    show_scenarios: bool,
) -> go.Figure:
    fig = go.Figure()

    if show_market:
        _, mkt_levels = _implied_rate_path(base_sofr, mkt_cuts, all_meetings)
        fig.add_trace(go.Scatter(
            x=x_labels, y=mkt_levels,
            mode="lines+markers",
            name="Market SOFR",
            line=dict(color=_MKT_COLOR, width=2, dash="dot"),
            marker=dict(size=5, color=_MKT_COLOR, symbol="diamond"),
            hovertemplate="%{x}<br><b>Market SOFR: %{y:.4f}%</b><extra></extra>",
        ))

    if show_scenarios:
        for i, case in enumerate(case_list):
            color = _CASE_COLORS[i % len(_CASE_COLORS)]
            _, levels = _implied_rate_path(
                case["base_sofr"], case["meeting_cuts"], all_meetings
            )
            fig.add_trace(go.Scatter(
                x=x_labels, y=levels,
                mode="lines+markers",
                name=case["name"],
                line=dict(color=color, width=1.5),
                marker=dict(size=4, color=color),
                hovertemplate=f"%{{x}}<br><b>{case['name']}: %{{y:.4f}}%</b><extra></extra>",
            ))

    # Base rate reference
    fig.add_hline(
        y=base_sofr, line_color="#FF6600", line_width=1, line_dash="dot",
        annotation_text=f"Base {base_sofr:.2f}%",
        annotation_font=dict(color="#FF6600", size=9),
    )

    fig.update_layout(
        **_plotly_base(300),
        title=dict(text="IMPLIED SOFR RATE PATH (%)", font=dict(color="#FF8C00", size=11), x=0),
        yaxis=dict(
            tickfont=dict(color="#FF6600", size=9),
            gridcolor="#111", showgrid=True,
            tickformat=".2f",
        ),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Meeting Summary Table
# ─────────────────────────────────────────────────────────────────────────────

def _meeting_table(
    all_meetings: list,
    mkt_cuts:     Dict[date, float],
    selected_cases: List[dict],
    show_market:  bool,
    show_scenarios: bool,
) -> str:
    """HTML table: rows = meetings, columns = Market + each case."""
    row_labels = []
    for m in all_meetings:
        d = m["decision_date"]
        sep = "⭐" if m["is_sep"] else ""
        off = "~" if not m["is_official"] else ""
        row_labels.append(f"{off}{d.strftime('%Y %b %d')}{sep}")

    col_labels = []
    col_types  = []
    if show_market:
        col_labels.append("MARKET")
        col_types.append("mkt")
    if show_scenarios:
        for c in selected_cases:
            col_labels.append(f"{c['id']}\n{c['name'][:10]}")
            col_types.append(None)

    data = []
    for m in all_meetings:
        eff = m["effective_date"]
        row = []
        if show_market:
            row.append(mkt_cuts.get(eff, 0.0))
        if show_scenarios:
            for c in selected_cases:
                row.append(c["meeting_cuts"].get(eff, 0.0))
        data.append(row)

    if not col_labels:
        return "<div style='color:#444;padding:8px;font-size:11px;'>No data selected.</div>"

    return build_table(row_labels, col_labels, data, fmt="{:+.2f}", col_types=col_types)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────────────────────────────────────

def render_tab_premiums(cm, sr1_c, zq_c, sr3_c, base_sofr, base_effr, market_cuts):
    bb_section("📊 MEETING PREMIUMS — Market vs Scenario Overlay")

    if not cm.cases and not any(v != 0 for v in market_cuts.values()):
        st.info("Add cases in the sidebar or enter market premiums to visualise.")

    # ── Controls row ─────────────────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3 = st.columns([2, 4, 2])
    with ctrl1:
        overlay = st.radio(
            "Show",
            ["Both", "Market Only", "Scenarios Only"],
            horizontal=False, key="overlay_mode",
        )
        show_mkt = overlay in ("Both", "Market Only")
        show_scn = overlay in ("Both", "Scenarios Only")

    with ctrl2:
        if cm.cases:
            all_labels = [f"{c['id']} | {c['name']}" for c in cm.cases]
            default    = all_labels[:min(6, len(all_labels))]
            selected_labels = st.multiselect(
                "Cases", all_labels, default=default, key="prem_cases",
                label_visibility="collapsed",
            )
            sel_ids    = [s.split(" | ")[0] for s in selected_labels]
            sel_cases  = [c for c in cm.cases if c["id"] in sel_ids]
        else:
            st.caption("No cases — add via sidebar")
            sel_cases = []

    with ctrl3:
        year_filter = st.multiselect(
            "Years", [2026, 2027, 2028, 2029, 2030],
            default=[2026, 2027], key="prem_years",
        )

    # ── Filter meetings by year ───────────────────────────────────────────────
    meetings = [
        m for m in ALL_FOMC_MEETINGS
        if m["decision_date"].year in year_filter
    ]
    if not meetings:
        st.warning("No meetings for selected years.")
        return

    x_labels, _ = _build_meeting_series({}, meetings)

    # Build per-case (name, color, ys) tuples
    case_series = []
    for i, c in enumerate(sel_cases):
        _, ys = _build_meeting_series(c["meeting_cuts"], meetings)
        case_series.append((
            f"{c['id']}|{c['name'][:10]}",
            _CASE_COLORS[i % len(_CASE_COLORS)],
            ys,
        ))

    _, mkt_ys = _build_meeting_series(market_cuts, meetings)

    # ── Chart 1: Per-meeting cuts ─────────────────────────────────────────────
    bb_subsection("Per-Meeting Cuts / Hikes (bps)")
    fig1 = _chart_meeting_cuts(x_labels, mkt_ys, case_series, show_mkt, show_scn)
    st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

    # ── Charts 2 & 3 side-by-side ────────────────────────────────────────────
    c_left, c_right = st.columns(2)
    with c_left:
        bb_subsection("Cumulative Cuts (bps)")
        fig2 = _chart_cumulative(x_labels, mkt_ys, case_series, show_mkt, show_scn)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    with c_right:
        bb_subsection("Implied Rate Path (%)")
        fig3 = _chart_rate_path(
            x_labels, base_sofr, market_cuts, sel_cases, meetings, show_mkt, show_scn
        )
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    # ── Meeting detail table ──────────────────────────────────────────────────
    bb_subsection("Per-Meeting Detail Table")
    tbl = _meeting_table(meetings, market_cuts, sel_cases, show_mkt, show_scn)
    st.markdown(tbl, unsafe_allow_html=True)

    # ── Range analysis (if multiple cases) ───────────────────────────────────
    if len(sel_cases) >= 2:
        with st.expander("📊 Cross-Case Range Analysis", expanded=False):
            analysis = cm.meeting_range_analysis()
            if analysis:
                _render_range_chart(analysis, meetings)


def _render_range_chart(analysis: list, meetings: list):
    """Mini range chart for selected meetings."""
    filtered = [
        a for a in analysis
        if any(a["effective_date"] == m["effective_date"] for m in meetings)
    ]
    if not filtered:
        return

    dates  = [a["decision_date"].strftime("%b %d, %y") for a in filtered]
    mins   = [a["min_cut"] for a in filtered]
    maxs   = [a["max_cut"] for a in filtered]
    means  = [a["mean_cut"] for a in filtered]

    fig = go.Figure()
    # range band
    fig.add_trace(go.Scatter(
        x=dates + dates[::-1], y=maxs + mins[::-1],
        fill="toself", fillcolor="rgba(255,100,0,0.1)",
        line=dict(color="rgba(0,0,0,0)"), name="Range", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=maxs, mode="lines", line=dict(color="#FF6600", width=1, dash="dot"),
        name="Max", hovertemplate="%{x}<br>Max: %{y:+.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=mins, mode="lines", line=dict(color="#FF3131", width=1, dash="dot"),
        name="Min", hovertemplate="%{x}<br>Min: %{y:+.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=means, mode="lines+markers",
        line=dict(color="#FFB347", width=2),
        marker=dict(size=5, color="#FFB347"),
        name="Mean", hovertemplate="%{x}<br>Mean: %{y:+.1f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_color="#2A2A2A", line_width=1)
    base_layout = dict(
        paper_bgcolor="#000", plot_bgcolor="#000",
        font=dict(family="IBM Plex Mono, Courier New", color="#C0C0C0", size=9),
        margin=dict(l=48, r=12, t=30, b=60),
        height=260,
        xaxis=dict(tickfont=dict(color="#FF6600", size=8), gridcolor="#111", tickangle=-40),
        yaxis=dict(tickfont=dict(color="#FF6600", size=8), gridcolor="#111",
                   zeroline=True, zerolinecolor="#2A2A2A"),
        legend=dict(bgcolor="#0D0800", bordercolor="#FF6600", borderwidth=1,
                    font=dict(color="#C0C0C0", size=8), orientation="h", x=0, y=1.12),
        title=dict(text="RANGE ACROSS CASES (bps)", font=dict(color="#FF8C00", size=10), x=0),
    )
    fig.update_layout(**base_layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
