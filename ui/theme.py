"""EXAMFLOW shared Navy & Ice Blue theme with comprehensive contrast fixes."""

from __future__ import annotations

import streamlit as st


THEMES = {
    "Light": {
        "page": "#F4F7FB",
        "surface": "#FFFFFF",
        "surface_alt": "#EAF3FC",
        "text": "#142B4A",
        "muted": "#52657D",
        "border": "#D9E4F0",
        "primary": "#2878C8",
        "primary_hover": "#1D65AC",
        "sidebar": "#EBF2FA",
        "sidebar_text": "#142B4A",
        "sidebar_muted": "#4B617D",
        "sidebar_border": "#CADCED",
        "sidebar_btn_bg": "#FFFFFF",
        "sidebar_btn_border": "#CADCED",
        "input": "#FFFFFF",
        "shadow": "0 2px 12px rgba(20,43,74,.06)",
        "tag_bg": "#DCEBFA",
        "tag_border": "#B9D4F0",
        "tag_text": "#142B4A",
    },
    "Dark": {
        "page": "#101B2A",
        "surface": "#17263A",
        "surface_alt": "#203650",
        "text": "#EDF5FF",
        "muted": "#B2C2D5",
        "border": "#344B65",
        "primary": "#69A9EA",
        "primary_hover": "#8BBDF0",
        "sidebar": "#0B1522",
        "sidebar_text": "#EDF5FF",
        "sidebar_muted": "#8EA6C2",
        "sidebar_border": "#1E2D40",
        "sidebar_btn_bg": "#17263A",
        "sidebar_btn_border": "#344B65",
        "input": "#203650",
        "shadow": "0 2px 12px rgba(0,0,0,.18)",
        "tag_bg": "#203650",
        "tag_border": "#344B65",
        "tag_text": "#EDF5FF",
    },
}


def save_appearance():
    """Save the selected appearance preference."""
    st.session_state["examflow_appearance"] = (
        st.session_state["_examflow_appearance_widget"]
    )


