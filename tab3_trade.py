"""
STIR Terminal — Tab 3: Trade Builder
Supports: Outright · Spread · Fly · Condor · Defly
Outputs: DV01 · PnL/bp · Scenario PnL table + chart
"""
from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import date
from typing import Dict, List, Optional

from ui.styles import bb_section, bb_subsection, build_table
from ui.tab2_structures import compute_prices_for_cases
from config.constants import CONTRACT_SPECS

# ─────────────────────────────────────────────────────────────────────────────
# DV01 helpers
# ─────────────────────────────────────────────────────────────────────────────

_DV01 = {"SR1": 41.67, "ZQ": 41.67, "SR3": 25.00}

_TRADE_WEIGHTS = {
    "Outright": [1],
    "Spread":   [1, -1],           # back - front (+1 back, -1 front)
    "Fly":      [1, -2, 1],        # front - 2×mid + back
    "Condor":   [1, -1, -1, 1],   # front - mid1 - mid2 + back
    "Defly":    [1, -3, 3, -1],   # front - 3×m1 + 3×m2 - back
}

_COLORS = [
    "#FF8C00", "#00FF41", "#00BFFF", "#FF69B4",
    "#FFD700", "#7FFF00", "#FF6347", "#40E0D0",
]


def dv01_for_trade(product: str, trade_type: str, lots: int) -> float:
    """Net DV01 in $ for the structure (directional, using abs weights sum)."""
    weights = _TRADE_WEIGHTS.get(trade_type, [1])
    dv01_per = _DV01.get(product, 41.67)
    # For structures, DV01 is per front leg × lots (net long)
    return abs(weights[0]) * dv01_per * lots


def pnl_per_bp(product: str, trade_type: str, lots: int) -> float:
    return dv01_for_trade(product, trade_type, lots)


# ─────────────────────────────────────────────────────────────────────────────
# Base price (flat rate — no cuts)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def _base_prices_cached(
    base_sofr: float, base_effr: float,
    sr1_meta: tuple, zq_meta: tuple, sr3_meta: tuple,
) -> dict:
    from core.pricing_engine import price_sr1, price_zq, price_sr3
    sr1 = {c: price_sr1(y, m, {}, base_sofr) for c, y, m in sr1_meta}
    zq  = {c: price_zq(y, m, {}, base_effr)  for c, y, m in zq_meta}
    sr3 = {c: price_sr3(
               date.fromisoformat(rs), date.fromisoformat(re), {}, base_sofr
           ) for c, rs, re in sr3_meta}
    return {"SR1": sr1, "ZQ": zq, "SR3": sr3}


def get_base_prices(sr1_c, zq_c, sr3_c, base_sofr, base_effr) -> dict:
    sr1_meta = tuple((c["code"], c["year"], c["month"]) for c in sr1_c)
    zq_meta  = tuple((c["code"], c["year"], c["month"]) for c in zq_c)
    sr3_meta = tuple((c["code"], c["ref_start"].isoformat(), c["ref_end"].isoformat())
                     for c in sr3_c)
    return _base_prices_cached(base_sofr, base_effr, sr1_meta, zq_meta, sr3_meta)


# ─────────────────────────────────────────────────────────────────────────────
# Structure price: sum over legs
# ─────────────────────────────────────────────────────────────────────────────

def structure_price(
    trade_type: str,
    product:    str,
    leg_codes:  List[str],
    prices:     Dict[str, float],
) -> Optional[float]:
    weights = _TRADE_WEIGHTS.get(trade_type, [1])
    if len(leg_codes) != len(weights):
        return None
    total = 0.0
    for code, w in zip(leg_codes, weights):
        px = prices.get(code)
        if px is None:
            return None
        total += w * px
    return round(total, 6)


# ─────────────────────────────────────────────────────────────────────────────
# Leg selector
# ─────────────────────────────────────────────────────────────────────────────

def _leg_selector(
    product:    str,
    trade_type: str,
    sr1_c: list, zq_c: list, sr3_c: list,
    key_pfx: str,
) -> List[str]:
    """Return list of selected contract codes (one per leg)."""
    if product == "SR1":
        contracts = sr1_c
    elif product == "ZQ":
        contracts = zq_c
    else:
        contracts = sr3_c

    options = [c["code"] for c in contracts]
    n_legs  = len(_TRADE_WEIGHTS.get(trade_type, [1]))
    labels  = {
        "Outright": ["Leg"],
        "Spread":   ["Front (−1)", "Back (+1)"],
        "Fly":      ["Front (+1)", "Mid (−2)", "Back (+1)"],
        "Condor":   ["Leg 1 (+1)", "Leg 2 (−1)", "Leg 3 (−1)", "Leg 4 (+1)"],
        "Defly":    ["Leg 1 (+1)", "Leg 2 (−3)", "Leg 3 (+3)", "Leg 4 (−1)"],
    }

    leg_labels = labels.get(trade_type, [f"Leg {i+1}" for i in range(n_legs)])
    codes = []
    cols  = st.columns(n_legs)
    for i, (col, lbl) in enumerate(zip(cols, leg_labels)):
        with col:
            default_idx = min(i, len(options) - 1)
            sel = st.selectbox(lbl, options, index=default_idx, key=f"{key_pfx}_leg{i}")
            codes.append(sel)
    return codes


