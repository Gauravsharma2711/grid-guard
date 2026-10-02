"""Grid-Guard Operational Streamlit Dashboard.

Primary user-facing operational interface for non-technical loss (NTL) detection,
dynamic Expected Net Value (ENV) inspection prioritization, and Tree-SHAP explainability.
Communicates strictly via the Grid-Guard FastAPI backend application boundary.
"""

from __future__ import annotations

import streamlit as st

from grid_guard.dashboard.api_client import DashboardApiError
from grid_guard.dashboard.state import get_api_client, init_session_state
from grid_guard.dashboard.views import (
    render_inspection_queue_view,
    render_meter_analysis_view,
    render_model_insights_view,
    render_overview_view,
    render_system_info_view,
)

# Page configuration
st.set_page_config(
    page_title="Grid-Guard — Smart Meter NTL Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Operational Data-Product Styling (Clean, professional, high-contrast)
st.markdown(
    """
    <style>
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 700;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        color: #555555;
    }
    /* Compact containers */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
    }
    /* Status pills */
    .status-badge-ok {
        background-color: #e6f4ea;
        color: #137333;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .status-badge-err {
        background-color: #fce8e6;
        color: #c5221f;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state
init_session_state()

# Sidebar Navigation & Backend Liveness
with st.sidebar:
    st.markdown("## ⚡ GRID-GUARD")
    st.caption("Financial-Aware NTL Detection Platform")

    # API Connection Check
    client = get_api_client()
    try:
        health = client.check_health()
        api_version = health.get("api_version", "1.0.0")
        st.markdown(
            f'<span class="status-badge-ok">🟢 API Online (v{api_version})</span>',
            unsafe_allow_html=True,
        )
    except DashboardApiError:
        st.markdown(
            '<span class="status-badge-err">🔴 API Disconnected</span>', unsafe_allow_html=True
        )
        st.caption(
            "FastAPI backend is offline. Run `uv run uvicorn grid_guard.api.main:app --port 8000`."
        )

    st.markdown("---")
    st.markdown("### Navigation")

    views = [
        "📊 Fleet Overview",
        "📋 Inspection Queue",
        "🔬 Meter Analysis",
        "📈 Model Insights",
        "⚙️ System Status",
    ]

    # Handle automatic drilldown navigation from queue
    default_nav_idx = 0
    if st.session_state.selected_queue_meter_id is not None:
        default_nav_idx = 2  # Meter Analysis

    selected_nav = st.radio(
        "Select Operational View:",
        views,
        index=default_nav_idx,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("Grid-Guard Phase 10 | Production Polish")
    st.caption("© 2026 Grid-Guard Systems")

# Route to view
try:
    if selected_nav == "📊 Fleet Overview":
        render_overview_view()
    elif selected_nav == "📋 Inspection Queue":
        render_inspection_queue_view()
    elif selected_nav == "🔬 Meter Analysis":
        render_meter_analysis_view()
    elif selected_nav == "📈 Model Insights":
        render_model_insights_view()
    elif selected_nav == "⚙️ System Status":
        render_system_info_view()
except Exception as e:
    st.error(f"An unexpected UI rendering error occurred: {type(e).__name__} — {e}")
    st.info("Check backend logs or reload the session.")
