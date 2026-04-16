"""
STIR Terminal — Tab 2: Structures
Sections: Outrights · Spreads · Butterflies · Condors · Deflys
All structures computed from Python pricing engine.
Columns = cases, rows = instruments.
"""
from __future__ import annotations
import streamlit as st
from datetime import date
from typing import Dict, List

from ui.styles import bb_section, bb_subsection, build_table

# ─────────────────────────────────────────────────────────────────────────────
# Caching: price computation per case
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def _compute_prices_cached(
    case_id: str,
    base_sofr: float,
    base_effr: float,
    sofr_path_items: tuple,   # tuple of (iso_date, float)
    effr_path_items: tuple,
    sr1_meta: tuple,          # ((code, year, month), ...)
    zq_meta:  tuple,
    sr3_meta: tuple,          # ((code, ref_start_iso, ref_end_iso), ...)
) -> dict:
    from core.pricing_engine import price_sr1, price_zq, price_sr3
    sofr = {date.fromisoformat(k): v for k, v in sofr_path_items}
    effr = {date.fromisoformat(k): v for k, v in effr_path_items}
    return {
        "SR1": {c: price_sr1(y, m, sofr, base_sofr) for c, y, m in sr1_meta},
        "ZQ":  {c: price_zq(y, m, effr, base_effr)  for c, y, m in zq_meta},
        "SR3": {c: price_sr3(
                    date.fromisoformat(rs), date.fromisoformat(re), sofr, base_sofr
                ) for c, rs, re in sr3_meta},
    }


def compute_prices_for_cases(
    cases: list,
    sr1_c: list, zq_c: list, sr3_c: list,
) -> Dict[str, dict]:
    sr1_meta = tuple((c["code"], c["year"], c["month"]) for c in sr1_c)
    zq_meta  = tuple((c["code"], c["year"], c["month"]) for c in zq_c)
    sr3_meta = tuple((c["code"], c["ref_start"].isoformat(), c["ref_end"].isoformat())
                     for c in sr3_c)
    out = {}
    for case in cases:
        sp = tuple((k.isoformat(), v) for k, v in case["rate_path"]["sofr"].items())
        ep = tuple((k.isoformat(), v) for k, v in case["rate_path"]["effr"].items())
        out[case["id"]] = _compute_prices_cached(
            case["id"], case["base_sofr"], case["base_effr"],
            sp, ep, sr1_meta, zq_meta, sr3_meta,
        )
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Table builders
# ─────────────────────────────────────────────────────────────────────────────

def _outright_table(contracts, cases, all_prices, product, fmt="{:.4f}") -> str:
    row_labels = [c["code"] for c in contracts]
    col_labels = [f"{c['id']}\n{c['name'][:9]}" for c in cases]
    data = [
        [all_prices.get(case["id"], {}).get(product, {}).get(cont["code"])
         for case in cases]
        for cont in contracts
    ]
    return build_table(row_labels, col_labels, data, fmt=fmt)


def _structure_table(
    gap_key: str,
    all_structs: Dict[str, dict],  # {case_id: {gap_key: {instrument: val}}}
    cases: list,
    fmt="{:.4f}",
) -> str:
    if not cases:
        return ""
    first_id = cases[0]["id"]
    keys = list(all_structs.get(first_id, {}).get(gap_key, {}).keys())
    if not keys:
        return "<div style='color:#444;font-size:11px;padding:6px;'>No structures for this tenor.</div>"
    col_labels = [f"{c['id']}\n{c['name'][:9]}" for c in cases]
    data = [
        [all_structs.get(c["id"], {}).get(gap_key, {}).get(k) for c in cases]
        for k in keys
    ]
    return build_table(keys, col_labels, data, fmt=fmt)


# ─────────────────────────────────────────────────────────────────────────────
# Section renderers
# ─────────────────────────────────────────────────────────────────────────────

def _render_outrights(cases, sr1_c, zq_c, sr3_c, all_prices):
    bb_subsection(f"OUTRIGHTS")
    t1, t2, t3 = st.tabs(["SR1 — 1M SOFR", "ZQ — 30D EFFR", "SR3 — 3M SOFR"])
    with t1:
        st.markdown(_outright_table(sr1_c, cases, all_prices, "SR1"), unsafe_allow_html=True)
    with t2:
        st.markdown(_outright_table(zq_c, cases, all_prices, "ZQ"), unsafe_allow_html=True)
    with t3:
        st.markdown(_outright_table(sr3_c, cases, all_prices, "SR3"), unsafe_allow_html=True)


