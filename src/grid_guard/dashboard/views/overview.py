"""Executive Overview view for Grid-Guard Dashboard."""

from __future__ import annotations

import streamlit as st

from grid_guard.dashboard.components.kpi_cards import render_overview_kpis
from grid_guard.dashboard.state import load_decision_comparison_artifact


def render_overview_view() -> None:
    """Render the high-level operational Overview page."""
    st.title("⚡ Grid-Guard Operational Command Center")
    st.caption(
        "Financial-Aware Smart Meter Tampering & Non-Technical Loss (NTL) Prioritization Platform"
    )

    data = load_decision_comparison_artifact()
    summary = data.get("primary_queue_summary", {})

    if not summary:
        st.warning("Operational evaluation artifacts are not loaded. Check artifacts/decision/.")
        return

    st.subheader("📊 Executive KPIs (Latest Fleet Snapshot)")
    render_overview_kpis(summary)

    st.markdown("---")
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("🎯 Fleet Inspection Funnel")
        st.markdown(
            """
            In an electrical distribution grid with **42,372 monitored smart meters**, classical fixed-threshold
            approaches either flood field operations with low-value false alarms or overlook major high-consumption
            commercial anomalies.

            Grid-Guard uses an asymmetric **Cost-Sensitive Objective** and **Dynamic Expected Net Value (ENV)**
            prioritization to maximize economic recovery within operational dispatch constraints:
            """
        )

        funnel_cols = st.columns(3)
        with funnel_cols[0]:
            st.metric("Total Smart Meters", f"{summary.get('total_candidates', 42372):,}")
        with funnel_cols[1]:
            st.metric(
                "Economically Viable",
                f"{summary.get('inspections_recommended', 801):,}",
                help="Candidates with strictly positive Expected Net Value (p * R > C_dispatch)",
            )
        with funnel_cols[2]:
            st.metric(
                "Total Expected Net Value",
                f"${summary.get('expected_financials', {}).get('expected_net_value', 275230.47):,.2f}",
                delta="+$275.2k Net ROI",
                help="Projected financial surplus after paying all crew dispatch costs",
            )

    with col2:
        st.subheader("💡 Key Operational Policies")
        st.markdown(
            """
            - **Dynamic Breakeven Rule ($\\tau_{\\text{env}}$):**
              $$\\tau_{\\text{env}} = \\frac{C_{\\text{dispatch}}}{R}$$
              An inspection is only dispatched when $p_i > \\tau_{\\text{env}}$, guaranteeing $E[\\text{Net Value}] > 0$.
            - **Bayes Cost Threshold ($\\tau_{\\text{cost}}$):**
              $$\\tau_{\\text{cost}} = \\frac{C_{\\text{FP}}}{C_{\\text{FP}} + C_{\\text{FN}}}$$
            - **Explainable Work Orders:**
              Every flagged candidate includes Tree-SHAP local attributions and domain-verified electrical signatures.
            """
        )

    st.markdown("---")
    st.subheader("🚀 Quick Navigation")
    nav_col1, nav_col2, nav_col3 = st.columns(3)
    with nav_col1:
        st.info(
            "📋 **Inspection Queue**\n\nFilter and export prioritized work orders ranked strictly by ENV descending."
        )
    with nav_col2:
        st.info(
            "🔬 **Meter Analysis**\n\nInspect consumption time-series, evaluate demo scenarios, and generate field tickets."
        )
    with nav_col3:
        st.info(
            "📈 **Model Insights**\n\nReview comparative benchmarks across Phase 4 Baseline, Phase 5 Imbalance, and Phase 6 Cost-Sensitive models."
        )