def apply_theme() -> str:
    """Apply the saved theme consistently across all pages."""

    # Initialize the saved preference.
    if "examflow_appearance" not in st.session_state:
        st.session_state["examflow_appearance"] = "Light"

    # Always synchronize the selector with the saved preference.
    st.session_state["_examflow_appearance_widget"] = (
        st.session_state["examflow_appearance"]
    )

    st.logo(
        "ui/examflow_logo.svg",
        size="large",
    )

    with st.sidebar:
        st.markdown(
            '<div class="exam-appearance-label">APPEARANCE</div>',
            unsafe_allow_html=True,
        )

        st.radio(
            "Appearance",
            ["Light", "Dark"],
            horizontal=True,
            key="_examflow_appearance_widget",
            on_change=save_appearance,
            label_visibility="collapsed",
        )

        st.markdown(
            '<div class="exam-sidebar-rule"></div>',
            unsafe_allow_html=True,
        )

    # Read the currently selected theme.
    mode = st.session_state["examflow_appearance"]
    c = THEMES[mode]

    css = f"""
    <style>

    :root {{
        --exam-page: {c['page']};
        --exam-surface: {c['surface']};
        --exam-surface-alt: {c['surface_alt']};
        --exam-text: {c['text']};
        --exam-muted: {c['muted']};
        --exam-border: {c['border']};
        --exam-primary: {c['primary']};
        --exam-primary-hover: {c['primary_hover']};
        --exam-input: {c['input']};
        --exam-shadow: {c['shadow']};
        --exam-tag-bg: {c['tag_bg']};
        --exam-tag-border: {c['tag_border']};
        --exam-tag-text: {c['tag_text']};
        --exam-sidebar-bg: {c['sidebar']};
        --exam-sidebar-text: {c['sidebar_text']};
        --exam-sidebar-muted: {c['sidebar_muted']};
        --exam-sidebar-border: {c['sidebar_border']};
        --exam-sidebar-btn-bg: {c['sidebar_btn_bg']};
        --exam-sidebar-btn-border: {c['sidebar_btn_border']};
    }}

    /* Main application background & text */
    html, body, [data-testid="stAppViewContainer"] {{
        background: var(--exam-page) !important;
        color: var(--exam-text) !important;
    }}

    [data-testid="stHeader"] {{
        background: transparent !important;
    }}

    .main .block-container {{
        max-width: 1500px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }}

    /* Sidebar Background and Container */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"],
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div {{
        background: var(--exam-sidebar-bg) !important;
        background-color: var(--exam-sidebar-bg) !important;
        border-right: 1px solid var(--exam-sidebar-border) !important;
    }}

    /* Sidebar Headings, Text, Labels */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5,
    [data-testid="stSidebar"] h6 {{
        color: var(--exam-sidebar-text) !important;
        font-weight: 700 !important;
    }}

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] li,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {{
        color: var(--exam-sidebar-text) !important;
    }}

    [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] caption {{
        color: var(--exam-sidebar-muted) !important;
        font-size: 13px !important;
    }}

    /* Sidebar Appearance Section */
    .exam-appearance-label {{
        color: var(--exam-sidebar-muted) !important;
        font-size: 11px !important;
        font-weight: 750 !important;
        letter-spacing: 1px !important;
        margin-bottom: 5px !important;
    }}

    .exam-sidebar-rule {{
        border-top: 1px solid var(--exam-sidebar-border) !important;
        margin: 12px 0 14px !important;
    }}

    /* Sidebar Radio Buttons (Light/Dark) */
    [data-testid="stSidebar"] [data-testid="stRadio"] label,
    [data-testid="stSidebar"] [data-testid="stRadio"] label p,
    [data-testid="stSidebar"] [data-testid="stRadio"] label span,
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] * {{
        color: var(--exam-sidebar-text) !important;
        font-weight: 600 !important;
    }}

    /* Sidebar Normal Buttons */
    [data-testid="stSidebar"] .stButton button,
    [data-testid="stSidebar"] [data-testid="stButton"] button,
    [data-testid="stSidebar"] [data-testid*="stBaseButton-secondary"],
    [data-testid="stSidebar"] [data-testid*="baseButton-secondary"],
    [data-testid="stSidebar"] button[kind="secondary"] {{
        background: var(--exam-sidebar-btn-bg) !important;
        background-color: var(--exam-sidebar-btn-bg) !important;
        color: var(--exam-sidebar-text) !important;
        -webkit-text-fill-color: var(--exam-sidebar-text) !important;
        border: 1px solid var(--exam-sidebar-btn-border) !important;
        border-radius: 9px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
        font-weight: 650 !important;
    }}

    [data-testid="stSidebar"] .stButton button *,
    [data-testid="stSidebar"] [data-testid="stButton"] button *,
    [data-testid="stSidebar"] [data-testid*="stBaseButton-secondary"] *,
    [data-testid="stSidebar"] [data-testid*="baseButton-secondary"] *,
    [data-testid="stSidebar"] button[kind="secondary"] * {{
        color: var(--exam-sidebar-text) !important;
        -webkit-text-fill-color: var(--exam-sidebar-text) !important;
    }}

    [data-testid="stSidebar"] .stButton button:hover,
    [data-testid="stSidebar"] [data-testid="stButton"] button:hover,
    [data-testid="stSidebar"] button[kind="secondary"]:hover {{
        border-color: var(--exam-primary) !important;
        color: var(--exam-primary) !important;
        -webkit-text-fill-color: var(--exam-primary) !important;
    }}

    [data-testid="stSidebar"] .stButton button:hover *,
    [data-testid="stSidebar"] [data-testid="stButton"] button:hover *,
    [data-testid="stSidebar"] button[kind="secondary"]:hover * {{
        color: var(--exam-primary) !important;
        -webkit-text-fill-color: var(--exam-primary) !important;
    }}

    /* Sidebar Primary Button (e.g. 🚀 Auto-Plan Exam) */
    [data-testid="stSidebar"] .stButton button[kind="primary"],
    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"],
    [data-testid="stSidebar"] [data-testid*="stBaseButton-primary"],
    [data-testid="stSidebar"] [data-testid*="baseButton-primary"],
    [data-testid="stSidebar"] button[kind="primary"] {{
        background: var(--exam-primary) !important;
        background-color: var(--exam-primary) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: 1px solid var(--exam-primary) !important;
        font-weight: 700 !important;
    }}

    [data-testid="stSidebar"] .stButton button[kind="primary"] *,
    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] *,
    [data-testid="stSidebar"] [data-testid*="stBaseButton-primary"] *,
    [data-testid="stSidebar"] [data-testid*="baseButton-primary"] *,
    [data-testid="stSidebar"] button[kind="primary"] * {{
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }}

    /* Sidebar Navigation Links */
    [data-testid="stSidebarNav"] a {{
        border-radius: 9px !important;
        margin: 3px 8px !important;
        padding: 9px 12px !important;
        color: var(--exam-sidebar-text) !important;
        font-weight: 550 !important;
    }}

    [data-testid="stSidebarNav"] a:not([aria-current="page"]) * {{
        color: var(--exam-sidebar-text) !important;
    }}

    [data-testid="stSidebarNav"] a:hover {{
        background: rgba(40,120,200,.14) !important;
    }}

    [data-testid="stSidebarNav"] a[aria-current="page"] {{
        background: var(--exam-primary) !important;
        color: #FFFFFF !important;
        font-weight: 750 !important;
    }}

    [data-testid="stSidebarNav"] a[aria-current="page"] * {{
        color: #FFFFFF !important;
    }}

    /* Hide 'app' and 'About' pages from sidebar navigation */
    [data-testid="stSidebarNav"] ul li:first-child,
    [data-testid="stSidebarNav"] li:has(a[href=""]),
    [data-testid="stSidebarNav"] li:has(a[href="/"]),
    [data-testid="stSidebarNav"] li:has(a[href$="app"]),
    [data-testid="stSidebarNav"] li:has(a[href$="/app"]),
    [data-testid="stSidebarNav"] li:has(a[href*="/app/"]),
    [data-testid="stSidebarNav"] li:has(a[href*="About"]),
    [data-testid="stSidebarNav"] li:has(a[href*="about"]),
    [data-testid="stSidebarNav"] li:has(a[href*="10_About"]),
    [data-testid="stSidebarNavLink"][href=""],
    [data-testid="stSidebarNavLink"][href="/"],
    [data-testid="stSidebarNavLink"][href$="app"],
    [data-testid="stSidebarNavLink"][href$="/app"],
    [data-testid="stSidebarNavLink"][href*="About"],
    [data-testid="stSidebarNavLink"][href*="about"],
    [data-testid="stSidebarNavLink"][href*="10_About"],
    [data-testid="stSidebarNavLinkContainer"]:has(a[href=""]),
    [data-testid="stSidebarNavLinkContainer"]:has(a[href="/"]),
    [data-testid="stSidebarNavLinkContainer"]:has(a[href$="app"]),
    [data-testid="stSidebarNavLinkContainer"]:has(a[href*="About"]),
    [data-testid="stSidebarNavLinkContainer"]:has(a[href*="about"]),
    [data-testid="stSidebarNavLinkContainer"]:has(a[href*="10_About"]) {{
        display: none !important;
    }}

    /* Headings and typography */
    h1, h2, h3, h4, h5, h6 {{
        color: var(--exam-text) !important;
    }}

    h1 {{
        font-size: 1.85rem !important;
        font-weight: 750 !important;
        letter-spacing: -.025em;
    }}

    h2 {{
        font-size: 1.35rem !important;
        font-weight: 700 !important;
    }}

    h3 {{
        font-size: 1.1rem !important;
        font-weight: 650 !important;
    }}

    .main-header {{
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: var(--exam-text) !important;
        margin-bottom: 0.2rem !important;
    }}

    .sub-header {{
        font-size: 1.15rem !important;
        font-weight: 500 !important;
        color: var(--exam-muted) !important;
        margin-bottom: 1.2rem !important;
    }}

    p, li, label, span {{
        color: var(--exam-text);
    }}

    [data-testid="stMarkdownContainer"] {{
        color: var(--exam-text);
    }}

    [data-testid="stCaptionContainer"],
    .stCaption {{
        color: var(--exam-muted) !important;
    }}

    /* Metric cards */
    [data-testid="stMetric"] {{
        background: var(--exam-surface) !important;
        border: 1px solid var(--exam-border);
        border-radius: 12px;
        padding: 17px 18px;
        box-shadow: var(--exam-shadow);
    }}

    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] * {{
        color: var(--exam-muted) !important;
    }}

    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {{
        color: var(--exam-text) !important;
    }}

    /* Containers and cards */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: var(--exam-surface) !important;
        border-color: var(--exam-border) !important;
        border-radius: 12px;
    }}

    /* All Text Inputs */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input,
    [data-testid="stTimeInput"] input,
    [data-testid="stTextArea"] textarea,
    input[type="text"],
    input[type="number"],
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {{
        background: var(--exam-input) !important;
        color: var(--exam-text) !important;
        -webkit-text-fill-color: var(--exam-text) !important;
        border: 1px solid var(--exam-border) !important;
        border-radius: 9px !important;
    }}

    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stTextArea"] textarea::placeholder {{
        color: var(--exam-muted) !important;
        -webkit-text-fill-color: var(--exam-muted) !important;
        opacity: 1 !important;
    }}

    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stNumberInput"] input:focus {{
        border-color: var(--exam-primary) !important;
    }}

    /* Selectbox and Multiselect */
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div {{
        background: var(--exam-input) !important;
        color: var(--exam-text) !important;
        border-color: var(--exam-border) !important;
        border-radius: 9px !important;
    }}

    [data-testid="stSelectbox"] [data-baseweb="select"] svg,
    [data-testid="stMultiSelect"] [data-baseweb="select"] svg {{
        color: var(--exam-text) !important;
        fill: currentColor !important;
    }}

    /* BaseWeb Multiselect Tags (Pills) */
    [data-baseweb="tag"] {{
        background: var(--exam-tag-bg) !important;
        border: 1px solid var(--exam-tag-border) !important;
        border-radius: 6px !important;
    }}

    [data-baseweb="tag"] * {{
        color: var(--exam-tag-text) !important;
        -webkit-text-fill-color: var(--exam-tag-text) !important;
    }}

    [data-baseweb="tag"] svg {{
        color: var(--exam-tag-text) !important;
        fill: var(--exam-tag-text) !important;
    }}

    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [data-baseweb="popover"] [role="listbox"] {{
        background: var(--exam-surface) !important;
        border: 1px solid var(--exam-border) !important;
    }}

    [role="option"] {{
        background: var(--exam-surface) !important;
        color: var(--exam-text) !important;
    }}

    [role="option"]:hover,
    [role="option"][aria-selected="true"] {{
        background: var(--exam-surface-alt) !important;
        color: var(--exam-text) !important;
    }}

    /* Tabs */
    [data-testid="stTabs"] [role="tab"] {{
        color: var(--exam-text) !important;
        font-weight: 650;
    }}

    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
        color: var(--exam-primary) !important;
        border-bottom-color: var(--exam-primary) !important;
    }}

    [data-testid="stTabs"] [role="tab"] * {{
        color: inherit !important;
    }}

    /* Buttons (Everywhere in Main Application) */
    .stButton button,
    [data-testid="stButton"] button,
    button[data-testid*="stBaseButton"],
    button[data-testid*="baseButton"],
    button[kind="secondary"],
    button[kind="tertiary"],
    [data-testid="stDownloadButton"] button {{
        background: var(--exam-surface) !important;
        background-color: var(--exam-surface) !important;
        color: var(--exam-text) !important;
        -webkit-text-fill-color: var(--exam-text) !important;
        border: 1.5px solid var(--exam-border) !important;
        border-radius: 9px !important;
        min-height: 2.55rem !important;
        font-weight: 650 !important;
    }}

    .stButton button *,
    [data-testid="stButton"] button *,
    button[data-testid*="stBaseButton"] *,
    button[data-testid*="baseButton"] *,
    button[kind="secondary"] *,
    button[kind="tertiary"] *,
    [data-testid="stDownloadButton"] button * {{
        color: var(--exam-text) !important;
        -webkit-text-fill-color: var(--exam-text) !important;
    }}

    .stButton button:hover,
    [data-testid="stButton"] button:hover,
    button[data-testid*="stBaseButton"]:hover,
    button[data-testid*="baseButton"]:hover,
    button[kind="secondary"]:hover,
    [data-testid="stDownloadButton"] button:hover {{
        background: var(--exam-surface-alt) !important;
        background-color: var(--exam-surface-alt) !important;
        border-color: var(--exam-primary) !important;
        color: var(--exam-primary) !important;
        -webkit-text-fill-color: var(--exam-primary) !important;
    }}

    .stButton button:hover *,
    [data-testid="stButton"] button:hover *,
    button[data-testid*="stBaseButton"]:hover *,
    button[data-testid*="baseButton"]:hover *,
    button[kind="secondary"]:hover *,
    [data-testid="stDownloadButton"] button:hover * {{
        color: var(--exam-primary) !important;
        -webkit-text-fill-color: var(--exam-primary) !important;
    }}

    .stButton button[kind="primary"],
    [data-testid="stButton"] button[kind="primary"],
    button[data-testid*="stBaseButton-primary"],
    button[data-testid*="baseButton-primary"],
    button[kind="primary"] {{
        background: var(--exam-primary) !important;
        background-color: var(--exam-primary) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: 1.5px solid var(--exam-primary) !important;
        border-radius: 9px !important;
        font-weight: 700 !important;
    }}

    .stButton button[kind="primary"] *,
    [data-testid="stButton"] button[kind="primary"] *,
    button[data-testid*="stBaseButton-primary"] *,
    button[data-testid*="baseButton-primary"] *,
    button[kind="primary"] * {{
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }}

    .stButton button[kind="primary"]:hover,
    [data-testid="stButton"] button[kind="primary"]:hover,
    button[data-testid*="stBaseButton-primary"]:hover,
    button[data-testid*="baseButton-primary"]:hover,
    button[kind="primary"]:hover {{
        background: var(--exam-primary-hover) !important;
        background-color: var(--exam-primary-hover) !important;
        border-color: var(--exam-primary-hover) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }}

    /* Disabled button state (preserves contrast, prevents washed out white-on-white) */
    .stButton button:disabled,
    [data-testid="stButton"] button:disabled,
    button[data-testid*="stBaseButton"]:disabled,
    button[data-testid*="baseButton"]:disabled,
    button[disabled] {{
        background: var(--exam-surface) !important;
        background-color: var(--exam-surface) !important;
        color: var(--exam-muted) !important;
        -webkit-text-fill-color: var(--exam-muted) !important;
        border-color: var(--exam-border) !important;
        opacity: 0.65 !important;
        cursor: not-allowed !important;
    }}

    .stButton button:disabled *,
    [data-testid="stButton"] button:disabled *,
    button[data-testid*="stBaseButton"]:disabled *,
    button[data-testid*="baseButton"]:disabled *,
    button[disabled] * {{
        color: var(--exam-muted) !important;
        -webkit-text-fill-color: var(--exam-muted) !important;
    }}

    /* Alerts (Info, Warning, Error, Success) */
    [data-testid="stAlert"] {{
        background: var(--exam-surface-alt) !important;
        border: 1px solid var(--exam-border) !important;
        border-radius: 10px !important;
    }}

    [data-testid="stAlert"] [data-testid="stMarkdownContainer"] *,
    [data-testid="stAlert"] p,
    [data-testid="stAlert"] li,
    [data-testid="stAlert"] span {{
        color: var(--exam-text) !important;
    }}

    /* Chat Messages in Copilot */
    [data-testid="stChatMessage"] {{
        background: var(--exam-surface) !important;
        border: 1px solid var(--exam-border) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin-bottom: 0.75rem !important;
        box-shadow: var(--exam-shadow) !important;
    }}

    /* Chat message avatars (prevent washed-out white box in dark mode) */
    [data-testid="stChatMessage"] [data-testid*="Avatar"],
    [data-testid="stChatMessage"] [data-testid*="avatar"],
    [data-testid="stChatMessageAvatar"],
    [data-testid="stChatMessageAvatarCustom"],
    [data-testid="stChatMessageAvatarUser"],
    [data-testid="stChatMessageAvatarAssistant"],
    div[data-testid*="chatAvatarIcon"] {{
        background: var(--exam-surface-alt) !important;
        background-color: var(--exam-surface-alt) !important;
        border: 1px solid var(--exam-border) !important;
        border-radius: 9px !important;
    }}

    [data-testid="stChatMessage"] [data-testid*="Avatar"] svg,
    [data-testid="stChatMessage"] [data-testid*="Avatar"] *,
    [data-testid="stChatMessageAvatar"] svg,
    div[data-testid*="chatAvatarIcon"] svg {{
        color: var(--exam-primary) !important;
        fill: var(--exam-primary) !important;
        stroke: var(--exam-primary) !important;
    }}

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] * {{
        color: var(--exam-text) !important;
    }}

    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] div {{
        color: var(--exam-text) !important;
    }}

    [data-testid="stChatMessage"] code {{
        background: var(--exam-tag-bg) !important;
        color: var(--exam-tag-text) !important;
        border: 1px solid var(--exam-tag-border) !important;
        padding: 2px 7px !important;
        border-radius: 5px !important;
        font-weight: 700 !important;
    }}

    /* Chat Input Bar & Bottom Container */
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"],
    .stBottom,
    .stBottom > div,
    div[class*="stBottom"],
    div[class*="e87roqt3"],
    div[class*="e87roqt4"],
    div[class*="e87roqt"] {{
        background: var(--exam-page) !important;
        background-color: var(--exam-page) !important;
    }}

    [data-testid="stChatInput"],
    .stChatInput {{
        background: var(--exam-surface) !important;
        background-color: var(--exam-surface) !important;
        border: 1.5px solid var(--exam-border) !important;
        border-radius: 12px !important;
        box-shadow: var(--exam-shadow) !important;
        overflow: hidden !important;
    }}

    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] > div > div,
    .stChatInput > div,
    div[class*="e17zv8n20"],
    div[class*="e17zv8n21"],
    div[class*="e17zv8n23"],
    div[class*="e17zv8n24"],
    div[class*="e17zv8n25"],
    div[class*="e17zv8n26"],
    div[class*="e17zv8n27"],
    div[class*="e17zv8n28"] {{
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
    }}

    [data-testid="stChatInput"]:focus-within,
    .stChatInput:focus-within {{
        border-color: var(--exam-primary) !important;
        box-shadow: 0 0 0 2px rgba(40, 120, 200, 0.25) !important;
    }}

    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInputTextArea"],
    textarea[data-testid="stChatInputTextArea"],
    .stChatInput textarea,
    textarea[class*="e17zv8n"] {{
        background: transparent !important;
        background-color: transparent !important;
        color: var(--exam-text) !important;
        -webkit-text-fill-color: var(--exam-text) !important;
        caret-color: var(--exam-primary) !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        opacity: 1 !important;
    }}

    [data-testid="stChatInput"] textarea::placeholder,
    [data-testid="stChatInputTextArea"]::placeholder,
    .stChatInput textarea::placeholder {{
        color: var(--exam-muted) !important;
        -webkit-text-fill-color: var(--exam-muted) !important;
        opacity: 0.85 !important;
    }}

    [data-testid="stChatInputSubmitButton"],
    [data-testid="stChatInput"] button,
    button[class*="e17zv8n29"] {{
        background: var(--exam-primary) !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
    }}

    [data-testid="stChatInputSubmitButton"] svg,
    [data-testid="stChatInput"] button svg {{
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }}

    /* DataFrames and Tables */
    [data-testid="stDataFrame"],
    [data-testid="stTable"] {{
        background: var(--exam-surface) !important;
        border: 1px solid var(--exam-border) !important;
        border-radius: 10px !important;
    }}

    table {{
        color: var(--exam-text) !important;
    }}

    th {{
        background: var(--exam-surface-alt) !important;
        color: var(--exam-text) !important;
        font-weight: 700 !important;
        border-bottom: 2px solid var(--exam-border) !important;
    }}

    td {{
        color: var(--exam-text);
        border: 1px solid var(--exam-border);
    }}

    /* JSON Viewer */
    [data-testid="stJson"] {{
        background: var(--exam-surface-alt) !important;
        border: 1px solid var(--exam-border) !important;
        border-radius: 9px !important;
        padding: 10px !important;
    }}

    [data-testid="stJson"] * {{
        color: var(--exam-text) !important;
    }}

    /* Code Blocks (st.code, pre, and syntax highlighter) */
    .stCode,
    [data-testid="stCode"],
    [data-testid="stCodeBlock"],
    [data-testid="stCodeUnhighlighted"],
    div[class*="stCode"] {{
        background: var(--exam-surface-alt) !important;
        background-color: var(--exam-surface-alt) !important;
        border: 1px solid var(--exam-border) !important;
        border-radius: 9px !important;
    }}

    .stCode pre,
    [data-testid="stCode"] pre,
    [data-testid="stCodeBlock"] pre,
    [data-testid="stCodeUnhighlighted"] pre,
    div[class*="stCode"] pre,
    pre {{
        background: var(--exam-surface-alt) !important;
        background-color: var(--exam-surface-alt) !important;
        color: var(--exam-text) !important;
        -webkit-text-fill-color: var(--exam-text) !important;
        border: none !important;
        border-radius: 9px !important;
    }}

    .stCode code,
    .stCode pre code,
    .stCode span,
    [data-testid="stCode"] code,
    [data-testid="stCode"] pre code,
    [data-testid="stCode"] span,
    [data-testid="stCodeBlock"] code,
    [data-testid="stCodeBlock"] span,
    [data-testid="stCodeUnhighlighted"] *,
    div[class*="stCode"] code,
    div[class*="stCode"] span,
    pre code,
    pre span {{
        color: var(--exam-text) !important;
        -webkit-text-fill-color: var(--exam-text) !important;
        background: transparent !important;
        background-color: transparent !important;
    }}

    /* Copy button inside code block */
    [data-testid="stCode"] button,
    .stCode button {{
        background: var(--exam-surface) !important;
        background-color: var(--exam-surface) !important;
        color: var(--exam-text) !important;
        -webkit-text-fill-color: var(--exam-text) !important;
        border: 1px solid var(--exam-border) !important;
    }}

    [data-testid="stCode"] button svg,
    .stCode button svg {{
        color: var(--exam-muted) !important;
        fill: var(--exam-muted) !important;
    }}

    /* Inline code in markdown */
    code:not(pre code),
    [data-testid="stMarkdownContainer"] code:not(pre code),
    p code,
    li code {{
        background: var(--exam-tag-bg) !important;
        background-color: var(--exam-tag-bg) !important;
        color: var(--exam-tag-text) !important;
        -webkit-text-fill-color: var(--exam-tag-text) !important;
        border: 1px solid var(--exam-tag-border) !important;
        border-radius: 6px !important;
        padding: 2px 7px !important;
        font-weight: 600 !important;
        font-size: 0.9em !important;
    }}

    /* Expanders */
    [data-testid="stExpander"] {{
        background: var(--exam-surface) !important;
        border: 1px solid var(--exam-border) !important;
        border-radius: 10px !important;
        overflow: hidden;
    }}

    [data-testid="stExpander"] details {{
        background: var(--exam-surface) !important;
    }}

    [data-testid="stExpander"] summary {{
        background: var(--exam-surface-alt) !important;
        color: var(--exam-text) !important;
    }}

    [data-testid="stExpander"] summary *,
    [data-testid="stExpander"] summary svg {{
        color: var(--exam-text) !important;
        stroke: currentColor;
    }}

    [data-testid="stExpander"] details > div {{
        color: var(--exam-text) !important;
    }}

    /* File Uploader Dropzone */
    [data-testid="stFileUploader"] {{
        background: var(--exam-surface) !important;
        border: 1px solid var(--exam-border);
        border-radius: 10px;
        padding: 10px;
    }}

    [data-testid="stFileUploaderDropzone"] {{
        background: var(--exam-surface-alt) !important;
        border: 1px dashed var(--exam-border) !important;
        border-radius: 10px !important;
    }}

    [data-testid="stFileUploaderDropzone"] *,
    [data-testid="stFileUploaderDropzoneInstructions"] * {{
        color: var(--exam-text) !important;
    }}

    [data-testid="stFileUploaderDropzone"] button {{
        background: var(--exam-primary) !important;
        color: #FFFFFF !important;
    }}

    [data-testid="stFileUploaderDropzone"] button * {{
        color: #FFFFFF !important;
    }}

    /* Checkbox & Radio Labels */
    [data-testid="stCheckbox"] label *,
    [data-testid="stRadio"] label * {{
        color: var(--exam-text);
    }}

    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p {{
        color: var(--exam-text) !important;
    }}

    /* Tooltips */
    [data-testid="stTooltipIcon"] svg,
    [data-testid="stWidgetLabel"] svg,
    [data-testid="stMetricLabel"] svg {{
        color: var(--exam-muted) !important;
        stroke: var(--exam-muted) !important;
    }}

    /* Dividers and links */
    hr {{
        border-color: var(--exam-border) !important;
    }}

    a {{
        color: var(--exam-primary);
    }}

    /* Mobile layout */
    @media (max-width: 768px) {{
        .main .block-container {{
            padding-top: 1rem;
        }}
        h1 {{
            font-size: 1.5rem !important;
        }}
    }}

    /* Logo */
    [data-testid="stSidebarHeader"] [data-testid="stLogo"] {{
        width: 100% !important;
        max-width: 320px !important;
    }}

    [data-testid="stSidebarHeader"] img {{
        width: 100% !important;
        max-width: 320px !important;
        height: auto !important;
        max-height: none !important;
        object-fit: contain !important;
    }}

    </style>
    """

    st.markdown(css, unsafe_allow_html=True)

    return mode