def _render_spreads(cases, sr1_c, zq_c, sr3_c, all_prices):
    from core.structures import compute_spreads
    from config.constants import SR1_SPREAD_GAPS, ZQ_SPREAD_GAPS, SR3_SPREAD_GAPS

    sr1_s = {c["id"]: compute_spreads(sr1_c, all_prices.get(c["id"],{}).get("SR1",{}), SR1_SPREAD_GAPS)
             for c in cases}
    zq_s  = {c["id"]: compute_spreads(zq_c,  all_prices.get(c["id"],{}).get("ZQ", {}), ZQ_SPREAD_GAPS)
             for c in cases}
    sr3_s = {c["id"]: compute_spreads(sr3_c, all_prices.get(c["id"],{}).get("SR3",{}), SR3_SPREAD_GAPS)
             for c in cases}

    bb_subsection("SPREADS")
    t1, t2, t3 = st.tabs(["SR1 SPREADS", "ZQ SPREADS", "SR3 SPREADS"])

    with t1:
        for g in SR1_SPREAD_GAPS:
            k = f"{g}M"
            st.markdown(f"<div style='color:#FF6600;font-size:10px;margin:4px 0 2px;'>◾ {k} SPREAD</div>",
                        unsafe_allow_html=True)
            st.markdown(_structure_table(k, sr1_s, cases), unsafe_allow_html=True)

    with t2:
        for g in ZQ_SPREAD_GAPS:
            k = f"{g}M"
            st.markdown(f"<div style='color:#FF6600;font-size:10px;margin:4px 0 2px;'>◾ {k} SPREAD</div>",
                        unsafe_allow_html=True)
            st.markdown(_structure_table(k, zq_s, cases), unsafe_allow_html=True)

    with t3:
        labels = {1:"1Q (3M)", 2:"2Q (6M)", 3:"3Q (9M)", 4:"4Q (1Y)"}
        for g in SR3_SPREAD_GAPS:
            k = f"{g}Q"
            st.markdown(f"<div style='color:#FF6600;font-size:10px;margin:4px 0 2px;'>◾ {labels.get(g,k)} SPREAD</div>",
                        unsafe_allow_html=True)
            st.markdown(_structure_table(k, sr3_s, cases), unsafe_allow_html=True)


def _render_butterflies(cases, sr1_c, zq_c, sr3_c, all_prices):
    from core.structures import compute_butterflies
    from config.constants import SR1_FLY_GAPS, ZQ_FLY_GAPS, SR3_FLY_GAPS

    sr1_f = {c["id"]: compute_butterflies(sr1_c, all_prices.get(c["id"],{}).get("SR1",{}), SR1_FLY_GAPS)
             for c in cases}
    zq_f  = {c["id"]: compute_butterflies(zq_c,  all_prices.get(c["id"],{}).get("ZQ", {}), ZQ_FLY_GAPS)
             for c in cases}
    sr3_f = {c["id"]: compute_butterflies(sr3_c, all_prices.get(c["id"],{}).get("SR3",{}), SR3_FLY_GAPS)
             for c in cases}

    bb_subsection("BUTTERFLIES  [+1 / −2 / +1]")
    t1, t2, t3 = st.tabs(["SR1 FLIES", "ZQ FLIES", "SR3 FLIES"])

    with t1:
        for g in SR1_FLY_GAPS:
            k = f"{g}M"
            st.markdown(f"<div style='color:#FF6600;font-size:10px;margin:4px 0 2px;'>◾ {k} FLY</div>",
                        unsafe_allow_html=True)
            st.markdown(_structure_table(k, sr1_f, cases), unsafe_allow_html=True)
    with t2:
        for g in ZQ_FLY_GAPS:
            k = f"{g}M"
            st.markdown(f"<div style='color:#FF6600;font-size:10px;margin:4px 0 2px;'>◾ {k} FLY</div>",
                        unsafe_allow_html=True)
            st.markdown(_structure_table(k, zq_f, cases), unsafe_allow_html=True)
    with t3:
        for g in SR3_FLY_GAPS:
            k = f"{g}Q"
            st.markdown(f"<div style='color:#FF6600;font-size:10px;margin:4px 0 2px;'>◾ {k} FLY</div>",
                        unsafe_allow_html=True)
            st.markdown(_structure_table(k, sr3_f, cases), unsafe_allow_html=True)


