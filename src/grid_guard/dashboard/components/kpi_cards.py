"""Reusable KPI metric card components for Grid-Guard Dashboard."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_overview_kpis(summary: dict[str, Any]) -> None:
    """Render high-level operational KPI cards with proper financial labeling."""
    expected = summary.get("expected_financials", {})
    realized = summary.get("realized_evaluation", {})

    total_candidates = summary.get("total_candidates", 0)
    recommended = summary.get("inspections_recommended", 0)
    rate = summary.get("inspection_rate_pct", 0.0)

    gross_rec = expected.get("expected_gross_recovery", 0.0)
    dispatch_cost = expected.get("expected_dispatch_cost", 0.0)
    net_value = expected.get("expected_net_value", 0.0)
    mean_env = expected.get("mean_env_per_ticket", 0.0)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Monitored Meters",
            value=f"{total_candidates:,}",
            help="Total active AMI smart meters evaluated in the latest snapshot",
        )
        st.metric(
            label="Recommended Inspections",
            value=f"{recommended:,}",
            delta=f"{rate:.2f}% of fleet",
            delta_color="off",
            help="Candidate meters meeting the dynamic Expected Net Value cutoff",
        )

    with col2:
        st.metric(
            label="Expected Recovery (Modeled)",
            value=f"${gross_rec:,.2f}",
            help="Projected gross financial recovery: sum of p_i * R_i across recommended tickets",
        )
        st.metric(
            label="Expected Dispatch Cost",
            value=f"${dispatch_cost:,.2f}",
            help="Total operational crew dispatch budget: N_inspections * C_FP ($100/visit)",
        )

    with col3:
        st.metric(
            label="Expected Net Value (ENV)",
            value=f"${net_value:,.2f}",
            delta="Positive ROI",
            delta_color="normal" if net_value > 0 else "inverse",
            help="Modeled net financial return: Expected Recovery - Total Dispatch Cost",
        )
        st.metric(
            label="Mean ENV per Ticket",
            value=f"${mean_env:,.2f}",
            help="Average expected net revenue contribution per dispatched field crew",
        )

    with col4:
        precision = realized.get("precision", 0.0)
        net_rec = realized.get("realized_net_recovery", 0.0)
        st.metric(
            label="Validation Precision",
            value=f"{precision * 100:.1f}%",
            help="Field verification precision achieved on holdout test partition",
        )
        st.metric(
            label="Realized Net Recovery",
            value=f"${net_rec:,.2f}",
            help="Actual revenue recovered net of dispatch costs on ground-truth evaluation",
        )


def render_meter_kpis(data: dict[str, Any]) -> None:
    """Render single-meter prediction and financial metrics banner."""
    pred_obj = data.get("prediction", {})
    prob = pred_obj.get("tamper_probability") if pred_obj else data.get("tamper_probability", 0.0)

    decision_obj = data.get("decision", {})
    recommended = (
        decision_obj.get("inspection_recommended")
        if decision_obj
        else data.get("inspection_recommended", False)
    )
    decision_rule = (
        decision_obj.get("decision_rule") if decision_obj else data.get("decision_rule", "env")
    )
    threshold = (
        decision_obj.get("active_threshold") if decision_obj else data.get("active_threshold", 0.5)
    )

    financial = data.get("financial", {})
    if financial:
        leakage_kwh = financial.get("estimated_leakage_kwh", 0.0)
        recoverable_rev = financial.get("estimated_recoverable_revenue", 0.0)
        dispatch_cost = financial.get("dispatch_cost", 100.0)
        env = financial.get("expected_net_value", 0.0)
    else:
        leakage_kwh = data.get("estimated_leakage_kwh", 0.0)
        recoverable_rev = data.get("estimated_recoverable_revenue", 0.0)
        dispatch_cost = data.get("dispatch_cost", 100.0)
        env = data.get("env", 0.0)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="Tamper Probability",
            value=f"{prob * 100:.1f}%",
            delta="High Risk" if prob >= 0.5 else "Low Risk",
            delta_color="inverse" if prob >= 0.5 else "normal",
            help="LightGBM cost-sensitive booster predicted posterior probability",
        )

    with col2:
        decision_label = "DISPATCH RECOMMENDED" if recommended else "DO NOT DISPATCH"
        st.metric(
            label=f"Decision ({decision_rule.upper()})",
            value=decision_label,
            delta=f"Threshold tau: {threshold:.3f}",
            delta_color="normal" if recommended else "off",
            help="Dynamic operational decision based on Expected Net Value maximization",
        )

    with col3:
        st.metric(
            label="Recoverable Revenue",
            value=f"${recoverable_rev:,.2f}",
            delta=f"{leakage_kwh:,.1f} kWh leakage",
            delta_color="off",
            help="Modeled 12-month unmetered revenue exposure R = Deficit * Tariff * Cycles",
        )

    with col4:
        st.metric(
            label="Dispatch Cost",
            value=f"${dispatch_cost:,.2f}",
            help="Assumed fixed crew operational dispatch cost C_FP",
        )

    with col5:
        st.metric(
            label="Expected Net Value (ENV)",
            value=f"${env:,.2f}",
            delta="Economically Justified" if env > 0 else "Negative ROI",
            delta_color="normal" if env > 0 else "inverse",
            help="E[Net Value] = p * R - C_dispatch. Must be strictly positive for dispatch.",
        )
