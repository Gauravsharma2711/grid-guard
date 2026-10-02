"""Model Performance and Insights view for Grid-Guard Dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from grid_guard.dashboard.components.charts import (
    plot_phase_benchmarks_chart,
    plot_policy_comparison_chart,
)
from grid_guard.dashboard.state import (
    load_cost_sensitive_comparison_artifact,
    load_decision_comparison_artifact,
)


def render_model_insights_view() -> None:
    """Render the technical Model Insights and comparative benchmark view."""
    st.title("📈 Model Performance & Comparative Evaluation")
    st.caption(
        "Empirical benchmarks across experimental development phases and operational decision policies."
    )

    cost_data = load_cost_sensitive_comparison_artifact()
    decision_data = load_decision_comparison_artifact()

    tab1, tab2 = st.tabs(
        ["Multi-Phase ML Benchmarks (Phases 4–6)", "Operational Decision Rules (Phase 7)"]
    )

    with tab1:
        st.subheader("1. Machine Learning Evolution Across Development Phases")
        st.markdown(
            """
            Grid-Guard evaluated three modeling regimes on a time-aware validation partition (254,232 samples, 8.53% prevalence):
            1. **Phase 4 Baseline**: Standard unweighted LightGBM booster.
            2. **Phase 5 Imbalance**: SMOTE-Tomek balanced sampling.
            3. **Phase 6 Cost-Sensitive**: Financially weighted learning where sample loss is scaled by potential revenue leakage.
            """
        )

        plot_phase_benchmarks_chart(cost_data)

        # Comparative Metrics Table
        exps = cost_data.get("validation_experiments", {})
        if exps:
            rows = []
            for name, display in [
                ("phase4_unweighted_baseline", "Phase 4: Unweighted Baseline"),
                ("phase5_smote_tomek", "Phase 5: SMOTE-Tomek"),
                ("phase6_cost_sensitive_dispatch_norm", "Phase 6: Cost-Sensitive (Champion)"),
            ]:
                item = exps.get(name, {})
                stat = item.get("statistical", {})
                cm = stat.get("confusion_matrix", {})
                fin = item.get("financial", {})
                ranking = item.get("ranking", {})

                rows.append(
                    {
                        "Phase / Architecture": display,
                        "PR-AUC": f"{stat.get('pr_auc', 0.0):.4f}",
                        "ROC-AUC": f"{stat.get('roc_auc', 0.0):.4f}",
                        "Precision@10": f"{ranking.get('10', {}).get('precision_at_k', 0.0):.2f}",
                        "Precision@50": f"{ranking.get('50', {}).get('precision_at_k', 0.0):.2f}",
                        "Precision@100": f"{ranking.get('100', {}).get('precision_at_k', 0.0):.2f}",
                        "Precision@500": f"{ranking.get('500', {}).get('precision_at_k', 0.0):.2f}",
                        "False Positives": f"{cm.get('fp', 0):,}",
                        "Wasted Dispatch ($)": f"${fin.get('wasted_dispatch_cost', 0.0):,.0f}",
                        "Lost Leakage ($)": f"${fin.get('undetected_leakage_cost', 0.0):,.0f}",
                        "Total Operational Loss ($)": f"${fin.get('total_operational_loss', 0.0):,.0f}",
                    }
                )

            df_table = pd.DataFrame(rows)
            st.dataframe(df_table, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("2. Operational Decision Rule Comparison")
        st.markdown(
            """
            Comparison of three candidate inspection policies on the primary 42,372 meter candidate queue:
            - **Fixed Threshold (p >= 0.50)**: Ignores financial stakes; treats a $10 leakage customer the same as a $10,000 commercial customer.
            - **Bayes Cost Threshold**: Threshold scaled by theoretical cost ratio $\\tau = \\frac{C_{\\text{FP}}}{C_{\\text{FP}} + C_{\\text{FN}}}$.
            - **Dynamic Expected Net Value (Grid-Guard)**: Dispatches crew only when expected recovery exceeds dispatch cost ($p_i \\times R_i > C_{\\text{dispatch}}$) and ranks by ENV descending.
            """
        )

        plot_policy_comparison_chart(decision_data)

        # Policy Table
        policies = decision_data.get("policy_comparison", {})
        if policies:
            policy_rows = []
            for pol_key, pol_title in [
                ("fixed_threshold_0.5", "Fixed Threshold (p >= 0.50)"),
                ("bayes_cost_threshold", "Bayes Cost Threshold"),
                ("env_ranking", "Dynamic Expected Net Value (ENV)"),
            ]:
                pol_data = policies.get(pol_key, {})
                exp_fin = pol_data.get("expected_financials", {})
                real_ev = pol_data.get("realized_evaluation", {})

                policy_rows.append(
                    {
                        "Policy": pol_title,
                        "Inspections Dispatched": f"{pol_data.get('inspections_recommended', 0):,}",
                        "Inspection Rate": f"{pol_data.get('inspection_rate_pct', 0.0):.2f}%",
                        "Expected Gross Recovery": f"${exp_fin.get('expected_gross_recovery', 0.0):,.2f}",
                        "Total Dispatch Cost": f"${exp_fin.get('expected_dispatch_cost', 0.0):,.2f}",
                        "Expected Net Value (ENV)": f"${exp_fin.get('expected_net_value', 0.0):,.2f}",
                        "Mean ENV / Ticket": f"${exp_fin.get('mean_env_per_ticket', 0.0):,.2f}",
                        "Realized Operational Loss": f"${real_ev.get('realized_total_operational_loss', 0.0):,.2f}",
                    }
                )

            df_pol = pd.DataFrame(policy_rows)
            st.dataframe(df_pol, use_container_width=True, hide_index=True)
            st.caption(
                "Note: Expected numbers reflect model expectations ($E[R] = \\sum p_i R_i$). "
                "Realized numbers reflect actual evaluation against holdout ground-truth test labels."
            )
