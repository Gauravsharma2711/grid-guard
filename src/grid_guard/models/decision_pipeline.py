"""End-to-end operational decision pipeline for dynamic thresholding, ENV ranking, and inspection ticket dispatch."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from grid_guard.config.settings import Settings, get_settings
from grid_guard.decision.prioritization import InspectionPrioritizer
from grid_guard.evaluation.decision_metrics import DecisionEvaluator
from grid_guard.evaluation.plots import DecisionVisualizer
from grid_guard.tracking.experiment import MLflowTracker

logger = logging.getLogger(__name__)


class DecisionPipeline:
    """Orchestrates Phase 7 dynamic thresholding, Expected Net Value prioritization, and ticket generation."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.decision_settings = self.settings.decision
        self.prioritizer = InspectionPrioritizer(settings=self.decision_settings)
        self.evaluator = DecisionEvaluator(settings=self.decision_settings)

    def run(
        self,
        predictions_path: str | Path | None = None,
        output_dir: str | Path | None = None,
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """Execute the complete Phase 7 decision engine workflow.

        Args:
            predictions_path: Path to Phase 6 predictions parquet (defaults to champion_predictions.parquet).
            output_dir: Target directory for artifacts (defaults to artifacts/decision).
            enable_mlflow: Whether to log results and artifacts to MLflow.

        Returns:
            Dictionary containing comparison metrics, top-K ranking, scenarios, and execution summary.
        """
        start_time = time.time()
        in_path = Path(
            predictions_path
            or self.settings.artifacts_dir / "cost_sensitive" / "champion_predictions.parquet"
        )
        out_dir = Path(output_dir or self.settings.artifacts_dir / "decision")
        out_dir.mkdir(parents=True, exist_ok=True)
        figs_dir = out_dir / "figures"
        figs_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Loading Phase 6 predictions from '%s'...", in_path)
        if not in_path.exists():
            raise FileNotFoundError(
                f"Predictions file not found at '{in_path}'. Run Phase 6 first."
            )

        df_preds = pl.read_parquet(in_path)
        logger.info(
            "Loaded %d prediction rows across %d unique meters.",
            len(df_preds),
            df_preds["meter_id"].n_unique(),
        )

        # Step 1: Generate Primary Prioritized Inspection Queue
        logger.info(
            "Prioritizing inspection queue under primary rule: %s...",
            self.decision_settings.decision_rule.value,
        )
        df_tickets = self.prioritizer.prioritize(df_preds)
        n_candidates = len(df_tickets)
        n_inspections = int(df_tickets.get_column("inspection_recommended").sum())
        logger.info(
            "Decision engine evaluated %d candidates: %d recommended for physical inspection.",
            n_candidates,
            n_inspections,
        )

        # Step 2: Export Canonical Tickets Datasets
        logger.info("Exporting canonical inspection ticket artifacts...")
        tickets_parquet_path = out_dir / "inspection_tickets.parquet"
        df_tickets.write_parquet(tickets_parquet_path)

        tickets_csv_path = out_dir / "inspection_tickets.csv"
        # Export CSV for inspection audit (head 5000 if large for readability)
        df_tickets.head(5000).write_csv(tickets_csv_path)

        # Export top 100 dispatch tickets
        top_100_csv = out_dir / "top_100_inspection_tickets.csv"
        df_tickets.head(100).write_csv(top_100_csv)

        # Step 3: Run Decision Policy Comparison (Fixed 0.5 vs. Bayes Cost vs. Dynamic ENV)
        logger.info(
            "Comparing decision policies: Fixed 0.5 vs. Bayes Cost Threshold vs. Dynamic ENV..."
        )
        policy_comparison = self.evaluator.compare_decision_policies(df_preds)

        # Step 4: Evaluate Top-K Inspection Ranking Capacity
        logger.info("Evaluating Top-K capacity metrics and cumulative yield...")
        top_k_metrics = self.evaluator.evaluate_top_k_ranking(df_tickets)

        # Step 5: Run Operational Scenario Sensitivity Analysis
        logger.info("Running operational economic scenario analysis...")
        scenario_metrics = self.evaluator.run_scenario_sensitivity(df_preds)

        # Step 6: Generate Publication-Grade Visualizations
        logger.info("Generating publication-grade decision visualizations...")
        visualizer = DecisionVisualizer(output_dir=figs_dir)

        env_arr = df_tickets.get_column("env").to_numpy().astype(np.float64)
        prob_arr = df_tickets.get_column("calibrated_probability").to_numpy().astype(np.float64)
        rev_arr = (
            df_tickets.get_column("estimated_recoverable_revenue").to_numpy().astype(np.float64)
        )

        # 1. ENV Distribution
        visualizer.plot_env_distribution(env_values=env_arr)

        # 2. Probability vs. ENV scatter
        visualizer.plot_probability_vs_env(
            probabilities=prob_arr,
            env_values=env_arr,
            recoverable_revenue=rev_arr,
        )

        # 3. Dynamic Threshold Response Curve
        visualizer.plot_threshold_vs_financial_exposure(
            dispatch_cost=self.decision_settings.dispatch_cost,
        )

        # 4. Cumulative ENV Ranking Curve (ENV vs. Probability-only)
        # Create probability-ranked baseline for comparison
        df_prob_ranked = df_tickets.sort("calibrated_probability", descending=True)
        prob_env_arr = df_prob_ranked.get_column("env").to_numpy().astype(np.float64)
        visualizer.plot_cumulative_env_by_rank(
            env_ranked_env=env_arr,
            prob_ranked_env=prob_env_arr,
            top_n=1000,
        )

        # 5. Policy Comparison Bar Chart
        visualizer.plot_policy_comparison_bar(comparison_dict=policy_comparison)

        # Step 7: Save Comparison Reports & JSON Summaries
        summary_results = {
            "execution_time_seconds": round(time.time() - start_time, 2),
            "decision_settings": {
                "decision_rule": self.decision_settings.decision_rule.value,
                "dispatch_cost": self.decision_settings.dispatch_cost,
                "default_tariff": self.decision_settings.default_tariff,
                "recovery_factor": self.decision_settings.recovery_factor,
                "undetected_cycles": self.decision_settings.undetected_cycles,
                "fixed_threshold": self.decision_settings.fixed_threshold,
                "capacity_policy": self.decision_settings.capacity_policy.value,
                "ranking_strategy": self.decision_settings.ranking_strategy.value,
                "aggregation_period": self.decision_settings.aggregation_period.value,
            },
            "primary_queue_summary": self.evaluator.evaluate_policy(df_tickets),
            "policy_comparison": policy_comparison,
            "top_k_ranking": top_k_metrics,
            "scenario_sensitivity": scenario_metrics,
        }

        # Save JSON
        json_report_path = out_dir / "decision_comparison.json"
        with open(json_report_path, "w", encoding="utf-8") as f:
            json.dump(summary_results, f, indent=2)

        # Save Markdown Report
        report_md_path = out_dir / "decision_comparison_report.md"
        self._write_markdown_report(summary_results, report_md_path)

        # Step 8: MLflow Experiment Tracking
        if enable_mlflow:
            logger.info("Logging Phase 7 decision engine results to MLflow...")
            try:
                tracker = MLflowTracker(
                    experiment_name=self.settings.tracking.experiment_name,
                    tracking_uri=self.settings.tracking.tracking_uri,
                )
                prim_sum = summary_results["primary_queue_summary"]
                with tracker.start_run(
                    run_name=f"decision_engine_{self.decision_settings.decision_rule.value}",
                    tags={
                        "phase": "7",
                        "component": "decision_engine",
                        "rule": self.decision_settings.decision_rule.value,
                        "ranking": self.decision_settings.ranking_strategy.value,
                    },
                ):
                    tracker.log_params(
                        {
                            "decision_rule": self.decision_settings.decision_rule.value,
                            "dispatch_cost": self.decision_settings.dispatch_cost,
                            "tariff": self.decision_settings.default_tariff,
                            "recovery_factor": self.decision_settings.recovery_factor,
                            "undetected_cycles": self.decision_settings.undetected_cycles,
                            "fixed_threshold": self.decision_settings.fixed_threshold,
                            "capacity_policy": self.decision_settings.capacity_policy.value,
                            "ranking_strategy": self.decision_settings.ranking_strategy.value,
                        }
                    )
                    metrics_to_log: dict[str, float] = {
                        "total_candidates": float(prim_sum["total_candidates"]),
                        "inspections_recommended": float(prim_sum["inspections_recommended"]),
                        "inspection_rate_pct": float(prim_sum["inspection_rate_pct"]),
                        "expected_gross_recovery": float(
                            prim_sum["expected_financials"]["expected_gross_recovery"]
                        ),
                        "expected_dispatch_cost": float(
                            prim_sum["expected_financials"]["expected_dispatch_cost"]
                        ),
                        "expected_net_value": float(
                            prim_sum["expected_financials"]["expected_net_value"]
                        ),
                        "mean_env_per_ticket": float(
                            prim_sum["expected_financials"]["mean_env_per_ticket"]
                        ),
                        "median_env_per_ticket": float(
                            prim_sum["expected_financials"]["median_env_per_ticket"]
                        ),
                        "max_env": float(prim_sum["expected_financials"]["max_env"]),
                    }
                    if "realized_evaluation" in prim_sum:
                        real = prim_sum["realized_evaluation"]
                        metrics_to_log.update(
                            {
                                "realized_tp": float(real["tp"]),
                                "realized_fp": float(real["fp"]),
                                "realized_fn": float(real["fn"]),
                                "realized_precision": float(real["precision"]),
                                "realized_recall": float(real["recall"]),
                                "realized_f1": float(real["f1_score"]),
                                "realized_dispatch_cost": float(
                                    real["realized_total_dispatch_cost"]
                                ),
                                "realized_gross_recovery": float(real["realized_gross_recovery"]),
                                "realized_net_recovery": float(real["realized_net_recovery"]),
                                "realized_total_loss": float(
                                    real["realized_total_operational_loss"]
                                ),
                            }
                        )
                    tracker.log_metrics(metrics_to_log)
                    tracker.log_artifact(str(json_report_path))
                    tracker.log_artifact(str(report_md_path))
                    tracker.log_artifact(str(figs_dir))
                    tracker.log_artifact(str(top_100_csv))
                logger.info("Phase 7 decision engine successfully tracked to MLflow.")
            except Exception as e:
                logger.warning(f"Failed to log Phase 7 to MLflow: {e}")

        total_env_val = summary_results["primary_queue_summary"]["expected_financials"][
            "expected_net_value"
        ]
        logger.info(
            f"Phase 7 decision pipeline completed in {time.time() - start_time:.2f}s. "
            f"Recommended: {n_inspections} tickets (Total ENV: ${total_env_val:,.2f})."
        )
        return summary_results

    def _write_markdown_report(self, summary: dict[str, Any], path: Path) -> None:
        """Write professional Markdown audit report comparing decision policies."""
        p_comp = summary["policy_comparison"]
        top_k = summary["top_k_ranking"]
        scenarios = summary["scenario_sensitivity"]

        lines = [
            "# Grid-Guard Phase 7: Dynamic Thresholding, Expected Net Value & Inspection Prioritization Report",
            "",
            "## 1. Executive Summary",
            "",
            "In electricity Non-Technical Loss (NTL) detection, **prediction probability alone is not the final inspection decision**.",
            "Deploying physical field inspection crews incurs a non-trivial fixed operational cost ($C_{\\text{dispatch}} = $100.00).",
            "A conventional fixed-threshold model (e.g. $p \\ge 0.5$) commits severe economic errors:",
            "1. It dispatches costly crews to low-consumption residential accounts with high detection probability but negligible recoverable revenue ($ENV < 0$).",
            "2. It ignores high-volume industrial/commercial diversions with moderate probability where potential recovery exceeds inspection fees by orders of magnitude.",
            "",
            "In Phase 7, Grid-Guard establishes the **operational decision engine**:",
            "- Calculates per-meter dynamic thresholds: **Bayes Cost Threshold** ($\\tau_{\\text{cost}}$) and **Direct ENV Threshold** ($\\tau_{\\text{env}}$).",
            "- Computes **Expected Net Value**: $\\text{ENV}_i = p_i \\times R_i - C_{\\text{dispatch}}$.",
            "- Dispatches inspections only when economically justified ($\\text{ENV}_i > 0$).",
            "- Ranks candidates into a prioritized work-order queue based on expected financial yield.",
            "",
            "---",
            "",
            "## 2. Decision Logic & Mathematical Formulation",
            "",
            "### 2.1 Bayes Cost Threshold (Error Loss Minimization)",
            "Comparing expected cost of inspecting vs. not inspecting:",
            "$$\\tau_{\\text{cost}, i} = \\frac{C_{\\text{dispatch}}}{C_{\\text{dispatch}} + C_{FN, i}}$$",
            "where $C_{FN, i}$ is the financial penalty of failing to inspect a tampered meter. As potential leakage $C_{FN, i} \\to \\infty$, $\\tau_{\\text{cost}, i} \\to 0$.",
            "",
            "### 2.2 Direct ENV Economic Threshold (Positive Net Recovery)",
            "Inspecting yields positive expected financial return when:",
            "$$\\text{ENV}_i = p_i \\times R_i - C_{\\text{dispatch}} > 0 \\iff p_i > \\frac{C_{\\text{dispatch}}}{R_i} = \\tau_{\\text{env}, i}$$",
            "where $R_i$ is the estimated recoverable tariff revenue. When $R_i \\le 0$, $\\tau_{\\text{env}, i} = \\infty$, preventing loss-making dispatches.",
            "",
            "---",
            "",
            "## 3. Controlled Policy Benchmark: Fixed 0.5 vs. Bayes Cost vs. Dynamic ENV",
            "",
            "| Operational Metric | Policy A: Fixed Threshold ($p \\ge 0.5$) | Policy B: Bayes Cost Threshold ($p \\ge \\tau_{\\text{cost}}$) | Policy C: Dynamic ENV Rule ($\\text{ENV} > 0$) |",
            "|---|---|---|---|",
        ]

        p_fixed = p_comp["fixed_threshold_0.5"]
        p_bayes = p_comp["bayes_cost_threshold"]
        p_env = p_comp["dynamic_env_rule"]

        lines.extend(
            [
                f"| **Candidates Evaluated** | `{p_fixed['total_candidates']:,}` | `{p_bayes['total_candidates']:,}` | `{p_env['total_candidates']:,}` |",
                f"| **Inspections Recommended** | `{p_fixed['inspections_recommended']:,}` | `{p_bayes['inspections_recommended']:,}` | `{p_env['inspections_recommended']:,}` |",
                f"| **Inspection Rate** | `{p_fixed['inspection_rate_pct']:.2f}%` | `{p_bayes['inspection_rate_pct']:.2f}%` | `{p_env['inspection_rate_pct']:.2f}%` |",
                f"| **Expected Gross Recovery** | `${p_fixed['expected_financials']['expected_gross_recovery']:,.2f}` | `${p_bayes['expected_financials']['expected_gross_recovery']:,.2f}` | `${p_env['expected_financials']['expected_gross_recovery']:,.2f}` |",
                f"| **Expected Dispatch Cost** | `${p_fixed['expected_financials']['expected_dispatch_cost']:,.2f}` | `${p_bayes['expected_financials']['expected_dispatch_cost']:,.2f}` | `${p_env['expected_financials']['expected_dispatch_cost']:,.2f}` |",
                f"| **Expected Net Value (ENV)** | `${p_fixed['expected_financials']['expected_net_value']:,.2f}` | `${p_bayes['expected_financials']['expected_net_value']:,.2f}` | **`${p_env['expected_financials']['expected_net_value']:,.2f}`** |",
                f"| **Mean ENV per Ticket** | `${p_fixed['expected_financials']['mean_env_per_ticket']:,.2f}` | `${p_bayes['expected_financials']['mean_env_per_ticket']:,.2f}` | **`${p_env['expected_financials']['mean_env_per_ticket']:,.2f}`** |",
            ]
        )

        if "realized_evaluation" in p_fixed and "realized_evaluation" in p_env:
            rf = p_fixed["realized_evaluation"]
            rb = p_bayes["realized_evaluation"]
            re = p_env["realized_evaluation"]
            lines.extend(
                [
                    f"| **Realized Precision** | `{rf['precision'] * 100:.2f}%` | `{rb['precision'] * 100:.2f}%` | `{re['precision'] * 100:.2f}%` |",
                    f"| **Realized Recall** | `{rf['recall'] * 100:.2f}%` | `{rb['recall'] * 100:.2f}%` | `{re['recall'] * 100:.2f}%` |",
                    f"| **Confirmed Thefts ($TP$)** | `{rf['tp']:,}` | `{rb['tp']:,}` | `{re['tp']:,}` |",
                    f"| **Wasted Dispatches ($FP$)** | `{rf['fp']:,}` | `{rb['fp']:,}` | `{re['fp']:,}` |",
                    f"| **Realized Total Dispatch Cost** | `${rf['realized_total_dispatch_cost']:,.2f}` | `${rb['realized_total_dispatch_cost']:,.2f}` | `${re['realized_total_dispatch_cost']:,.2f}` |",
                    f"| **Realized Gross Recovery** | `${rf['realized_gross_recovery']:,.2f}` | `${rb['realized_gross_recovery']:,.2f}` | `${re['realized_gross_recovery']:,.2f}` |",
                    f"| **Realized Net Recovery** | `${rf['realized_net_recovery']:,.2f}` | `${rb['realized_net_recovery']:,.2f}` | **`${re['realized_net_recovery']:,.2f}`** |",
                ]
            )

        lines.extend(
            [
                "",
                "---",
                "",
                "## 4. Top-K Field Inspection Prioritization Queue",
                "",
                "Utility field crews operate under finite monthly inspection capacity constraints ($K$).",
                "Sorting tickets by Expected Net Value ensures each dispatched crew captures maximum financial yield:",
                "",
                "| Capacity ($K$) | Inspected | Expected Gross Recovery | Expected Dispatch Cost | Expected Net Value | Precision@K | Realized Recovery | Realized Net Recovery |",
                "|---|---|---|---|---|---|---|---|",
            ]
        )

        for k_row in top_k:
            prec_str = (
                f"`{k_row.get('precision_at_k', 0.0) * 100:.1f}%`"
                if "precision_at_k" in k_row
                else "N/A"
            )
            real_rec = (
                f"`${k_row.get('realized_gross_recovery', 0.0):,.0f}`"
                if "realized_gross_recovery" in k_row
                else "N/A"
            )
            real_net = (
                f"`${k_row.get('realized_net_recovery', 0.0):,.0f}`"
                if "realized_net_recovery" in k_row
                else "N/A"
            )
            lines.append(
                f"| **Top {k_row['k']:,}** | `{k_row['inspections_evaluated']:,}` | "
                f"`${k_row['expected_gross_recovery']:,.2f}` | `${k_row['expected_dispatch_cost']:,.2f}` | "
                f"**`${k_row['expected_net_value']:,.2f}`** | {prec_str} | {real_rec} | {real_net} |"
            )

        lines.extend(
            [
                "",
                "---",
                "",
                "## 5. Economic Scenario Sensitivity Analysis",
                "",
                "| Scenario | Dispatch Cost | Recovery Factor | Recommended Tickets | Expected Gross Recovery | Expected Net Value | Mean ENV / Ticket |",
                "|---|---|---|---|---|---|---|",
            ]
        )

        for sc_name, sc_data in scenarios.items():
            lines.append(
                f"| **{sc_name}** | `${sc_data['dispatch_cost']:,.0f}` | `{sc_data['recovery_factor']:.2f}` | "
                f"`{sc_data['inspections_recommended']:,}` | `${sc_data['expected_gross_recovery']:,.2f}` | "
                f"**`${sc_data['expected_net_value']:,.2f}`** | `${sc_data['mean_env_per_ticket']:,.2f}` |"
            )

        lines.extend(
            [
                "",
                "---",
                "",
                "## 6. Operational Guardrails & Capacity Policy",
                "",
                "- **One Ticket Per Inspection Unit**: Multitemporal snapshot records are grouped to the latest evaluation snapshot (`latest_snapshot`), eliminating duplicate work orders.",
                "- **Strictly Positive ENV Policy**: Negative-ENV meters are rejected from dispatch by default, preventing wasteful quota-filling dispatches.",
                "- **Deterministic Work Orders**: Every ticket receives an immutable `ticket_id` derived cryptographically from `meter_id` and evaluation period.",
                "",
            ]
        )

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logger.info("Saved Markdown decision comparison report to '%s'.", path)
