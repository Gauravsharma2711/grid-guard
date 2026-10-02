"""Field Inspection Work Order Ticket card renderer for Grid-Guard Dashboard."""

from __future__ import annotations

import json
from typing import Any

import streamlit as st


def render_ticket_card(ticket_data: dict[str, Any]) -> None:
    """Render a field inspection ticket work order matching Grid-Guard specifications."""
    ticket_id = ticket_data.get("ticket_id", "TCK-PENDING")
    meter_id = ticket_data.get("meter_id", "UNKNOWN")
    eval_period = ticket_data.get("evaluation_period", "Latest Evaluation Window")
    prob = ticket_data.get("tamper_probability", 0.0)
    rec_revenue = ticket_data.get("estimated_recoverable_revenue", 0.0)
    dispatch_cost = ticket_data.get("dispatch_cost", 100.0)
    env = ticket_data.get("env", 0.0)
    decision_rule = ticket_data.get("decision_rule", "env")
    threshold = ticket_data.get("active_threshold", 0.5)
    rank = ticket_data.get("priority_rank", None)
    customer_type = ticket_data.get("customer_type", "Standard")

    explanation = ticket_data.get("explanation", {}) or {}
    summary = explanation.get("summary") or ticket_data.get(
        "signatures_summary", "Multivariate Feature Anomaly"
    )
    detected_sigs = explanation.get("detected_signatures", [])
    counter_ev = explanation.get("counter_evidence", [])
    top_pos = explanation.get("top_positive_features", [])

    st.markdown("---")
    st.subheader(f"🎫 Field Work Order Ticket: `{ticket_id}`")

    # Ticket metadata block in an expander or bordered container
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Target Meter ID:** `{meter_id}`")
            st.markdown(f"**Evaluation Period:** `{eval_period}`")
            st.markdown(f"**Customer Class:** `{customer_type.title()}`")
            if rank:
                st.markdown(f"**Priority Queue Rank:** `#{rank}`")

        with col2:
            st.markdown(f"**Tamper Probability:** `{prob * 100:.1f}%`")
            st.markdown(f"**Active Threshold (tau):** `{threshold:.3f}`")
            st.markdown(f"**Decision Policy:** `{decision_rule.upper()}`")
            status_text = (
                "🟢 DISPATCH RECOMMENDED"
                if ticket_data.get("inspection_recommended", False)
                else "⚪ DO NOT DISPATCH"
            )
            st.markdown(f"**Dispatch Status:** **{status_text}**")

        with col3:
            st.markdown(f"**Est. Recoverable Revenue:** `${rec_revenue:,.2f}`")
            st.markdown(f"**Crew Dispatch Cost:** `${dispatch_cost:,.2f}`")
            st.markdown(f"**Expected Net Value (ENV):** **${env:,.2f}**")

        st.markdown("#### 🔍 Why Flagged")
        st.info(summary)

        # Signatures
        if detected_sigs:
            st.markdown("#### ⚡ Detected Electrical Signatures")
            for sig in detected_sigs:
                if isinstance(sig, dict):
                    sig_name = sig.get("signature_name") or sig.get("name", "Unknown Signature")
                    sig_desc = sig.get("description", "")
                else:
                    sig_name = str(sig)
                    sig_desc = ""
                st.markdown(f"- **{sig_name}**: {sig_desc}" if sig_desc else f"- **{sig_name}**")

        # Top Model Drivers
        if top_pos:
            st.markdown("#### 📈 Key Model Drivers (Tree-SHAP)")
            for feat in top_pos[:5]:
                fname = feat.get("feature_name", "Feature").replace("_", " ").title()
                val = feat.get("feature_value")
                contrib = feat.get("contribution", 0.0)
                val_text = f" (Value: {val:.2f})" if isinstance(val, (int, float)) else ""
                st.markdown(f"- **{fname}**{val_text}: `+{contrib:.3f}` log-odds")

        # Counter-evidence
        if counter_ev:
            st.markdown("#### ⚖️ Counter-Evidence & Mitigating Factors")
            for ce in counter_ev:
                st.markdown(f"- {ce}")

        # Field safety disclaimer
        st.warning(
            "⚠️ **Operational Field Dispatch Note:** "
            "Model evidence indicates an anomalous consumption signature that warrants physical verification; "
            "it does NOT establish physical bypass or legal theft. Field personnel must follow standard safety "
            "and regulatory inspection protocols without presumption of customer guilt."
        )

        # JSON Export Button
        ticket_json_str = json.dumps(ticket_data, indent=2, default=str)
        st.download_button(
            label="📥 Export Work Order (JSON)",
            data=ticket_json_str,
            file_name=f"ticket_{ticket_id}_{meter_id}.json",
            mime="application/json",
            help="Download complete structured field inspection ticket for utility work management systems",
        )
