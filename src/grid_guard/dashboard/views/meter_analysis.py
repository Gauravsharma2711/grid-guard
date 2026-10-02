"""Detailed Meter Analysis and Demonstration view for Grid-Guard Dashboard."""

from __future__ import annotations

from typing import Any

import streamlit as st

from grid_guard.dashboard.api_client import DashboardApiError
from grid_guard.dashboard.components.charts import (
    plot_consumption_timeseries,
    plot_shap_contributions,
)
from grid_guard.dashboard.components.kpi_cards import render_meter_kpis
from grid_guard.dashboard.components.ticket_card import render_ticket_card
from grid_guard.dashboard.demo_data.synthetic_meters import DEMO_METERS, get_demo_meter
from grid_guard.dashboard.state import get_api_client


def render_meter_analysis_view() -> None:
    """Render the end-to-end Meter Analysis & Demonstration view."""
    st.title("🔬 Meter Investigation & Explainability")
    st.caption(
        "Interactive end-to-end evaluation: raw AMI smart-meter time-series → 60 temporal features "
        "→ cost-sensitive model score → dynamic ENV → Tree-SHAP attributions → field work order ticket."
    )

    client = get_api_client()

    # Step 1: Input Selection / Demo Archetype Picker
    st.subheader("1. Select Meter Dataset (Demo Scenarios or Custom)")
    demo_keys = list(DEMO_METERS.keys())
    demo_names = [f"{DEMO_METERS[k]['name']} ({k})" for k in demo_keys]

    selected_idx = 0
    if st.session_state.selected_demo_key in demo_keys:
        selected_idx = demo_keys.index(st.session_state.selected_demo_key)

    col_select, col_info = st.columns([2, 3])
    with col_select:
        choice = st.selectbox(
            "Choose a Demonstration Scenario:",
            demo_names,
            index=selected_idx,
            help="Select one of 5 deterministic, clearly labeled synthetic demo meter archetypes",
        )
        selected_key = demo_keys[demo_names.index(choice)]
        st.session_state.selected_demo_key = selected_key

    demo_data = get_demo_meter(selected_key)
    with col_info:
        st.markdown(
            f"**Customer Class:** `{demo_data.get('customer_type', 'residential').title()}`"
        )
        st.markdown(f"**Description:** {demo_data.get('description', '')}")
        st.markdown(f"**Expected Outcome:** *{demo_data.get('expected_behavior', '')}*")
        st.caption("🏷️ **DATASET STATUS: SYNTHETIC DEMO DATA** (Zero real consumer information)")

    # Configuration overrides
    with st.expander("⚙️ Financial & Operational Parameter Overrides", expanded=False):
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            tariff = st.number_input("Electricity Tariff ($/kWh)", 0.05, 1.0, 0.15, step=0.01)
        with p_col2:
            dispatch_cost = st.number_input(
                "Crew Dispatch Cost ($)", 10.0, 1000.0, 100.0, step=10.0
            )
        with p_col3:
            policy = st.selectbox(
                "Decision Policy Rule", ["env", "cost_threshold", "fixed_threshold"]
            )

    # Execution trigger
    st.markdown("---")
    st.subheader("2. Run End-to-End Prediction & Explainability Pipeline")
    exec_col1, exec_col2 = st.columns([1, 3])
    with exec_col1:
        run_btn = st.button(
            "⚡ Score Meter & Generate Ticket", type="primary", use_container_width=True
        )

    ticket_data: dict[str, Any] | None = st.session_state.current_ticket

    if run_btn:
        with st.spinner(
            "Calling Grid-Guard FastAPI backend (Feature Extraction → Booster → Dynamic ENV → Tree-SHAP)..."
        ):
            try:
                ticket_data = client.generate_ticket(
                    meter_id=demo_data["meter_id"],
                    readings=demo_data["readings"],
                    tariff_per_kwh=tariff,
                    dispatch_cost=dispatch_cost,
                    decision_rule=policy,
                    include_explanation=True,
                )
                st.session_state.current_ticket = ticket_data
                st.session_state.current_readings = demo_data["readings"]
                st.success("✅ Analysis completed successfully via FastAPI backend!")
            except DashboardApiError as e:
                st.error(f"❌ API Request Failed: {e.message}")
                if e.detail:
                    st.code(e.detail)
                return

    # If no ticket in state yet, allow running automatically on initial load
    if ticket_data is None:
        st.info(
            "Click **'Score Meter & Generate Ticket'** above to process this meter's 90-day AMI readings."
        )
        # Plot raw time-series even before prediction
        plot_consumption_timeseries(demo_data["readings"], demo_data["meter_id"])
        return

    # Render results
    st.markdown("---")
    st.subheader("3. Model Decision & Financial Exposure")
    render_meter_kpis(ticket_data)

    st.markdown("---")
    t_col1, t_col2 = st.columns([3, 2])

    with t_col1:
        st.subheader("📈 AMI Daily Consumption Time-Series")
        readings = st.session_state.get("current_readings", demo_data["readings"])
        plot_consumption_timeseries(readings, ticket_data.get("meter_id", demo_data["meter_id"]))

    with t_col2:
        st.subheader("⚡ Detected Tampering Signatures")
        explanation = ticket_data.get("explanation", {}) or {}
        signatures = explanation.get("detected_signatures", [])
        if signatures:
            for sig in signatures:
                if isinstance(sig, dict):
                    name = sig.get("signature_name") or sig.get("name", "Signature")
                    desc = sig.get("description", "")
                else:
                    name = str(sig)
                    desc = ""
                st.markdown(f"- **{name}**")
                if desc:
                    st.caption(desc)
        else:
            st.info(
                "No distinct electrical tampering signatures detected above activation thresholds."
            )

        st.subheader("⚖️ Counter-Evidence")
        counter_ev = explanation.get("counter_evidence", [])
        if counter_ev:
            for ce in counter_ev:
                st.markdown(f"- {ce}")
        else:
            st.caption("No mitigating counter-evidence found.")

    st.markdown("---")
    st.subheader("4. Local Tree-SHAP Attribution")
    st.caption(
        "How each engineered feature moved the model score away from the dataset expected log-odds baseline:"
    )
    top_pos = explanation.get("top_positive_features", [])
    top_neg = explanation.get("top_negative_features", [])
    combined_features = top_pos + top_neg
    plot_shap_contributions(combined_features)

    # Render complete inspection ticket
    render_ticket_card(ticket_data)
