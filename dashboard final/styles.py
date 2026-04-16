"""
STIR Terminal — Bloomberg Dark Theme (v2)
Full-screen · No overlapping text · Responsive · Professional
"""
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&display=swap');

/* ═══ RESET & BASE ══════════════════════════════════════════════════════ */
*, *::before, *::after {
    font-family: 'IBM Plex Mono', 'Courier New', monospace !important;
    box-sizing: border-box;
}
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
.main, section.main, .block-container {
    background-color: #000 !important;
    color: #C0C0C0 !important;
}
/* Full viewport height — no blue gaps */
[data-testid="stAppViewContainer"] > div:first-child {
    min-height: 100vh;
}
[data-testid="block-container"] {
    padding: 0.3rem 0.8rem 2rem !important;
    max-width: 100% !important;
}

/* ═══ SIDEBAR ═══════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background-color: #050505 !important;
    border-right: 1px solid #FF6600 !important;
}
[data-testid="stSidebar"] > div {
    padding: 0.5rem 0.6rem !important;
}
[data-testid="stSidebar"] *:not(button):not(input) {
    color: #C0C0C0 !important;
}

/* ═══ SCROLLBAR ═════════════════════════════════════════════════════════ */
::-webkit-scrollbar            { width: 5px; height: 5px; }
::-webkit-scrollbar-track      { background: #000; }
::-webkit-scrollbar-thumb      { background: #FF6600; border-radius: 3px; }

/* ═══ HEADER ════════════════════════════════════════════════════════════ */
.bb-header {
    background: linear-gradient(90deg, #150800 0%, #000 70%);
    border-bottom: 2px solid #FF8C00;
    padding: 6px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 6px;
}
.bb-h-title { color: #FF8C00; font-size: 14px; font-weight: 700; letter-spacing: 3px; }
.bb-h-sub   { color: #FF6600; font-size: 10px; letter-spacing: 1px; margin-top: 2px; }
.bb-h-right { text-align: right; }
.bb-h-time  { color: #FFB347; font-size: 10px; }
.bb-h-cases { color: #00FF41; font-size: 10px; font-weight: 700; }

/* ═══ SECTION / SUBSECTION LABELS ══════════════════════════════════════ */
.bb-section {
    background: #0D0D00;
    border-left: 3px solid #FF8C00;
    border-bottom: 1px solid #2A2A00;
    padding: 3px 8px;
    color: #FF8C00;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 6px 0 4px;
}
.bb-subsection {
    color: #FF6600;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1px;
    border-bottom: 1px solid #1A1A1A;
    padding: 2px 0;
    margin: 5px 0 3px;
    text-transform: uppercase;
}

/* ═══ RATE DISPLAY ══════════════════════════════════════════════════════ */
.bb-rate-pair {
    display: flex;
    gap: 6px;
    margin: 4px 0 6px;
}
.bb-rate-box {
    flex: 1;
    background: #0D0D00;
    border: 1px solid #FF6600;
    border-radius: 2px;
    padding: 5px 8px;
    text-align: center;
}
.bb-rl  { color: #FF8C00; font-size: 9px; letter-spacing: 2px; }
.bb-rv  { color: #00FF41; font-size: 17px; font-weight: 700; line-height: 1.2; }

/* ═══ INPUTS ════════════════════════════════════════════════════════════ */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
textarea {
    background: #0A0A00 !important;
    color: #FF6600 !important;
    border: 1px solid #444 !important;
    border-radius: 2px !important;
    font-size: 11px !important;
}
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextInput"] input:focus,
textarea:focus {
    border-color: #FF8C00 !important;
    box-shadow: 0 0 4px rgba(255,140,0,0.3) !important;
}
[data-testid="stSelectbox"] > div > div {
    background: #0A0A00 !important;
    border: 1px solid #444 !important;
    color: #FF6600 !important;
    font-size: 11px !important;
}
/* Data editor cells */
[data-testid="stDataEditor"] { font-size: 11px !important; }
[data-testid="stDataEditor"] input { font-size: 11px !important; }

/* ═══ BUTTONS ═══════════════════════════════════════════════════════════ */
.stButton > button {
    background: #000 !important;
    color: #FF8C00 !important;
    border: 1px solid #FF8C00 !important;
    border-radius: 2px !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
    font-weight: 700 !important;
    padding: 5px 12px !important;
    transition: all 0.12s !important;
    width: 100% !important;
}
.stButton > button:hover {
    background: #1A0D00 !important;
    color: #FFB347 !important;
    border-color: #FFB347 !important;
    box-shadow: 0 0 6px rgba(255,140,0,0.35) !important;
}
.stButton > button[kind="primary"] {
    background: #FF6600 !important;
    color: #000 !important;
    border-color: #FF8C00 !important;
}
.stButton > button[kind="primary"]:hover {
    background: #FF8C00 !important;
}

/* ═══ TABS ══════════════════════════════════════════════════════════════ */
[data-testid="stTabs"] [role="tablist"] {
    gap: 0 !important;
    border-bottom: 2px solid #FF6600 !important;
    background: #000 !important;
    flex-wrap: wrap !important;
}
[data-testid="stTabs"] button[role="tab"] {
    background: #000 !important;
    color: #888 !important;
    border: 1px solid #2A2A2A !important;
    border-bottom: none !important;
    padding: 5px 12px !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
    font-weight: 600 !important;
    border-radius: 0 !important;
    white-space: nowrap !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    background: #1A0D00 !important;
    color: #FF8C00 !important;
    border-color: #FF6600 !important;
    border-bottom: 2px solid #1A0D00 !important;
}
[data-testid="stTabs"] button[role="tab"]:hover {
    background: #0D0800 !important;
    color: #FF6600 !important;
}

/* ═══ MULTISELECT ═══════════════════════════════════════════════════════ */
[data-testid="stMultiSelect"] > div > div {
    background: #0A0A00 !important;
    border: 1px solid #444 !important;
}
span[data-baseweb="tag"] {
    background: #1A0D00 !important;
    border: 1px solid #FF6600 !important;
    color: #FF6600 !important;
    font-size: 10px !important;
}

/* ═══ RADIO / TOGGLE ════════════════════════════════════════════════════ */
[data-testid="stRadio"] label { font-size: 11px !important; }
[data-testid="stRadio"] [data-baseweb="radio"] {
    border-color: #FF6600 !important;
}

/* ═══ EXPANDER ══════════════════════════════════════════════════════════ */
[data-testid="stExpander"] {
    border: 1px solid #2A2A2A !important;
    background: #050505 !important;
    margin: 2px 0 !important;
}
[data-testid="stExpander"] summary {
    color: #FF6600 !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
    padding: 4px 8px !important;
}

/* ═══ METRIC ════════════════════════════════════════════════════════════ */
[data-testid="metric-container"] {
    background: #0D0D00;
    border: 1px solid #2A2A2A;
    padding: 6px 10px !important;
    border-radius: 2px;
}
[data-testid="metric-container"] label   { color: #FF8C00 !important; font-size: 9px !important; letter-spacing: 1px !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #00FF41 !important; font-size: 16px !important; }
[data-testid="metric-container"] [data-testid="stMetricDelta"] { font-size: 10px !important; }

/* ═══ ALERTS ════════════════════════════════════════════════════════════ */
[data-testid="stAlert"] { font-size: 11px !important; }

/* ═══ BLOOMBERG TABLE ═══════════════════════════════════════════════════ */
.bb-table-wrap {
    overflow-x: auto;
    overflow-y: auto;
    max-height: 460px;
    border: 1px solid #2A2A2A;
    margin: 4px 0 10px;
    background: #000;
    border-radius: 2px;
}
table.bb-tbl {
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
    background: #000;
    min-width: 400px;
}
table.bb-tbl thead { position: sticky; top: 0; z-index: 10; }
table.bb-tbl th {
    background: #0D0800;
    color: #FF8C00;
    border: 1px solid #2A2A2A;
    padding: 4px 8px;
    text-align: center;
    font-size: 10px;
    letter-spacing: 1px;
    font-weight: 700;
    white-space: nowrap;
}
table.bb-tbl td {
    border: 1px solid #111;
    padding: 3px 7px;
    text-align: right;
    color: #C0C0C0;
    white-space: nowrap;
    font-size: 11px;
}
table.bb-tbl td.lbl {
    text-align: left;
    color: #FF6600;
    font-weight: 600;
    position: sticky;
    left: 0;
    background: #060600;
    border-right: 1px solid #FF6600;
    padding-left: 8px;
    min-width: 140px;
    max-width: 220px;
    overflow: hidden;
    text-overflow: ellipsis;
}
table.bb-tbl tr:nth-child(even) td { background: #040400; }
table.bb-tbl tr:hover td { background: #1A0D00 !important; color: #FFB347 !important; }
table.bb-tbl td.pos { color: #00FF41 !important; font-weight: 600; }
table.bb-tbl td.neg { color: #FF3131 !important; font-weight: 600; }
table.bb-tbl td.zer { color: #555 !important; }
table.bb-tbl td.mkt { color: #00BFFF !important; font-weight: 600; }

/* ═══ CASE ITEMS ════════════════════════════════════════════════════════ */
.bb-case-item {
    background: #080800;
    border: 1px solid #2A2A2A;
    border-left: 3px solid #FF6600;
    padding: 4px 8px;
    margin: 2px 0;
    font-size: 10px;
}
.bb-case-id   { color: #555; font-size: 9px; }
.bb-case-name { color: #FF6600; font-weight: 600; }
.bb-case-info { color: #777; font-size: 9px; margin-top: 1px; }

/* ═══ STATUS BAR ════════════════════════════════════════════════════════ */
.bb-status {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: #0D0800;
    border-top: 1px solid #FF6600;
    padding: 2px 14px;
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: #FF6600;
    z-index: 9999;
}

/* ═══ HIDE STREAMLIT CHROME ═════════════════════════════════════════════ */
#MainMenu, footer, header          { visibility: hidden !important; }
[data-testid="stToolbar"]          { display: none !important; }
[data-testid="stDecoration"]       { display: none !important; }

/* ═══ MISC FIXES ════════════════════════════════════════════════════════ */
label, .stMarkdown p { color: #C0C0C0 !important; font-size: 11px !important; }
h1 { color: #FF8C00 !important; font-size: 15px !important; letter-spacing: 3px !important; }
h2 { color: #FF6600 !important; font-size: 12px !important; letter-spacing: 2px !important; }
h3 { color: #FFB347 !important; font-size: 11px !important; letter-spacing: 1px !important; }
.stMarkdown hr { border-color: #2A2A2A !important; margin: 4px 0 !important; }
[data-testid="column"] { padding: 0 4px !important; }
</style>
"""


def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)


def bb_header(title: str, subtitle: str = ""):
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    st.markdown(f"""
    <div class="bb-header">
        <div>
            <div class="bb-h-title">⬛ {title}</div>
            <div class="bb-h-sub">{subtitle}</div>
        </div>
        <div class="bb-h-right">
            <div class="bb-h-time">🕐 {now}</div>
        </div>
    </div>""", unsafe_allow_html=True)


def bb_section(label: str):
    st.markdown(f'<div class="bb-section">{label}</div>', unsafe_allow_html=True)


def bb_subsection(label: str):
    st.markdown(f'<div class="bb-subsection">▸ {label}</div>', unsafe_allow_html=True)


def build_table(
    row_labels: list,
    col_labels: list,
    data: list,
    fmt: str = "{:.4f}",
    col_types: list = None,   # list of "pos/neg/mkt/plain" per column
) -> str:
    """
    Build Bloomberg HTML table.
    data[i][j] = value at row i, col j.
    """
    html = '<div class="bb-table-wrap"><table class="bb-tbl"><thead><tr>'
    html += '<th>INSTRUMENT</th>'
    for col in col_labels:
        html += f'<th>{col}</th>'
    html += '</tr></thead><tbody>'

    for i, (lbl, row) in enumerate(zip(row_labels, data)):
        html += '<tr>'
        html += f'<td class="lbl">{lbl}</td>'
        for j, val in enumerate(row):
            col_class = (col_types[j] if col_types and j < len(col_types) else None)
            if val is None or (isinstance(val, float) and val != val):
                html += '<td class="zer">—</td>'
                continue
            try:
                fv = float(val)
                if col_class == "mkt":
                    cls = "mkt"
                elif fv > 0.0001:
                    cls = "pos"
                elif fv < -0.0001:
                    cls = "neg"
                else:
                    cls = "zer"
                html += f'<td class="{cls}">{fmt.format(fv)}</td>'
            except (TypeError, ValueError):
                html += f'<td class="zer">{val}</td>'
        html += '</tr>'

    html += '</tbody></table></div>'
    return html


def status_bar(n_cases: int, base_sofr: float, base_effr: float):
    st.markdown(f"""
    <div class="bb-status">
        <span>STIR TRADING TERMINAL v2</span>
        <span>SOFR: <b>{base_sofr:.4f}%</b> &nbsp;|&nbsp; EFFR: <b>{base_effr:.4f}%</b></span>
        <span>CASES: <b>{n_cases}</b></span>
    </div>""", unsafe_allow_html=True)
