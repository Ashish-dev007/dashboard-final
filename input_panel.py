"""
STIR Terminal — Sidebar Input Panel (v2)
Sections:
  1. Base Rates (SOFR / EFFR)
  2. Market Premiums (per-FOMC meeting, manual entry)
  3. Formula Builder
  4. Case Builder (annual + H1/H2, per year)
  5. Case List
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
from datetime import date

from config.fomc_dates import ALL_FOMC_MEETINGS, FOMC_BY_YEAR
from ui.styles import bb_section, bb_subsection


# ─────────────────────────────────────────────────────────────────────────────
# 1. BASE RATES
# ─────────────────────────────────────────────────────────────────────────────

def render_base_rates() -> tuple[float, float]:
    bb_section("BASE RATES")
    c1, c2 = st.columns(2)
    with c1:
        base_sofr = st.number_input(
            "SOFR %", min_value=0.0, max_value=20.0,
            value=st.session_state.get("base_sofr", 4.30),
            step=0.0025, format="%.4f", key="base_sofr_inp",
            help="Current SOFR"
        )
    with c2:
        base_effr = st.number_input(
            "EFFR %", min_value=0.0, max_value=20.0,
            value=st.session_state.get("base_effr", 4.33),
            step=0.0025, format="%.4f", key="base_effr_inp",
            help="Current EFFR"
        )
    st.session_state["base_sofr"] = base_sofr
    st.session_state["base_effr"] = base_effr

    st.markdown(f"""
    <div class="bb-rate-pair">
      <div class="bb-rate-box">
        <div class="bb-rl">SOFR</div>
        <div class="bb-rv">{base_sofr:.4f}%</div>
      </div>
      <div class="bb-rate-box">
        <div class="bb-rl">EFFR</div>
        <div class="bb-rv">{base_effr:.4f}%</div>
      </div>
    </div>""", unsafe_allow_html=True)
    return base_sofr, base_effr


# ─────────────────────────────────────────────────────────────────────────────
# 2. MARKET PREMIUMS
# ─────────────────────────────────────────────────────────────────────────────

def render_market_premiums() -> dict:
    """
    Per-FOMC meeting market-implied cut/hike in bps.
    Returns {effective_date: bps}
    Shows only next 16 meetings (2 years).
    """
    bb_section("MARKET PREMIUMS")
    with st.expander("📡 Enter market-implied bps per meeting", expanded=True):
        st.caption("Market pricing (OIS/futures implied). Neg = cuts, Pos = hikes.")

        # Get next 16 meetings from today
        today = date.today()
        upcoming = [m for m in ALL_FOMC_MEETINGS
                    if m["effective_date"] > today][:16]

        if not upcoming:
            return {}

        # Build editable dataframe
        default_key = "mkt_premiums_df"
        if default_key not in st.session_state:
            rows = []
            for i, m in enumerate(upcoming):
                d = m["decision_date"]
                sep = "⭐" if m["is_sep"] else "  "
                off = "~" if not m["is_official"] else " "
                rows.append({
                    "Meeting": f"{off}M{i+1} {d.strftime('%b %d %y')} {sep}",
                    "bps": 0.0,
                })
            st.session_state[default_key] = pd.DataFrame(rows)

        df = st.session_state[default_key]
        edited = st.data_editor(
            df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Meeting": st.column_config.TextColumn("Meeting", disabled=True, width="medium"),
                "bps": st.column_config.NumberColumn(
                    "bps", min_value=-200.0, max_value=200.0,
                    step=0.5, format="%.1f", width="small"
                ),
            },
            key="mkt_premiums_editor",
        )
        st.session_state[default_key] = edited

        total = edited["bps"].sum()
        col_t = "#00FF41" if total < -0.01 else ("#FF3131" if total > 0.01 else "#555")
        st.markdown(
            f"<small style='color:{col_t};'>Total: {total:+.1f} bps &nbsp;|&nbsp; "
            f"{len(upcoming)} meetings shown</small>",
            unsafe_allow_html=True,
        )

        # Map back to {effective_date: bps}
        mkt_cuts = {}
        for i, m in enumerate(upcoming):
            if i < len(edited):
                mkt_cuts[m["effective_date"]] = float(edited.iloc[i]["bps"])
            else:
                mkt_cuts[m["effective_date"]] = 0.0

        return mkt_cuts


# ─────────────────────────────────────────────────────────────────────────────
# 3. FORMULA BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def render_formula_builder(cm) -> None:
    bb_section("FORMULA BUILDER")
    with st.expander("🔧 Define custom weight distribution", expanded=False):
        st.caption("Weights = fraction of annual cut at each of 8 meetings")
        fname = st.text_input("Name", placeholder="e.g. War-2026", key="fml_name")
        fdesc = st.text_input("Description (optional)", key="fml_desc")

        weights = []
        row1 = st.columns(4)
        row2 = st.columns(4)
        for i, col in enumerate(row1 + row2):
            with col:
                w = st.number_input(
                    f"M{i+1}", min_value=0.0, max_value=1.0,
                    value=round(1/8, 4), step=0.01, format="%.3f",
                    key=f"fw_{i}",
                )
                weights.append(w)

        total = sum(weights)
        ok = abs(total - 1) < 0.02
        st.markdown(
            f"<small style='color:{'#00FF41' if ok else '#FF3131'};'>"
            f"∑ = {total:.3f} (auto-normalised)</small>",
            unsafe_allow_html=True,
        )

        if st.button("💾 SAVE FORMULA", key="save_fml"):
            if not fname.strip():
                st.error("Name required")
            elif fname in cm.get_formula_names():
                st.error("Name already exists")
            else:
                cm.add_formula(fname, weights, fdesc)
                st.success(f"Saved '{fname}'")
                st.rerun()

        st.markdown("---")
        bb_subsection("Saved Formulas")
        for f in cm.formulas:
            tag = "🔒" if f.get("is_builtin") else "📋"
            with st.expander(f"{tag} {f['name']}", expanded=False):
                w_str = "  ".join(f"{w:.3f}" for w in f["weights"])
                st.markdown(
                    f"<small style='color:#666'>{f.get('description','')}</small><br>"
                    f"<code style='color:#FF6600;font-size:9px'>{w_str}</code>",
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────────────────────────────────────
# 4. CASE BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def _year_row(year: int, formula_names: list, pfx: str) -> dict:
    """Render one year's config row. Returns year_config dict."""
    meetings = FOMC_BY_YEAR.get(year, [])
    official = meetings and meetings[0].get("is_official", False)
    icon = "✅" if official else "🔮"
    st.markdown(
        f"<div style='color:#FF8C00;font-size:10px;letter-spacing:1px;"
        f"border-top:1px solid #1A1A1A;padding-top:4px;margin-top:3px;'>"
        f"{icon} {year}</div>",
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "Mode", ["Annual", "H1 / H2"],
        horizontal=True, key=f"{pfx}_m_{year}",
        label_visibility="collapsed",
    )
    cfg = {"mode": "annual" if mode == "Annual" else "h1h2"}

    if mode == "Annual":
        c1, c2 = st.columns([2, 3])
        with c1:
            cfg["annual_cut"] = st.number_input(
                "bps", value=0.0, step=0.5, format="%.1f",
                key=f"{pfx}_ac_{year}",
                help="Total cut(−)/hike(+) in bps for year"
            )
        with c2:
            cfg["formula_name"] = st.selectbox(
                "Formula", formula_names, key=f"{pfx}_af_{year}"
            )
    else:
        # H1
        st.markdown("<small style='color:#888'>H1 (Jan–Jun)</small>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            cfg["h1_cut"] = st.number_input(
                "H1 bps", value=0.0, step=0.5, format="%.1f",
                key=f"{pfx}_h1c_{year}"
            )
        with c2:
            cfg["h1_formula"] = st.selectbox(
                "H1 Model", formula_names, key=f"{pfx}_h1f_{year}"
            )
        # H2
        st.markdown("<small style='color:#888'>H2 (Jul–Dec)</small>", unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            cfg["h2_cut"] = st.number_input(
                "H2 bps", value=0.0, step=0.5, format="%.1f",
                key=f"{pfx}_h2c_{year}"
            )
        with c4:
            cfg["h2_formula"] = st.selectbox(
                "H2 Model", formula_names, key=f"{pfx}_h2f_{year}"
            )
    return cfg


def render_case_builder(cm) -> None:
    bb_section("CASE BUILDER")
    fnames = cm.get_formula_names()

    case_name = st.text_input(
        "Case Name", placeholder="e.g. Base-50bp", key="cb_name"
    )

    year_configs = {}
    with st.expander("📅 YEAR-BY-YEAR RATE PATH", expanded=True):
        for y in [2026, 2027, 2028, 2029, 2030]:
            year_configs[str(y)] = _year_row(y, fnames, "cb")

    if st.button("🔍 PREVIEW CUTS", key="preview_btn"):
        from core.case_manager import build_rate_path
        sofr = st.session_state.get("base_sofr", 4.30)
        effr = st.session_state.get("base_effr", 4.33)
        _, _, cuts = build_rate_path(sofr, effr, year_configs)
        if cuts:
            rows = [f"{d.strftime('%Y-%m-%d')}  {v:+.2f} bps"
                    for d, v in sorted(cuts.items())]
            st.code("\n".join(rows), language=None)
        else:
            st.info("All holds — no rate changes")

    st.markdown("<hr style='border-color:#1A1A1A;margin:4px 0;'>", unsafe_allow_html=True)

    if st.button("➕ ADD CASE", type="primary", key="add_case"):
        if not case_name.strip():
            st.error("Enter a case name")
        elif case_name in [c["name"] for c in cm.cases]:
            st.error(f"'{case_name}' already exists")
        else:
            sofr = st.session_state.get("base_sofr_inp", 4.30)
            effr = st.session_state.get("base_effr_inp", 4.33)
            cm.add_case(case_name, effr, sofr, year_configs)
            st.success(f"✅ Added '{case_name}' ({len(cm.cases)} total)")
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# 5. CASE LIST
# ─────────────────────────────────────────────────────────────────────────────

def render_case_list(cm) -> None:
    bb_section(f"CASES  [{len(cm.cases)}]")
    if not cm.cases:
        st.markdown(
            "<div style='color:#444;font-size:10px;padding:8px;'>"
            "No cases — build above.</div>",
            unsafe_allow_html=True,
        )
        return

    for case in cm.cases:
        total = sum(case["meeting_cuts"].values())
        col_v = "#00FF41" if total < -0.01 else ("#FF3131" if total > 0.01 else "#888")
        c1, c2, c3 = st.columns([5, 1, 1])
        with c1:
            st.markdown(f"""
            <div class="bb-case-item">
              <div>
                <span class="bb-case-id">{case['id']}</span>
                <span class="bb-case-name"> {case['name']}</span>
              </div>
              <div class="bb-case-info">
                SOFR {case['base_sofr']:.2f}% │
                <span style="color:{col_v}">Σ {total:+.1f}bps</span>
              </div>
            </div>""", unsafe_allow_html=True)
        with c2:
            if st.button("⎘", key=f"dup_{case['id']}", help="Duplicate"):
                cm.duplicate_case(case["id"], f"{case['name']}(2)")
                st.rerun()
        with c3:
            if st.button("✕", key=f"del_{case['id']}", help="Delete"):
                cm.delete_case(case["id"])
                st.rerun()

    st.markdown("<hr style='border-color:#1A1A1A;margin:4px 0;'>", unsafe_allow_html=True)
    if st.button("🗑 CLEAR ALL", key="clear_all"):
        cm.delete_all_cases()
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar(cm) -> tuple:
    """Render full sidebar. Returns (base_sofr, base_effr, market_cuts)."""
    st.markdown(
        "<div style='text-align:center;color:#FF8C00;font-size:12px;"
        "font-weight:700;letter-spacing:3px;border-bottom:1px solid #FF6600;"
        "padding-bottom:6px;margin-bottom:6px;'>⬛ CONTROLS</div>",
        unsafe_allow_html=True,
    )

    base_sofr, base_effr = render_base_rates()
    st.markdown("<hr style='border-color:#1A1A1A;margin:4px 0;'>", unsafe_allow_html=True)

    market_cuts = render_market_premiums()
    st.markdown("<hr style='border-color:#1A1A1A;margin:4px 0;'>", unsafe_allow_html=True)

    render_formula_builder(cm)
    st.markdown("<hr style='border-color:#1A1A1A;margin:4px 0;'>", unsafe_allow_html=True)

    render_case_builder(cm)
    st.markdown("<hr style='border-color:#1A1A1A;margin:4px 0;'>", unsafe_allow_html=True)

    render_case_list(cm)

    return base_sofr, base_effr, market_cuts
