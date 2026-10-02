"""System Information and Health Status view for Grid-Guard Dashboard."""

from __future__ import annotations

import streamlit as st

from grid_guard.dashboard.api_client import DashboardApiError
from grid_guard.dashboard.state import get_api_client


def render_system_info_view() -> None:
    """Render the System Information and Health Monitoring view."""
    st.title("⚙️ System Status & Metadata Introspection")
    st.caption("Live health probes, loaded model checkpoints, and public operational constraints.")

    client = get_api_client()

    # Section 1: Live Service Health Probes
    st.subheader("1. Service Health & Readiness Probes")
    h_col1, h_col2 = st.columns(2)

    with h_col1:
        st.markdown("**FastAPI Application Liveness (`/health`)**")
        try:
            health = client.check_health()
            st.success(
                f"🟢 **HEALTHY** — Service: `{health.get('service')}`, Version: `v{health.get('api_version')}`"
            )
        except DashboardApiError as e:
            st.error(f"🔴 **UNAVAILABLE** — {e.message}")

    with h_col2:
        st.markdown("**Booster & Explainer Readiness (`/ready`)**")
        try:
            ready = client.check_ready()
            if ready.get("status") == "ready":
                st.success(
                    f"🟢 **READY** — Model: `{ready.get('model_version')}`, Features: `{ready.get('feature_count')} configured`"
                )
            else:
                st.warning("🟡 **INITIALIZING** — Checkpoints not fully pinned in memory.")
        except DashboardApiError as e:
            st.error(f"🔴 **UNAVAILABLE** — {e.message}")

    st.markdown("---")
    st.subheader("2. Model & Checkpoint Provenance")

    try:
        model_meta = client.get_model_metadata()
    except DashboardApiError:
        model_meta = {
            "model_version": "phase6_cost_sensitive_dispatch_norm",
            "model_type": "LightGBM Booster",
            "objective": "Binary Log-Loss with Financial Sample Weighting",
            "feature_count": 60,
            "feature_version": "v1.0.0",
            "explainer_type": "TreeSHAP (shap.TreeExplainer)",
            "base_value": -2.3725,
            "decision_rule_version": "v1.0.0",
        }

    meta_col1, meta_col2 = st.columns(2)
    with meta_col1:
        st.markdown(f"**Loaded Model Version:** `{model_meta.get('model_version', 'N/A')}`")
        st.markdown(
            f"**Booster Architecture:** `{model_meta.get('model_type', 'LightGBM Booster')}`"
        )
        st.markdown(
            f"**Training Objective:** `{model_meta.get('objective', 'Cost-Sensitive Weighted Log-Loss')}`"
        )
        st.markdown(
            f"**Feature Dimension:** `{model_meta.get('feature_count', 60)} temporal features`"
        )

    with meta_col2:
        st.markdown(
            f"**Explainability Engine:** `{model_meta.get('explainer_type', 'TreeSHAP (Exact TreeExplainer)')}`"
        )
        st.markdown(
            f"**Baseline Expected Value:** `{model_meta.get('base_value', -2.3725):.4f}` log-odds"
        )
        st.markdown("**Decision Rule Mode:** `Expected Net Value (ENV)`")
        st.markdown(
            "**Dataset Identifier:** `State Grid Corporation of China (SGCC) AMI Benchmark`"
        )

    st.markdown("---")
    st.subheader("3. Public Operational Constraints & Parameter Limits")

    try:
        pub_config = client.get_public_config()
        limits = pub_config.get("limits", {})
        fin_defaults = pub_config.get("financial_defaults", {})
    except DashboardApiError:
        limits = {"min_readings_per_meter": 30, "max_readings_per_meter": 730, "max_batch_size": 50}
        fin_defaults = {"default_tariff": 0.15, "default_dispatch_cost": 100.0, "currency": "USD"}

    lim_col1, lim_col2 = st.columns(2)
    with lim_col1:
        st.markdown("##### Input Ingestion Constraints")
        st.markdown("- **Input Cadence:** Daily Smart Meter Readings (kWh)")
        st.markdown(
            f"- **Minimum History Required:** `{limits.get('min_readings_per_meter', 30)} days`"
        )
        st.markdown(
            f"- **Maximum History Allowed:** `{limits.get('max_readings_per_meter', 730)} days`"
        )
        st.markdown(f"- **Batch Request Size Limit:** `{limits.get('max_batch_size', 50)} meters`")

    with lim_col2:
        st.markdown("##### Financial Parameter Defaults")
        st.markdown(f"- **Default Tariff:** `${fin_defaults.get('default_tariff', 0.15)}/kWh`")
        st.markdown(
            f"- **Default Crew Dispatch Cost ($C_{{\\text{{FP}}}}$):** `${fin_defaults.get('default_dispatch_cost', 100.0)}`"
        )
        st.markdown(f"- **Default Currency:** `{fin_defaults.get('currency', 'USD')}`")
        st.markdown("- **Leakage Recovery Horizon:** `12 billing cycles`")

    st.markdown("---")
    st.caption(
        "🔒 **Security Note:** File system paths, environment secrets, and backend credentials are "
        "intentionally redacted in compliance with Grid-Guard Phase 10 security standards."
    )
