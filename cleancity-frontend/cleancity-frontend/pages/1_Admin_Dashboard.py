"""
CleanCity Copilot — Municipal Admin Dashboard
Alibaba Cloud AI Hackathon 2026
"""

import pandas as pd
import streamlit as st

from utils.api_client import get_tickets, update_ticket_status
from utils.mock_data import SEVERITY_COLOR, CATEGORY_ICON

st.set_page_config(
    page_title="CleanCity Copilot — Admin",
    page_icon=None,
    layout="wide",
)

# ── Design System ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Inter:wght@400;500&display=swap');

    /* ── Base ── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0A1628;
        color: #D8E4F0;
    }
    .main .block-container {
        padding: 2rem 2.5rem 3rem 2.5rem;
        background-color: #0A1628;
        max-width: 100%;
    }

    /* ── Hide Streamlit Toolbar (Deploy & 3 Dots) ── */
    [data-testid="stToolbar"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background-color: #071020 !important;
        border-right: 1px solid #1E3A5F;
    }
    section[data-testid="stSidebar"] * { color: #8899AA !important; }
    section[data-testid="stSidebar"] .sidebar-wordmark {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.16em;
        color: #C9A84C !important;
        text-transform: uppercase;
    }
    section[data-testid="stSidebar"] .sidebar-product-name {
        font-family: 'DM Sans', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: #F0F4F8 !important;
        margin-bottom: 0.1rem;
    }
    section[data-testid="stSidebar"] .sidebar-role {
        font-size: 0.78rem;
        color: #4D6478 !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: #1E3A5F !important;
    }
    section[data-testid="stSidebar"] label { color: #8899AA !important; }
    section[data-testid="stSidebar"] .stRadio label { font-size: 0.88rem !important; }
    section[data-testid="stSidebar"] div[data-baseweb="select"] {
        background: #0A1628 !important;
        border-color: #1E3A5F !important;
    }

    /* ── Page header ── */
    .dash-wordmark {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.18em;
        color: #C9A84C;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }
    .dash-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 1.6rem;
        font-weight: 600;
        color: #F0F4F8;
        margin: 0 0 0.1rem 0;
        line-height: 1.2;
    }
    .dash-meta {
        font-size: 0.8rem;
        color: #4D6478;
    }

    /* ── Metric cards ── */
    div[data-testid="stMetric"] {
        background: #112240;
        border: 1px solid #1E3A5F;
        border-radius: 4px;
        padding: 1.2rem 1.4rem 1rem 1.4rem;
    }
    div[data-testid="stMetric"] label {
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.12em !important;
        text-transform: uppercase !important;
        color: #4D6478 !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-family: 'DM Sans', sans-serif;
        font-size: 2rem !important;
        font-weight: 600 !important;
        color: #F0F4F8 !important;
    }

    /* ── Section headers ── */
    .section-header {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.14em;
        color: #C9A84C;
        text-transform: uppercase;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #1E3A5F;
        margin: 2rem 0 1rem 0;
    }

    /* ── Severity badge ── */
    .sev-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 2px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.06em;
    }

    /* ── Alert list item ── */
    .alert-item {
        background: #112240;
        border: 1px solid #1E3A5F;
        border-left: 3px solid #DC2626;
        border-radius: 4px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.6rem;
    }
    .alert-ticket-id {
        font-size: 0.7rem;
        font-weight: 600;
        color: #4D6478;
        letter-spacing: 0.1em;
    }
    .alert-location {
        font-size: 0.88rem;
        font-weight: 500;
        color: #D8E4F0;
        margin: 0.1rem 0;
    }
    .alert-action {
        font-size: 0.78rem;
        color: #8899AA;
    }

    /* ── Data table ── */
    div[data-testid="stDataFrame"] {
        border: 1px solid #1E3A5F !important;
        border-radius: 4px;
    }
    div[data-testid="stDataFrame"] thead th {
        background: #071020 !important;
        color: #4D6478 !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
    }
    div[data-testid="stDataFrame"] tbody td {
        color: #D8E4F0 !important;
        font-size: 0.85rem !important;
        background: #112240 !important;
        border-bottom: 1px solid #1A3050 !important;
    }

    /* ── Detail panel ── */
    .detail-field-label {
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #4D6478;
        margin-bottom: 0.2rem;
        margin-top: 1rem;
    }
    .detail-field-value {
        font-size: 0.9rem;
        color: #D8E4F0;
        line-height: 1.5;
    }
    .detail-ticket-heading {
        font-family: 'DM Sans', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: #F0F4F8;
        margin-bottom: 0.4rem;
    }

    /* ── Selectbox inputs ── */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        background: #071020 !important;
        border-color: #1E3A5F !important;
        border-radius: 4px !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
        color: #D8E4F0 !important;
    }

    /* ── Primary button ── */
    div.stButton > button[kind="primary"] {
        background: #C9A84C !important;
        color: #0A1628 !important;
        font-family: 'DM Sans', sans-serif;
        font-weight: 600;
        border: none !important;
        border-radius: 4px;
        letter-spacing: 0.03em;
    }
    div.stButton > button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid #1E3A5F !important;
        color: #8899AA !important;
        border-radius: 4px;
    }

    /* ── Alert / info boxes ── */
    div[data-testid="stAlert"] {
        background: #0D2137 !important;
        border-left: 3px solid #C9A84C !important;
        border-radius: 4px !important;
        color: #D8E4F0 !important;
    }

    /* ── Map ── */
    div[data-testid="stDeckGlJsonChart"],
    iframe[title*="map"] {
        border: 1px solid #1E3A5F !important;
        border-radius: 4px;
    }

    /* ── Divider ── */
    hr { border-color: #1E3A5F !important; margin: 1.5rem 0 !important; }

    /* ── Caption ── */
    div[data-testid="stCaptionContainer"] p {
        color: #4D6478 !important;
        font-size: 0.76rem !important;
    }

    /* ── Header bar ── */
    header[data-testid="stHeader"] { background: #071020 !important; border-bottom: 1px solid #1E3A5F; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="sidebar-wordmark">Municipal Command</p>', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-product-name">CleanCity Copilot</p>', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-role">Admin Console</p>', unsafe_allow_html=True)
    st.divider()

    nav = st.radio(
        "View",
        ["Active Issues", "Resolved Tickets", "Settings"],
        label_visibility="collapsed",
    )
    st.divider()

    st.markdown("**Filters**")
    f_category = st.selectbox("Category", ["All", "Garbage", "Pothole", "Sewerage"])
    f_severity = st.selectbox("Severity", ["All", "Critical", "High", "Medium", "Low"])
    f_date = st.selectbox("Time window", ["Last 24h", "Last 48h", "Last 7 days", "All time"])
    st.divider()
    st.caption("CleanCity Copilot · Alibaba Cloud AI Hackathon 2026")

# ── Settings page ────────────────────────────────────────────────────────────────
if nav == "Settings":
    st.markdown('<p class="dash-wordmark">System</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="dash-title">Settings</h1>', unsafe_allow_html=True)
    st.info("Backend URL configuration, notification preferences, and team management will be available here.")
    st.stop()

# ── BULLETPROOF DATA LOADING ──────────────────────────────────────────────────────
status_filter = "Resolved" if nav == "Resolved Tickets" else None
raw_data = get_tickets(status=status_filter, category=f_category)

# Safety Check: Extract list if backend wrapped it in a dict (total, count, tickets)
if isinstance(raw_data, dict) and "tickets" in raw_data:
    tickets_list = raw_data["tickets"]
elif isinstance(raw_data, list):
    tickets_list = raw_data
else:
    tickets_list = []

df = pd.DataFrame(tickets_list)

# Wall #1 — backend returned nothing at all OR columns are entirely missing
if df.empty or "severity" not in df.columns or "created_at" not in df.columns:
    st.markdown('<p class="dash-wordmark">Operations</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="dash-title">No data</h1>', unsafe_allow_html=True)
    st.warning("No tickets found. The backend returned an empty dataset for the current filters.")
    st.stop()

# Severity filter
if f_severity != "All":
    df = df[df["severity"] == f_severity]
    if df.empty:
        st.warning("No tickets match the selected severity filter.")
        st.stop()

# Date filter
hours_map = {"Last 24h": 24, "Last 48h": 48, "Last 7 days": 168, "All time": None}
hrs = hours_map[f_date]
if hrs is not None:
    cutoff = pd.Timestamp.now() - pd.Timedelta(hours=hrs)
    df = df[pd.to_datetime(df["created_at"]) >= cutoff]
    if df.empty:
        st.warning("No tickets fall within the selected time window.")
        st.stop()

# ── Page header ─────────────────────────────────────────────────────────────────
is_resolved_view = nav == "Resolved Tickets"
st.markdown(
    f'<p class="dash-wordmark">{"Resolved" if is_resolved_view else "Operations"}</p>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<h1 class="dash-title">{"Resolved Tickets" if is_resolved_view else "Issue Dashboard"}</h1>',
    unsafe_allow_html=True,
)
now_str = pd.Timestamp.now().strftime("%d %b %Y, %H:%M")
st.markdown(f'<p class="dash-meta">Last updated: {now_str} &nbsp;|&nbsp; {len(df)} records loaded</p>', unsafe_allow_html=True)

# ── Metrics row ──────────────────────────────────────────────────────────────────
total_open     = int((df["status"] == "Open").sum())
critical_count = int(((df["status"] != "Resolved") & (df["severity"] == "Critical")).sum())
in_progress    = int((df["status"] == "In Progress").sum())
resolved_today = int(
    ((df["status"] == "Resolved")
    & (pd.to_datetime(df["created_at"]).dt.date == pd.Timestamp.now().date())).sum()
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Open Issues",            total_open)
m2.metric("Critical — Unresolved",  critical_count)
m3.metric("In Progress",            in_progress)
m4.metric("Resolved Today",         resolved_today)

# ── Map + Critical Alerts (asymmetric split) ────────────────────────────────────
st.markdown('<p class="section-header">Geospatial Overview</p>', unsafe_allow_html=True)

map_col, alert_col = st.columns([3, 2], gap="large")

with map_col:
    # Ensure lat/lng columns exist before plotting
    if "lat" in df.columns and "lng" in df.columns:
        map_df = df.dropna(subset=["lat", "lng"]).copy()
        if not map_df.empty:
            map_df["color"] = map_df["severity"].apply(
                lambda s: [int(SEVERITY_COLOR.get(s, "#8899AA")[i:i+2], 16) for i in (1, 3, 5)] + [210]
            )
            st.map(map_df, latitude="lat", longitude="lng", color="color", size=55)
            st.caption("Red — Critical   |   Orange — High   |   Yellow — Medium   |   Green — Low")
        else:
            st.info("Map data unavailable.")
    else:
        st.info("Coordinate data missing.")

with alert_col:
    st.markdown("**Unresolved critical alerts**")
    critical_df = df[(df["severity"] == "Critical") & (df["status"] != "Resolved")].head(8)
    if critical_df.empty:
        st.caption("No critical alerts in current filter.")
    else:
        for _, row in critical_df.iterrows():
            st.markdown(
                f"""
                <div class="alert-item">
                    <div class="alert-ticket-id">{row['ticket_id']} &nbsp;·&nbsp; {row['category']}</div>
                    <div class="alert-location">{row['address']}</div>
                    <div class="alert-action">{row.get('recommended_action', '—')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ── Ticket table ─────────────────────────────────────────────────────────────────
st.markdown('<p class="section-header">All Tickets</p>', unsafe_allow_html=True)

SEV_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}

display_df = df.copy()
display_df["_sev_order"] = display_df["severity"].map(SEV_ORDER).fillna(9)
display_df = display_df.sort_values("_sev_order").drop(columns=["_sev_order"])

table_df = display_df.rename(columns={
    "ticket_id":     "Ticket ID",
    "category":      "Category",
    "severity":      "Severity",
    "address": "Location",
    "status":        "Status",
    "created_at":    "Reported",
})[["Ticket ID", "Category", "Severity", "Location", "Status", "Reported"]]

table_df["Reported"] = pd.to_datetime(table_df["Reported"]).dt.strftime("%d %b %Y")

st.dataframe(table_df, use_container_width=True, hide_index=True)

# ── Ticket detail + action ────────────────────────────────────────────────────────
st.markdown('<p class="section-header">Ticket Detail &amp; Field Action</p>', unsafe_allow_html=True)

ticket_ids = df["ticket_id"].tolist()
selected_id = st.selectbox("Select ticket", ticket_ids, label_visibility="collapsed")

if selected_id:
    row = df[df["ticket_id"] == selected_id].iloc[0]
    sev = row["severity"]
    sev_hex = SEVERITY_COLOR.get(sev, "#8899AA")

    img_col, info_col = st.columns([1, 1.5], gap="large")

    with img_col:
        import os
        
        # Seedha local disk se file uthatay hain, HTTP request ki zaroorat hi nahi!
        demo_fallback = os.path.join("media", "images", "hyderabad_demo_sample.jpg")
        raw_path = str(row.get("image_url") or row.get("image_path") or "").strip()
        
        target_path = demo_fallback
        if raw_path and raw_path.lower() not in ["0", "null", "none"]:
            clean_path = raw_path.replace("http://localhost:8000/", "").lstrip('/')
            if not os.path.exists(clean_path):
                # Agar path mein media nahi hai toh add kar lo
                potential_path = os.path.join("media", clean_path)
                if os.path.exists(potential_path):
                    target_path = potential_path
            else:
                target_path = clean_path

        try:
            if os.path.exists(target_path):
                st.image(
                    target_path,
                    caption=f"Filed evidence — {row['ticket_id']}",
                    use_column_width=True, 
                )
            else:
                st.image(
                    demo_fallback,
                    caption=f"Filed evidence — {row['ticket_id']}",
                    use_column_width=True,
                )
        except Exception:
            st.markdown(
                """
                <div style="
                    background:#112240; border:1px solid #1E3A5F; border-radius:4px;
                    height:180px; display:flex; align-items:center; justify-content:center;
                    color:#4D6478; font-size:0.82rem;
                ">
                    Image missing on backend
                </div>
                """,
                unsafe_allow_html=True,
            )   
        st.markdown(
            f'<p class="detail-field-label">Location</p>'
            f'<p class="detail-field-value">{row["address"]}</p>',
            unsafe_allow_html=True,
        )
        reported_str = pd.to_datetime(row["created_at"]).strftime("%d %b %Y, %H:%M")
        st.markdown(
            f'<p class="detail-field-label">Reported</p>'
            f'<p class="detail-field-value">{reported_str}</p>',
            unsafe_allow_html=True,
        )
        dup = int(row.get("duplicate_count", 0))
        if dup > 0:
            st.caption(f"{dup} additional report(s) consolidated within 50 m / 48 h window.")

    with info_col:
        st.markdown(
            f'<p class="detail-ticket-heading">{row["category"]} — {row["ticket_id"]}</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<span class="sev-badge" style="background:{sev_hex}22; color:{sev_hex};">'
            f'{sev.upper()} SEVERITY</span>',
            unsafe_allow_html=True,
        )

        st.markdown('<p class="detail-field-label" style="margin-top:1.2rem;">AI Assessment</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="detail-field-value">{row.get("reasoning", row.get("translated_text", "—"))}</p>', unsafe_allow_html=True)

        st.markdown('<p class="detail-field-label">Recommended Field Action</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="detail-field-value">{row.get("recommended_action", row.get("ai_action_plan", "—"))}</p>', unsafe_allow_html=True)

        transcribed = row.get("transcribed_note", "")
        if transcribed:
            st.markdown('<p class="detail-field-label">Transcribed Voice Note</p>', unsafe_allow_html=True)
            st.markdown(
                f'<p class="detail-field-value" style="color:#8899AA; font-style:italic;">{transcribed}</p>',
                unsafe_allow_html=True,
            )

        st.markdown('<p class="detail-field-label" style="margin-top:1.4rem;">Update Status</p>', unsafe_allow_html=True)
        current_status_idx = (
            ["Open", "In Progress", "Resolved"].index(row["status"])
            if row["status"] in ["Open", "In Progress", "Resolved"]
            else 0
        )
        new_status = st.selectbox(
            "Status",
            ["Open", "In Progress", "Resolved"],
            index=current_status_idx,
            key=f"status_{selected_id}",
            label_visibility="collapsed",
        )

        if st.button("Confirm status update", key=f"save_{selected_id}", type="primary"):
            res = update_ticket_status(selected_id, new_status)
            if res.get("success"):
                st.success(f"Ticket {selected_id} status updated to '{new_status}'.")
                if res.get("mock"):
                    st.caption("Demo mode — backend not connected. Status updated locally.")
                st.rerun()
            else:
                st.error("Status update failed. Check backend connectivity.")

st.divider()
st.caption("CleanCity Copilot · Municipal Admin Console · Alibaba Cloud AI Hackathon 2026")