
"""EXAMFLOW shared Navy & Ice Blue theme."""

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
        "sidebar": "#142B4A",
        "sidebar_text": "#EAF3FC",
        "input": "#FFFFFF",
        "shadow": "0 2px 12px rgba(20,43,74,.06)",
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
        "sidebar_text": "#EAF3FC",
        "input": "#203650",
        "shadow": "0 2px 12px rgba(0,0,0,.18)",
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
    }}

    /* Main application background */

    html, body, [data-testid="stAppViewContainer"] {{
        background: var(--exam-page) !important;
        color: var(--exam-text) !important;
    }}

    [data-testid="stHeader"] {{
        background: transparent !important;
    }}

    .main .block-container {{
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }}

    /* Sidebar */

    [data-testid="stSidebar"] {{
        background: {c['sidebar']} !important;
        border-right: 1px solid rgba(255,255,255,.08);
    }}

    [data-testid="stSidebar"] * {{
        color: {c['sidebar_text']};
    }}

    [data-testid="stSidebarNav"] {{
        padding-top: .35rem;
    }}

    [data-testid="stSidebarNav"] a {{
        border-radius: 9px;
        margin: 3px 8px;
        padding: 9px 12px;
    }}

    [data-testid="stSidebarNav"] a:hover {{
        background: rgba(105,169,234,.16);
    }}

    [data-testid="stSidebarNav"] a[aria-current="page"] {{
        background: rgba(40,120,200,.35);
        font-weight: 700;
    }}

    .exam-appearance-label {{
        color: #B9D4F0 !important;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }}

    .exam-sidebar-rule {{
        border-top: 1px solid rgba(255,255,255,.17);
        margin: 12px 0 14px;
    }}

    /* Headings and general text */

    h1, h2, h3, h4, h5, h6 {{
        color: var(--exam-text) !important;
    }}

    h1 {{
        font-size: 1.9rem !important;
        font-weight: 750 !important;
        letter-spacing: -.025em;
    }}

    h2 {{
        font-size: 1.35rem !important;
        font-weight: 700 !important;
    }}

    h3 {{
        font-size: 1.08rem !important;
        font-weight: 650 !important;
    }}

    p, li, label {{
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

    /* Text inputs and text areas */

    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input,
    [data-testid="stTimeInput"] input,
    [data-testid="stTextArea"] textarea {{
        background: var(--exam-input) !important;
        color: var(--exam-text) !important;
        border: 1px solid var(--exam-border);
        border-radius: 9px;
    }}

    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stTextArea"] textarea::placeholder {{
        color: var(--exam-muted) !important;
        opacity: 1;
    }}

    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {{
        border-color: var(--exam-primary) !important;
    }}

    /* Select boxes and dropdowns */

    [data-testid="stSelectbox"] [data-baseweb="select"],
    [data-testid="stMultiSelect"] [data-baseweb="select"] {{
        background: var(--exam-input) !important;
        color: var(--exam-text) !important;
    }}

    [data-baseweb="popover"],
    [data-baseweb="menu"] {{
        background: var(--exam-surface) !important;
    }}

    [role="option"] {{
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

    /* Buttons */

    .stButton > button,
    [data-testid="stDownloadButton"] button {{
        background: var(--exam-surface) !important;
        color: var(--exam-text) !important;
        border: 1px solid var(--exam-border) !important;
        border-radius: 9px;
        min-height: 2.55rem;
        font-weight: 650;
    }}

    .stButton > button[kind="primary"],
    [data-testid="stDownloadButton"] button {{
        background: var(--exam-primary) !important;
        color: white !important;
        border-color: var(--exam-primary) !important;
    }}

    .stButton > button:hover,
    [data-testid="stDownloadButton"] button:hover {{
        border-color: var(--exam-primary) !important;
    }}

    /* File uploader */

    [data-testid="stFileUploader"] {{
        background: var(--exam-surface) !important;
        border: 1px solid var(--exam-border);
        border-radius: 10px;
        padding: 10px;
    }}

    [data-testid="stFileUploader"] section {{
        background: var(--exam-surface-alt) !important;
        border-radius: 8px;
    }}

    /* Tables */

    [data-testid="stDataFrame"],
    [data-testid="stTable"] {{
        background: var(--exam-surface);
        border: 1px solid var(--exam-border);
        border-radius: 10px;
        overflow: hidden;
    }}

    /* Alerts */

    [data-testid="stAlert"] {{
        border-radius: 10px;
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
            padding-top: 1.1rem;
        }}

        h1 {{
            font-size: 1.55rem !important;
        }}
    }}
        /* Make EXAMFLOW sidebar logo larger */
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

    
    /* -----------------------------------------------
       EXAMFLOW CONTRAST FIX
       File uploaders, expanders, buttons and controls
       ----------------------------------------------- */

    /* File uploader dropzone */

    [data-testid="stFileUploaderDropzone"] {{
        background: var(--exam-surface-alt) !important;
        border: 1px dashed var(--exam-border) !important;
        border-radius: 10px !important;
    }}

    [data-testid="stFileUploaderDropzone"] *,
    [data-testid="stFileUploaderDropzoneInstructions"],
    [data-testid="stFileUploaderDropzoneInstructions"] * {{
        color: var(--exam-text) !important;
    }}

    [data-testid="stFileUploaderDropzoneInstructions"] small,
    [data-testid="stFileUploaderDropzoneInstructions"] span {{
        color: var(--exam-muted) !important;
    }}

    /* Browse / Upload button inside file uploader */

    [data-testid="stFileUploaderDropzone"] button {{
        background: var(--exam-primary) !important;
        color: #FFFFFF !important;
        border: 1px solid var(--exam-primary) !important;
        border-radius: 8px !important;
    }}

    [data-testid="stFileUploaderDropzone"] button *,
    [data-testid="stFileUploaderDropzone"] button svg {{
        color: #FFFFFF !important;
        stroke: #FFFFFF !important;
    }}

    [data-testid="stFileUploaderDropzone"] button:hover {{
        background: var(--exam-primary-hover) !important;
    }}

    /* File upload labels and uploaded file names */

    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] span {{
        color: var(--exam-text);
    }}

    /* Expander header */

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
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary svg {{
        color: var(--exam-text) !important;
        stroke: currentColor;
    }}

    [data-testid="stExpander"] summary:hover {{
        background: var(--exam-surface-alt) !important;
    }}

    [data-testid="stExpander"] details > div {{
        color: var(--exam-text) !important;
    }}

    /* Button text and icons */

    .stButton > button *,
    [data-testid="stDownloadButton"] button * {{
        color: inherit !important;
    }}

    .stButton > button[kind="primary"] {{
        background: var(--exam-primary) !important;
        color: #FFFFFF !important;
    }}

    /* Selectbox and multiselect inner text */

    [data-testid="stSelectbox"] [data-baseweb="select"] *,
    [data-testid="stMultiSelect"] [data-baseweb="select"] * {{
        color: var(--exam-text) !important;
    }}

    /* Inputs and placeholders */

    [data-testid="stNumberInput"] button {{
        color: var(--exam-text) !important;
    }}

    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea {{
        -webkit-text-fill-color: var(--exam-text) !important;
    }}

    /* Tabs */

    [data-testid="stTabs"] [role="tab"] * {{
        color: inherit !important;
    }}

    /* Checkbox and radio labels */

    [data-testid="stCheckbox"] label *,
    [data-testid="stRadio"] label * {{
        color: var(--exam-text);
    }}

    /* Keep sidebar appearance selector readable */

    [data-testid="stSidebar"] [data-testid="stRadio"] label *,
    [data-testid="stSidebar"] [data-testid="stRadio"] p {{
        color: {c['sidebar_text']} !important;
    }}


    /* ================================================
       EXAMFLOW: LIGHT/DARK CONTROL CONTRAST FIX
       ================================================ */

    /* Help icons beside labels and metric titles */
    [data-testid="stTooltipIcon"],
    [data-testid="stTooltipIcon"] button,
    [data-testid="stTooltipIcon"] svg,
    [data-testid="stWidgetLabel"] svg,
    [data-testid="stMetricLabel"] svg {{
        color: var(--exam-muted) !important;
        stroke: var(--exam-muted) !important;
        opacity: 1 !important;
    }}

    /* Text and number input outer containers */
    [data-testid="stTextInput"] [data-baseweb="input"],
    [data-testid="stNumberInput"] [data-baseweb="input"],
    [data-testid="stDateInput"] [data-baseweb="input"],
    [data-testid="stTimeInput"] [data-baseweb="input"],
    [data-testid="stTextArea"] [data-baseweb="textarea"] {{
        background: var(--exam-input) !important;
        border: 1px solid var(--exam-border) !important;
        border-radius: 9px !important;
    }}

    /* Remove mismatched inner borders */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input,
    [data-testid="stTimeInput"] input,
    [data-testid="stTextArea"] textarea {{
        background: var(--exam-input) !important;
        color: var(--exam-text) !important;
        -webkit-text-fill-color: var(--exam-text) !important;
        border: none !important;
        outline: none !important;
    }}

    /* Number input plus/minus controls */
    [data-testid="stNumberInput"] button {{
        background: var(--exam-surface-alt) !important;
        color: var(--exam-text) !important;
        border-color: var(--exam-border) !important;
        opacity: 1 !important;
    }}

    [data-testid="stNumberInput"] button svg {{
        color: var(--exam-text) !important;
        stroke: var(--exam-text) !important;
        opacity: 1 !important;
    }}

    [data-testid="stNumberInput"] button:hover {{
        background: var(--exam-border) !important;
    }}

    /* Selectbox and multiselect backgrounds */
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

    /* Dropdown menu and options */
    [data-baseweb="popover"] [data-baseweb="menu"],
    [data-baseweb="popover"] [role="listbox"] {{
        background: var(--exam-surface) !important;
        color: var(--exam-text) !important;
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

    /* Form labels */
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p {{
        color: var(--exam-text) !important;
    }}

    /* Preserve readable sidebar appearance controls */
    [data-testid="stSidebar"] [data-testid="stRadio"] label *,
    [data-testid="stSidebar"] [data-testid="stRadio"] p {{
        color: {c['sidebar_text']} !important;
    }}


    </style>
    """

    st.markdown(css, unsafe_allow_html=True)

    return mode

