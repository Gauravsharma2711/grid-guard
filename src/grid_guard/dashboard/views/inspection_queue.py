"""Prioritized Inspection Queue view for Grid-Guard Dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from grid_guard.dashboard.api_client import DashboardApiError
from grid_guard.dashboard.state import get_api_client, load_enriched_tickets_table


def render_inspection_queue_view() -> None:
    """Render the filterable, prioritized Inspection Queue work order table."""
    st.title("📋 Prioritized Inspection Work Order Queue")
    st.caption("Meters ranked strictly by Expected Net Value (ENV = p * R - C_dispatch) descending")

    client = get_api_client()

    # Filter Sidebar / Top controls
    with st.expander("🔍 Queue Filters & Controls", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            search_query = st.text_input("Search Meter ID", placeholder="e.g. 1000282").strip()
        with f_col2:
            min_prob = st.slider("Min Tamper Probability", 0.0, 1.0, 0.50, step=0.05)
        with f_col3:
            min_env = st.slider("Min Expected Net Value ($)", 0.0, 5000.0, 0.0, step=50.0)
        with f_col4:
            max_rows = st.number_input("Max Results to Return", 10, 500, 50, step=10)

    # Fetch data: Try FastAPI first, fallback to cached artifact
    df: pd.DataFrame
    source_label = "Live FastAPI Backend"
    try:
        queue_resp = client.get_inspection_queue(
            max_inspections=int(max_rows),
            decision_rule="env",
            min_env=float(min_env),
            min_probability=float(min_prob),
            include_explanations=True,
        )
        tickets = queue_resp.get("tickets", [])
        if tickets:
            df = pd.DataFrame(tickets)
            if "env" not in df.columns and "expected_net_value" in df.columns:
                df["env"] = df["expected_net_value"]
        else:
            df = pd.DataFrame()
    except DashboardApiError:
        source_label = "Verified Phase 7/8 Precomputed Artifacts"
        df = load_enriched_tickets_table()

    if df.empty:
        st.warning("No inspection candidates matched the selected filter criteria.")
        return

    st.caption(f"Data Source: **{source_label}** | Found **{len(df):,}** candidate work orders")

    # Standardize column names for display
    col_mapping = {
        "priority_rank": "Rank",
        "meter_id": "Meter ID",
        "tamper_probability": "Probability",
        "estimated_recoverable_revenue": "Est. Recoverable ($)",
        "dispatch_cost": "Dispatch Cost ($)",
        "env": "Expected Net Value ($)",
        "decision_rule": "Policy",
        "inspection_recommended": "Recommended",
        "signatures_summary": "Detected Signatures",
        "customer_type": "Customer Type",
    }

    # Apply client-side filters if operating on precomputed artifact
    filtered_df = df.copy()
    if "meter_id" in filtered_df.columns and search_query:
        filtered_df = filtered_df[
            filtered_df["meter_id"].astype(str).str.contains(search_query, case=False, na=False)
        ]
    if "tamper_probability" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["tamper_probability"] >= min_prob]
    if "env" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["env"] >= min_env]

    # Display columns that exist
    display_cols = [c for c in col_mapping if c in filtered_df.columns]
    view_df = filtered_df[display_cols].rename(columns=col_mapping)

    # Format numeric values
    if "Probability" in view_df.columns:
        view_df["Probability"] = view_df["Probability"].map(lambda x: f"{x * 100:.1f}%")
    if "Est. Recoverable ($)" in view_df.columns:
        view_df["Est. Recoverable ($)"] = view_df["Est. Recoverable ($)"].map(
            lambda x: f"${x:,.2f}"
        )
    if "Dispatch Cost ($)" in view_df.columns:
        view_df["Dispatch Cost ($)"] = view_df["Dispatch Cost ($)"].map(lambda x: f"${x:,.2f}")
    if "Expected Net Value ($)" in view_df.columns:
        view_df["Expected Net Value ($)"] = view_df["Expected Net Value ($)"].map(
            lambda x: f"${x:,.2f}"
        )

    st.dataframe(view_df, use_container_width=True, hide_index=True)

    # Action bar: Drilldown selection & CSV export
    act_col1, act_col2 = st.columns([3, 1])

    with act_col1:
        if "meter_id" in filtered_df.columns and not filtered_df.empty:
            meter_list = filtered_df["meter_id"].astype(str).tolist()
            selected_meter = st.selectbox(
                "Select a Meter to inspect full details, time series, and SHAP attribution:",
                meter_list,
            )
            if st.button("🔎 Investigate Selected Meter in Meter Analysis"):
                st.session_state.selected_queue_meter_id = selected_meter
                st.session_state.current_meter_id = selected_meter
                st.info(
                    f"Selected meter `{selected_meter}`. Navigate to 'Meter Analysis' tab in sidebar to view details."
                )

    with act_col2:
        csv_data = view_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Queue (CSV)",
            data=csv_data,
            file_name="grid_guard_prioritized_inspection_queue.csv",
            mime="text/csv",
            help="Download the filtered inspection queue for field operations dispatch",
        )
