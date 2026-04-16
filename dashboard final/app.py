"""
STIR Trading Terminal v2 — Unified App
Bloomberg-style dashboard: Market + Scenario Overlay

Tabs:
  📊 Meeting Premiums — market vs scenario overlay charts
  📈 Structures       — outrights, spreads, flies, condors, deflys
  🧾 Trade Builder    — DV01, PnL/bp, scenario PnL

Usage:
    streamlit run app.py
"""

import streamlit as st
from datetime import datetime

# ── Page config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="STIR TERMINAL",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help":     None,
        "Report a bug": None,
        "About":        "STIR Trading Terminal v2 — SR1 | ZQ | SR3 | All Structures",
    },
)

# ── Imports (after page config) ───────────────────────────────────────────────
from ui.styles        import inject_css, bb_header, status_bar
from ui.input_panel   import render_sidebar
from ui.tab1_premiums import render_tab_premiums
from ui.tab2_structures import render_tab_structures
from ui.tab3_trade    import render_tab_trade
from core.case_manager import CaseManager
from core.date_utils   import (
    generate_sr1_contracts,
    generate_zq_contracts,
    generate_sr3_contracts,
)
from config.constants  import SR1_ZQ_HORIZON_MONTHS

# ── CSS ───────────────────────────────────────────────────────────────────────
inject_css()

# ── Session state ─────────────────────────────────────────────────────────────
if "cm" not in st.session_state:
    st.session_state["cm"] = CaseManager()
cm = st.session_state["cm"]

# ── Contract schedules (cached once) ─────────────────────────────────────────
@st.cache_resource
def load_contracts():
    sr1 = generate_sr1_contracts(SR1_ZQ_HORIZON_MONTHS)
    zq  = generate_zq_contracts(SR1_ZQ_HORIZON_MONTHS)
    sr3 = generate_sr3_contracts()
    return sr1, zq, sr3

sr1_c, zq_c, sr3_c = load_contracts()

# ── Header ────────────────────────────────────────────────────────────────────
bb_header(
    title    = "STIR TRADING TERMINAL",
    subtitle = (
        f"SR1({len(sr1_c)}) · ZQ({len(zq_c)}) · SR3({len(sr3_c)}) · "
        f"CASES({len(cm.cases)}) · "
        f"{datetime.now().strftime('%Y-%m-%d')}"
    ),
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    base_sofr, base_effr, market_cuts = render_sidebar(cm)

# ── Main tabs ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📊  MEETING PREMIUMS",
    "📈  STRUCTURES",
    "🧾  TRADE BUILDER",
])

with tab1:
    render_tab_premiums(
        cm, sr1_c, zq_c, sr3_c,
        base_sofr, base_effr, market_cuts,
    )

with tab2:
    render_tab_structures(
        cm, sr1_c, zq_c, sr3_c,
        base_sofr, base_effr,
    )

with tab3:
    render_tab_trade(
        cm, sr1_c, zq_c, sr3_c,
        base_sofr, base_effr,
    )

# ── Status bar ────────────────────────────────────────────────────────────────
status_bar(len(cm.cases), base_sofr, base_effr)
