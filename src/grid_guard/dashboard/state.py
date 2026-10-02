"""Streamlit session state management and artifact loaders for Grid-Guard Dashboard."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from grid_guard.dashboard.api_client import DashboardApiClient
from grid_guard.dashboard.demo_data.synthetic_meters import get_demo_meter


@st.cache_resource
def get_api_client() -> DashboardApiClient:
    """Provide a singleton instance of DashboardApiClient."""
    return DashboardApiClient()


def init_session_state() -> None:
    """Initialize necessary Streamlit session state keys."""
    if "selected_demo_key" not in st.session_state:
        st.session_state.selected_demo_key = "sustained_step_down"

    if "current_meter_id" not in st.session_state:
        default_demo = get_demo_meter("sustained_step_down")
        st.session_state.current_meter_id = default_demo["meter_id"]
        st.session_state.current_readings = default_demo["readings"]

    if "current_ticket" not in st.session_state:
        st.session_state.current_ticket = None

    if "current_prediction" not in st.session_state:
        st.session_state.current_prediction = None

    if "selected_queue_meter_id" not in st.session_state:
        st.session_state.selected_queue_meter_id = None

    if "api_health" not in st.session_state:
        st.session_state.api_health = None


@st.cache_data(ttl=3600)
def load_decision_comparison_artifact() -> dict[str, Any]:
    """Load precomputed decision policy benchmark comparison."""
    path = Path("artifacts/decision/decision_comparison.json")
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


@st.cache_data(ttl=3600)
def load_cost_sensitive_comparison_artifact() -> dict[str, Any]:
    """Load precomputed 3-phase model benchmark comparison."""
    path = Path("artifacts/cost_sensitive/cost_sensitive_comparison.json")
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


@st.cache_data(ttl=3600)
def load_enriched_tickets_table() -> pd.DataFrame:
    """Load precomputed inspection tickets CSV if available."""
    path = Path("artifacts/explainability/enriched_top_100_tickets.csv")
    if not path.exists():
        path = Path("artifacts/decision/top_100_inspection_tickets.csv")

    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()