# ─────────────────────────────────────────────────────────────────────────────
# Scenario PnL chart
# ─────────────────────────────────────────────────────────────────────────────

def _pnl_chart(
    case_names: List[str],
    pnl_values: List[float],
    trade_label: str,
) -> go.Figure:
    colors = [("#00FF41" if v > 0 else "#FF3131") for v in pnl_values]

    fig = go.Figure(go.Bar(
        x=case_names,
        y=pnl_values,
        marker=dict(color=colors, line=dict(color="#333", width=0.5)),
        hovertemplate="<b>%{x}</b><br>PnL: $%{y:,.0f}<extra></extra>",
        name="PnL ($)",
    ))
    fig.add_hline(y=0, line_color="#2A2A2A", line_width=1)
    fig.update_layout(
        paper_bgcolor="#000", plot_bgcolor="#000",
        font=dict(family="IBM Plex Mono, Courier New", color="#C0C0C0", size=10),
        title=dict(text=f"SCENARIO PnL — {trade_label}",
                   font=dict(color="#FF8C00", size=11), x=0),
        xaxis=dict(tickfont=dict(color="#FF6600", size=9), gridcolor="#111",
                   tickangle=-40),
        yaxis=dict(tickfont=dict(color="#FF6600", size=9), gridcolor="#111",
                   zeroline=True, zerolinecolor="#2A2A2A",
                   title=dict(text="PnL ($)", font=dict(color="#FF8C00", size=10))),
        margin=dict(l=60, r=12, t=40, b=80),
        height=300,
        showlegend=False,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────────────────────────────────────

def render_tab_trade(cm, sr1_c, zq_c, sr3_c, base_sofr, base_effr):
    bb_section("🧾 TRADE BUILDER")

    if not cm.cases:
        st.info("Add scenario cases in the sidebar to analyse trade PnL.")

    left, right = st.columns([1, 2])

    # ── LEFT: Trade inputs ────────────────────────────────────────────────────
    with left:
        bb_subsection("TRADE SETUP")

        product    = st.selectbox("Product", ["SR1", "ZQ", "SR3"], key="tb_product")
        trade_type = st.selectbox("Trade Type",
                                  ["Outright", "Spread", "Fly", "Condor", "Defly"],
                                  key="tb_type")
        direction  = st.radio("Direction", ["Buy", "Sell"], horizontal=True, key="tb_dir")
        lots       = st.number_input("Lots", min_value=1, max_value=10000,
                                     value=100, step=10, key="tb_lots")

        st.markdown("<hr style='border-color:#1A1A1A;margin:4px 0;'>", unsafe_allow_html=True)
        bb_subsection(f"LEGS — {trade_type}")
        leg_codes = _leg_selector(product, trade_type, sr1_c, zq_c, sr3_c, "tb")

        dir_sign = 1 if direction == "Buy" else -1
        dv01_val = dv01_for_trade(product, trade_type, lots)
        pnl_bp   = pnl_per_bp(product, trade_type, lots)

        st.markdown("<hr style='border-color:#1A1A1A;margin:4px 0;'>", unsafe_allow_html=True)
        bb_subsection("RISK METRICS")

        base_px = get_base_prices(sr1_c, zq_c, sr3_c, base_sofr, base_effr)
        base_struct = structure_price(
            trade_type, product, leg_codes,
            base_px.get(product, {})
        )

        m1, m2 = st.columns(2)
        with m1:
            st.metric("DV01 / lot", f"${_DV01[product]:.2f}")
            st.metric("PnL / bp", f"${pnl_bp:,.2f}")
        with m2:
            st.metric(f"Total DV01 ({lots}L)", f"${dv01_val * lots / lots * lots:,.0f}")
            if base_struct is not None:
                st.metric("Base Price", f"{base_struct:.4f}")
            else:
                st.metric("Base Price", "N/A")

        # Trade label for chart
        weights_str = "/".join(
            f"{'+' if w>0 else ''}{w}{c}" for w, c in
            zip(_TRADE_WEIGHTS.get(trade_type, [1]), leg_codes)
        )
        trade_label = f"{direction} {lots}x {product} {trade_type} [{weights_str}]"

    # ── RIGHT: Scenario PnL ───────────────────────────────────────────────────
    with right:
        bb_subsection("SCENARIO PnL ANALYSIS")

        if not cm.cases:
            st.markdown("<div style='color:#444;padding:20px;'>No cases.</div>",
                        unsafe_allow_html=True)
        else:
            # Case selection for PnL
            all_labels = [f"{c['id']} | {c['name']}" for c in cm.cases]
            default    = all_labels[:min(8, len(all_labels))]
            pnl_labels = st.multiselect(
                "Cases for PnL", all_labels, default=default,
                key="tb_pnl_cases",
            )
            pnl_ids    = [s.split(" | ")[0] for s in pnl_labels]
            pnl_cases  = [c for c in cm.cases if c["id"] in pnl_ids]

            if pnl_cases:
                with st.spinner(f"Computing {len(pnl_cases)} scenarios…"):
                    scen_prices = compute_prices_for_cases(
                        pnl_cases, sr1_c, zq_c, sr3_c
                    )

                # Build PnL table
                rows, pnl_vals, case_names_list = [], [], []

                for case in pnl_cases:
                    scen_struct = structure_price(
                        trade_type, product, leg_codes,
                        scen_prices.get(case["id"], {}).get(product, {})
                    )
                    if base_struct is None or scen_struct is None:
                        continue

                    price_chg  = scen_struct - base_struct
                    # PnL in bps: price change × dv01 (price pts are bps for these contracts)
                    # 1 price pt = 100 bps, so bps = price_chg × 100
                    pnl_bps    = price_chg * 100.0
                    pnl_dollar = price_chg * dv01_val / (1/100) * dir_sign

                    # Actually: DV01 = $ per 1 bp. Price in points.
                    # 1 price pt = 100 bps → PnL = price_chg × 100 × DV01_per_bp × lots
                    pnl_dollar = price_chg * 100.0 * (_DV01[product]) * lots * dir_sign

                    rows.append({
                        "Case": f"{case['id']}|{case['name'][:14]}",
                        "Base Px": f"{base_struct:.4f}" if base_struct else "—",
                        "Scen Px": f"{scen_struct:.4f}",
                        "ΔPx": f"{price_chg:+.4f}",
                        "Δbps": f"{pnl_bps:+.2f}",
                        "PnL ($)": f"${pnl_dollar:,.0f}",
                    })
                    pnl_vals.append(pnl_dollar)
                    case_names_list.append(f"{case['id']}|{case['name'][:8]}")

                if rows:
                    df = pd.DataFrame(rows)
                    st.dataframe(
                        df, hide_index=True,
                        use_container_width=True,
                        height=min(400, 38 + 36 * len(rows)),
                        column_config={
                            "Case":    st.column_config.TextColumn("Case", width="medium"),
                            "Base Px": st.column_config.TextColumn("Base", width="small"),
                            "Scen Px": st.column_config.TextColumn("Scen", width="small"),
                            "ΔPx":     st.column_config.TextColumn("ΔPx",  width="small"),
                            "Δbps":    st.column_config.TextColumn("Δbps", width="small"),
                            "PnL ($)": st.column_config.TextColumn("PnL ($)", width="medium"),
                        },
                    )

                    # Summary metrics
                    mc1, mc2, mc3, mc4 = st.columns(4)
                    mc1.metric("Best PnL",  f"${max(pnl_vals):,.0f}")
                    mc2.metric("Worst PnL", f"${min(pnl_vals):,.0f}")
                    mc3.metric("Mean PnL",  f"${sum(pnl_vals)/len(pnl_vals):,.0f}")
                    mc4.metric("# Scenarios", len(pnl_vals))

                    # PnL chart
                    st.markdown("<hr style='border-color:#1A1A1A;margin:4px 0;'>", unsafe_allow_html=True)
                    fig = _pnl_chart(case_names_list, pnl_vals, trade_label)
                    st.plotly_chart(fig, use_container_width=True,
                                    config={"displayModeBar": False})
                else:
                    st.warning("Could not compute PnL — check leg selection.")

    # ── Bottom: Full trade label ──────────────────────────────────────────────
    st.markdown(
        f"<div style='color:#555;font-size:10px;padding:4px 8px;border-top:1px solid #1A1A1A;'>"
        f"TRADE: {trade_label}</div>",
        unsafe_allow_html=True,
    )