def _render_condors(cases, sr1_c, zq_c, sr3_c, all_prices):
    from core.structures import compute_condors

    gaps_sr1 = [1]
    gaps_sr3 = [1, 2]

    sr1_cond = {c["id"]: compute_condors(sr1_c, all_prices.get(c["id"],{}).get("SR1",{}), gaps_sr1)
                for c in cases}
    zq_cond  = {c["id"]: compute_condors(zq_c,  all_prices.get(c["id"],{}).get("ZQ", {}), gaps_sr1)
                for c in cases}
    sr3_cond = {c["id"]: compute_condors(sr3_c, all_prices.get(c["id"],{}).get("SR3",{}), gaps_sr3)
                for c in cases}

    bb_subsection("CONDORS  [+1 / −1 / −1 / +1]")
    t1, t2, t3 = st.tabs(["SR1 CONDORS", "ZQ CONDORS", "SR3 CONDORS"])

    with t1:
        for g in gaps_sr1:
            k = f"{g}M"
            st.markdown(f"<div style='color:#FF6600;font-size:10px;margin:4px 0 2px;'>◾ {k} CONDOR</div>",
                        unsafe_allow_html=True)
            st.markdown(_structure_table(k, sr1_cond, cases), unsafe_allow_html=True)
    with t2:
        for g in gaps_sr1:
            k = f"{g}M"
            st.markdown(f"<div style='color:#FF6600;font-size:10px;margin:4px 0 2px;'>◾ {k} CONDOR</div>",
                        unsafe_allow_html=True)
            st.markdown(_structure_table(k, zq_cond, cases), unsafe_allow_html=True)
    with t3:
        for g in gaps_sr3:
            k = f"{g}Q"
            st.markdown(f"<div style='color:#FF6600;font-size:10px;margin:4px 0 2px;'>◾ {k} CONDOR</div>",
                        unsafe_allow_html=True)
            st.markdown(_structure_table(k, sr3_cond, cases), unsafe_allow_html=True)


def _render_deflys(cases, sr1_c, zq_c, sr3_c, all_prices):
    from core.structures import compute_deflys

    gaps_sr1 = [1]
    gaps_sr3 = [1, 2]

    sr1_d = {c["id"]: compute_deflys(sr1_c, all_prices.get(c["id"],{}).get("SR1",{}), gaps_sr1)
             for c in cases}
    zq_d  = {c["id"]: compute_deflys(zq_c,  all_prices.get(c["id"],{}).get("ZQ", {}), gaps_sr1)
             for c in cases}
    sr3_d = {c["id"]: compute_deflys(sr3_c, all_prices.get(c["id"],{}).get("SR3",{}), gaps_sr3)
             for c in cases}

    bb_subsection("DEFLYS  [+1 / −3 / +3 / −1]")
    t1, t2, t3 = st.tabs(["SR1 DEFLYS", "ZQ DEFLYS", "SR3 DEFLYS"])

    with t1:
        for g in gaps_sr1:
            k = f"{g}M"
            st.markdown(f"<div style='color:#FF6600;font-size:10px;margin:4px 0 2px;'>◾ {k} DEFLY</div>",
                        unsafe_allow_html=True)
            st.markdown(_structure_table(k, sr1_d, cases), unsafe_allow_html=True)
    with t2:
        for g in gaps_sr1:
            k = f"{g}M"
            st.markdown(f"<div style='color:#FF6600;font-size:10px;margin:4px 0 2px;'>◾ {k} DEFLY</div>",
                        unsafe_allow_html=True)
            st.markdown(_structure_table(k, zq_d, cases), unsafe_allow_html=True)
    with t3:
        for g in gaps_sr3:
            k = f"{g}Q"
            st.markdown(f"<div style='color:#FF6600;font-size:10px;margin:4px 0 2px;'>◾ {k} DEFLY</div>",
                        unsafe_allow_html=True)
            st.markdown(_structure_table(k, sr3_d, cases), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────────────────────────────────────

def render_tab_structures(cm, sr1_c, zq_c, sr3_c, base_sofr, base_effr):
    bb_section("📈 STRUCTURES")

    if not cm.cases:
        st.info("Add cases in the sidebar to compute structures.")
        return

    # Case selector
    all_labels = [f"{c['id']} | {c['name']}" for c in cm.cases]
    default    = all_labels[:min(5, len(all_labels))]
    sel_labels = st.multiselect(
        "Select Cases",
        all_labels, default=default,
        key="struct_cases",
        label_visibility="visible",
    )
    sel_ids   = [s.split(" | ")[0] for s in sel_labels]
    sel_cases = [c for c in cm.cases if c["id"] in sel_ids]

    if not sel_cases:
        st.warning("Select at least one case.")
        return

    # Compute prices for selected cases
    with st.spinner(f"Computing prices for {len(sel_cases)} cases…"):
        all_prices = compute_prices_for_cases(sel_cases, sr1_c, zq_c, sr3_c)

    # Structure tabs
    s1, s2, s3, s4, s5 = st.tabs([
        "📊 OUTRIGHTS", "📉 SPREADS", "🦋 BUTTERFLIES", "🔷 CONDORS", "🌀 DEFLYS"
    ])

    with s1:
        _render_outrights(sel_cases, sr1_c, zq_c, sr3_c, all_prices)

    with s2:
        _render_spreads(sel_cases, sr1_c, zq_c, sr3_c, all_prices)

    with s3:
        _render_butterflies(sel_cases, sr1_c, zq_c, sr3_c, all_prices)

    with s4:
        _render_condors(sel_cases, sr1_c, zq_c, sr3_c, all_prices)

    with s5:
        _render_deflys(sel_cases, sr1_c, zq_c, sr3_c, all_prices)
