"""
CleanCity Copilot — Citizen Reporting Portal
Alibaba Cloud AI Hackathon 2026
"""

import streamlit as st
from utils.api_client import submit_report

st.set_page_config(
    page_title="CleanCity Copilot — Report a Civic Issue",
    page_icon=None,
    layout="centered",
)

# ── Design System ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Inter:wght@400;500&display=swap');

    /* ── Base & Reset ── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0A1628;
        color: #D8E4F0;
    }
    .main .block-container {
        max-width: 680px;
        padding: 3rem 2rem 4rem 2rem;
        background-color: #0A1628;
    }

    /* ── FIX 3: Hide sidebar and its toggle on the citizen portal ── */
    [data-testid="stSidebar"]           { display: none !important; }
    [data-testid="collapsedControl"]    { display: none !important; }
    section[data-testid="stSidebarNav"] { display: none !important; }

    /* ── Page Header ── */
    .portal-wordmark {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.18em;
        color: #C9A84C;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .portal-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 2rem;
        font-weight: 600;
        color: #F0F4F8;
        line-height: 1.15;
        margin: 0 0 0.4rem 0;
    }
    .portal-subtitle {
        font-size: 0.92rem;
        color: #7A90A8;
        margin-bottom: 0;
        line-height: 1.5;
    }

    /* ── Section Labels ── */
    .form-section-label {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.14em;
        color: #C9A84C;
        text-transform: uppercase;
        margin: 2.4rem 0 0.6rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid #1E3A5F;
    }

    /* ── File uploader ── */
    div[data-testid="stFileUploader"] {
        background: #112240;
        border: 1px solid #1E3A5F;
        border-radius: 4px;
        padding: 1rem;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #C9A84C;
    }

    /* ── FIX 2: Text area — typed text and placeholder both readable ── */
    div[data-testid="stTextArea"] textarea {
        background: #112240 !important;
        border: 1px solid #1E3A5F !important;
        border-radius: 4px !important;
        color: #F0F4F8 !important;
        font-family: 'Inter', sans-serif;
        caret-color: #C9A84C;
    }
    div[data-testid="stTextArea"] textarea::placeholder {
        color: #4D6478 !important;
        opacity: 1 !important;
    }
    div[data-testid="stTextArea"] textarea:focus {
        border-color: #C9A84C !important;
        box-shadow: 0 0 0 2px rgba(201,168,76,0.15) !important;
        outline: none !important;
    }

    /* ── FIX 2: Text input — typed text and placeholder both readable ── */
    div[data-testid="stTextInput"] input {
        background: #112240 !important;
        border: 1px solid #1E3A5F !important;
        border-radius: 4px !important;
        color: #F0F4F8 !important;
        font-family: 'Inter', sans-serif;
        caret-color: #C9A84C;
    }
    div[data-testid="stTextInput"] input::placeholder {
        color: #4D6478 !important;
        opacity: 1 !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #C9A84C !important;
        box-shadow: 0 0 0 2px rgba(201,168,76,0.15) !important;
        outline: none !important;
    }

    /* ── Widget labels ── */
    label[data-testid="stWidgetLabel"] p {
        color: #8899AA !important;
        font-size: 0.85rem !important;
    }

    /* ── Audio recorder ── */
    div[data-testid="stAudio"],
    div[data-testid="stAudioInput"] {
        background: #112240;
        border: 1px solid #1E3A5F;
        border-radius: 4px;
        padding: 0.5rem 1rem;
    }

    /* ── Submit button ── */
    div.stButton > button[kind="primary"] {
        width: 100%;
        height: 3.2rem;
        background: #C9A84C !important;
        color: #0A1628 !important;
        font-family: 'DM Sans', sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        border: none !important;
        border-radius: 4px;
        letter-spacing: 0.04em;
        transition: opacity 0.15s ease;
    }
    div.stButton > button[kind="primary"]:hover {
        opacity: 0.88;
    }
    div.stButton > button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid #1E3A5F !important;
        color: #8899AA !important;
        border-radius: 4px;
    }

    /* ── Success card ── */
    div[data-testid="stAlert"][data-baseweb="notification"] {
        background: #0D2137 !important;
        border-left: 3px solid #C9A84C !important;
        border-radius: 4px !important;
        color: #D8E4F0 !important;
    }

    /* ── Image preview ── */
    div[data-testid="stImage"] img {
        border-radius: 4px;
        border: 1px solid #1E3A5F;
    }

    /* ── Caption / small text ── */
    div[data-testid="stCaptionContainer"] p,
    .stCaption {
        color: #4D6478 !important;
        font-size: 0.78rem !important;
    }

    /* ── Divider ── */
    hr {
        border-color: #1E3A5F !important;
        margin: 2rem 0 !important;
    }

    /* ── Top header bar ── */
    header[data-testid="stHeader"] { background: #0A1628 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<p class="portal-wordmark">Municipal Services — CleanCity Copilot</p>', unsafe_allow_html=True)
st.markdown('<h1 class="portal-title">Report a Civic Issue</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="portal-subtitle">Submit reports for garbage accumulation, road damage, or sewerage overflow. '
    'All submissions are triaged by AI and routed to the relevant municipal department.</p>',
    unsafe_allow_html=True,
)

if "last_ticket" not in st.session_state:
    st.session_state.last_ticket = None

# ── Success state ───────────────────────────────────────────────────────────────
if st.session_state.last_ticket:
    ticket = st.session_state.last_ticket
    st.success(
        f"Report received. Tracking reference: **{ticket['ticket_id']}**\n\n"
        "The municipal team will review and dispatch a field crew based on AI-assessed priority. "
        "Keep this reference number to track your submission."
    )
    if ticket.get("mock"):
        st.caption("Demo mode — backend not connected. This is a placeholder reference number.")
    if st.button("Submit another report", type="secondary"):
        st.session_state.last_ticket = None
        st.rerun()
    st.stop()

# ── Section 1: Photo ────────────────────────────────────────────────────────────
st.markdown('<p class="form-section-label">Section 1 — Photographic Evidence</p>', unsafe_allow_html=True)
image_file = st.file_uploader(
    "Upload a photograph of the problem area",
    type=["jpg", "jpeg", "png"],
    help="A clear, well-lit photograph significantly improves AI classification accuracy.",
)
if image_file:
    st.image(image_file, caption="Uploaded image — verify this shows the issue clearly.", use_container_width=True)

# ── Section 2: Description ──────────────────────────────────────────────────────
st.markdown('<p class="form-section-label">Section 2 — Description</p>', unsafe_allow_html=True)
st.caption("Provide a voice note or a written description. Voice input (Urdu / Roman Urdu / English) is transcribed automatically.")

audio_file = st.audio_input("Record a voice note")

description = st.text_area(
    "Written description",
    placeholder="Describe the issue, its location within the area, and how long it has been present.",
    height=96,
)

# ── Section 3: Location ─────────────────────────────────────────────────────────
st.markdown('<p class="form-section-label">Section 3 — Location</p>', unsafe_allow_html=True)

col_addr, col_gps = st.columns([4, 1])
with col_addr:
    address = st.text_input(
        "Street address or named area",
        placeholder="e.g. Latifabad Unit 9, Hyderabad",
    )
with col_gps:
    st.markdown("<div style='height:1.7rem'></div>", unsafe_allow_html=True)
    use_gps = st.button("GPS", help="Auto-detect current location")

lat, lng = None, None
if use_gps:
    st.info(
        "Automatic GPS detection requires the streamlit-geolocation component. "
        "Please enter the address manually until that integration is configured."
    )

st.divider()

# ── Submit ──────────────────────────────────────────────────────────────────────
can_submit = bool(image_file) and bool(address.strip())
if not can_submit:
    st.caption("A photograph and a location are required before submission.")

if st.button("Submit Report", disabled=not can_submit, type="primary"):
    with st.spinner("Transmitting report to municipal AI pipeline..."):
        result = submit_report(
            image_file=image_file,
            audio_file=audio_file,
            description=description,
            lat=lat,
            lng=lng,
            address=address,
        )
    if result.get("success"):
        st.session_state.last_ticket = result
        st.rerun()
    else:
        st.error(f"Submission failed: {result.get('message', 'An unexpected error occurred. Please try again.')}")

st.divider()
st.caption("CleanCity Copilot · Citizen Reporting Portal · Alibaba Cloud AI Hackathon 2026")
