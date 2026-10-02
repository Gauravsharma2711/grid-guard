"""Evaluation metrics for dynamic decision policies, comparison against fixed thresholds, and Top-K ranking."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import polars as pl

from grid_guard.config.decision import DecisionRule, DecisionSettings
from grid_guard.decision.prioritization import InspectionPrioritizer

logger = logging.getLogger(__name__)


class DecisionEvaluator:
    """Evaluates the economic and operational performance of inspection decision policies."""

    def __init__(self, settings: DecisionSettings | None = None) -> None:
        self.settings = settings or DecisionSettings()

    def evaluate_policy(
        self,
        df_tickets: pl.DataFrame,
    ) -> dict[str, Any]:
        """Compute operational and financial summary metrics for a generated inspection queue.

        Args:
            df_tickets: Polars DataFrame of candidate inspection tickets output by InspectionPrioritizer.

        Returns:
            Dictionary containing comprehensive statistical and financial metrics.
        """
        if df_tickets.is_empty():
            return {"total_candidates": 0, "inspections_recommended": 0}

        total_candidates = len(df_tickets)
        is_recommended = df_tickets.get_column("inspection_recommended").to_numpy().astype(bool)
        n_recommended = int(np.sum(is_recommended))

        p_cal = df_tickets.get_column("calibrated_probability").to_numpy().astype(np.float64)
        r_rev = df_tickets.get_column("estimated_recoverable_revenue").to_numpy().astype(np.float64)
        c_dispatch = (
            float(df_tickets.get_column("dispatch_cost")[0])
            if "dispatch_cost" in df_tickets.columns
            else self.settings.dispatch_cost
        )
        env_all = df_tickets.get_column("env").to_numpy().astype(np.float64)

        # Expected metrics among recommended inspections
        if n_recommended > 0:
            exp_gross = float(np.sum(p_cal[is_recommended] * r_rev[is_recommended]))
            exp_disp = float(n_recommended * c_dispatch)
            exp_env = float(np.sum(env_all[is_recommended]))
            mean_env = float(np.mean(env_all[is_recommended]))
            median_env = float(np.median(env_all[is_recommended]))
            max_env = float(np.max(env_all[is_recommended]))
        else:
            exp_gross = 0.0
            exp_disp = 0.0
            exp_env = 0.0
            mean_env = 0.0
            median_env = 0.0
            max_env = 0.0

        res: dict[str, Any] = {
            "total_candidates": total_candidates,
            "inspections_recommended": n_recommended,
            "inspection_rate_pct": round(n_recommended / total_candidates * 100, 2)
            if total_candidates > 0
            else 0.0,
            "expected_financials": {
                "expected_gross_recovery": round(exp_gross, 2),
                "expected_dispatch_cost": round(exp_disp, 2),
                "expected_net_value": round(exp_env, 2),
                "mean_env_per_ticket": round(mean_env, 2),
                "median_env_per_ticket": round(median_env, 2),
                "max_env": round(max_env, 2),
            },
        }

        # Realized/Proxy metrics if ground-truth labels are present
        if "actual_tamper_label" in df_tickets.columns:
            y_true = (
                df_tickets.get_column("actual_tamper_label")
                .fill_null(0)
                .to_numpy()
                .astype(np.int32)
            )
            y_pred = is_recommended.astype(np.int32)

            tp = int(np.sum((y_true == 1) & (y_pred == 1)))
            fp = int(np.sum((y_true == 0) & (y_pred == 1)))
            fn = int(np.sum((y_true == 1) & (y_pred == 0)))
            tn = int(np.sum((y_true == 0) & (y_pred == 0)))
            total_theft = int(np.sum(y_true == 1))

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / total_theft if total_theft > 0 else 0.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

            # Realized dollar calculations
            realized_fp_dispatch = float(fp * c_dispatch)
            realized_tp_dispatch = float(tp * c_dispatch)
            realized_total_dispatch = float((tp + fp) * c_dispatch)

            # Leakage lost on FN: sum of R_i on FN
            realized_fn_leakage = float(np.sum(r_rev[(y_true == 1) & (y_pred == 0)]))
            # Realized revenue recovered on TP: sum of R_i on TP
            realized_gross_recovery = float(np.sum(r_rev[(y_true == 1) & (y_pred == 1)]))
            realized_net_recovery = realized_gross_recovery - realized_total_dispatch
            realized_operational_loss = realized_fp_dispatch + realized_fn_leakage

            res["realized_evaluation"] = {
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "realized_fp_dispatch_cost": round(realized_fp_dispatch, 2),
                "realized_tp_dispatch_cost": round(realized_tp_dispatch, 2),
                "realized_total_dispatch_cost": round(realized_total_dispatch, 2),
                "realized_fn_leakage_lost": round(realized_fn_leakage, 2),
                "realized_gross_recovery": round(realized_gross_recovery, 2),
                "realized_net_recovery": round(realized_net_recovery, 2),
                "realized_total_operational_loss": round(realized_operational_loss, 2),
            }

        return res

    def compare_decision_policies(
        self,
        predictions_df: pl.DataFrame,
    ) -> dict[str, Any]:
        """Run controlled comparison across: Fixed 0.5, Bayes Cost Threshold, and Dynamic ENV Rule.

        Args:
            predictions_df: Predictions DataFrame.

        Returns:
            Dictionary mapping policy name to evaluation metrics.
        """
        policies = [
            ("fixed_threshold_0.5", DecisionRule.FIXED_THRESHOLD),
            ("bayes_cost_threshold", DecisionRule.COST_THRESHOLD),
            ("dynamic_env_rule", DecisionRule.ENV),
        ]

        comparison: dict[str, Any] = {}
        for name, rule in policies:
            cfg = self.settings.model_copy()
            cfg.decision_rule = rule
            prioritizer = InspectionPrioritizer(settings=cfg)
            tickets_df = prioritizer.prioritize(predictions_df)
            eval_metrics = self.evaluate_policy(tickets_df)
            comparison[name] = eval_metrics

        return comparison

    def evaluate_top_k_ranking(
        self,
        df_ranked_tickets: pl.DataFrame,
        top_k_values: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        """Calculate Precision@K, Recall@K, and cumulative financial recovery across inspection quotas.

        Args:
            df_ranked_tickets: Prioritized tickets sorted by ranking strategy.
            top_k_values: List of inspection capacities K to evaluate.

        Returns:
            List of dictionaries for each K capacity.
        """
        ks = top_k_values or self.settings.top_k_values
        results: list[dict[str, Any]] = []

        total_samples = len(df_ranked_tickets)
        has_labels = "actual_tamper_label" in df_ranked_tickets.columns
        total_thefts = (
            int(df_ranked_tickets.get_column("actual_tamper_label").sum()) if has_labels else 0
        )

        p_cal = df_ranked_tickets.get_column("calibrated_probability").to_numpy().astype(np.float64)
        r_rev = (
            df_ranked_tickets.get_column("estimated_recoverable_revenue")
            .to_numpy()
            .astype(np.float64)
        )
        env_all = df_ranked_tickets.get_column("env").to_numpy().astype(np.float64)
        c_dispatch = (
            float(df_ranked_tickets.get_column("dispatch_cost")[0])
            if "dispatch_cost" in df_ranked_tickets.columns
            else self.settings.dispatch_cost
        )

        y_true = (
            df_ranked_tickets.get_column("actual_tamper_label").to_numpy().astype(np.int32)
            if has_labels
            else np.zeros(total_samples, dtype=np.int32)
        )

        for k in ks:
            if k > total_samples:
                k_eff = total_samples
            else:
                k_eff = k

            if k_eff == 0:
                continue

            # Slice top k
            top_p = p_cal[:k_eff]
            top_r = r_rev[:k_eff]
            top_env = env_all[:k_eff]
            top_y = y_true[:k_eff]

            exp_gross = float(np.sum(top_p * top_r))
            exp_disp = float(k_eff * c_dispatch)
            exp_env = float(np.sum(top_env))

            k_dict: dict[str, Any] = {
                "k": k,
                "inspections_evaluated": k_eff,
                "expected_gross_recovery": round(exp_gross, 2),
                "expected_dispatch_cost": round(exp_disp, 2),
                "expected_net_value": round(exp_env, 2),
            }

            if has_labels:
                tp_k = int(np.sum(top_y == 1))
                prec_k = tp_k / k_eff if k_eff > 0 else 0.0
                rec_k = tp_k / total_thefts if total_thefts > 0 else 0.0
                realized_recovery = float(np.sum(top_r[top_y == 1]))
                realized_net = realized_recovery - exp_disp

                k_dict["confirmed_thefts"] = tp_k
                k_dict["precision_at_k"] = round(prec_k, 4)
                k_dict["recall_at_k"] = round(rec_k, 4)
                k_dict["realized_gross_recovery"] = round(realized_recovery, 2)
                k_dict["realized_net_recovery"] = round(realized_net, 2)

            results.append(k_dict)

        return results

    def run_scenario_sensitivity(
        self,
        predictions_df: pl.DataFrame,
    ) -> dict[str, Any]:
        """Perform economic scenario analysis across operational parameters.

        Scenarios:
            - Baseline: C_dispatch = $100, Tariff = $0.15, Recovery Factor = 1.0
            - High Dispatch Cost: C_dispatch = $200
            - Low Dispatch Cost: C_dispatch = $50
            - High Tariff: Tariff = $0.25 (simulated via 1.667x recovery multiplier)
            - Low Tariff: Tariff = $0.08 (simulated via 0.533x recovery multiplier)
            - Conservative Recovery: Recovery Factor = 0.70

        Args:
            predictions_df: Input predictions DataFrame.

        Returns:
            Dictionary mapping scenario name to outcome summary.
        """
        base_cfg = self.settings
        scenarios = {
            "baseline": base_cfg.model_copy(),
            "high_dispatch_cost_200": base_cfg.model_copy(update={"dispatch_cost": 200.0}),
            "low_dispatch_cost_50": base_cfg.model_copy(update={"dispatch_cost": 50.0}),
            "conservative_recovery_0.70": base_cfg.model_copy(update={"recovery_factor": 0.70}),
            "high_tariff_0.25": base_cfg.model_copy(
                update={"recovery_factor": 1.0 * (0.25 / 0.15)}
            ),
            "low_tariff_0.08": base_cfg.model_copy(update={"recovery_factor": 1.0 * (0.08 / 0.15)}),
        }

        scenario_results: dict[str, Any] = {}
        for sc_name, sc_cfg in scenarios.items():
            prioritizer = InspectionPrioritizer(settings=sc_cfg)
            tickets_df = prioritizer.prioritize(predictions_df)
            eval_metrics = self.evaluate_policy(tickets_df)
            scenario_results[sc_name] = {
                "dispatch_cost": sc_cfg.dispatch_cost,
                "recovery_factor": round(sc_cfg.recovery_factor, 3),
                "inspections_recommended": eval_metrics["inspections_recommended"],
                "expected_gross_recovery": eval_metrics["expected_financials"][
                    "expected_gross_recovery"
                ],
                "expected_net_value": eval_metrics["expected_financials"]["expected_net_value"],
                "mean_env_per_ticket": eval_metrics["expected_financials"]["mean_env_per_ticket"],
            }
            if "realized_evaluation" in eval_metrics:
                scenario_results[sc_name]["realized_precision"] = eval_metrics[
                    "realized_evaluation"
                ]["precision"]
                scenario_results[sc_name]["realized_net_recovery"] = eval_metrics[
                    "realized_evaluation"
                ]["realized_net_recovery"]

        return scenario_results
