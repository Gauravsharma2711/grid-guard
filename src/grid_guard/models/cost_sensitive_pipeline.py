"""Orchestration pipeline for Phase 6 Cost-Sensitive Learning, candidate experimentation, and multi-phase comparison."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from sklearn.metrics import precision_recall_curve

from grid_guard.config.cost_sensitive import CostNormalizationType
from grid_guard.config.settings import Settings, get_settings
from grid_guard.data.sampling import controlled_training_resample
from grid_guard.evaluation.calibration import CalibrationEvaluator
from grid_guard.evaluation.cost_analysis import (
    FinancialDiagnosticEvaluator,
    FinancialWeightBuilder,
)
from grid_guard.evaluation.financial import FinancialCostEvaluator, LeakageEstimator
from grid_guard.evaluation.metrics import ClassificationMetricsEvaluator, RankingEvaluator
from grid_guard.evaluation.plots import BaselineVisualizer, CostSensitiveVisualizer
from grid_guard.models.baseline import BaselineLightGBM
from grid_guard.models.cost_sensitive import CostSensitiveLightGBM
from grid_guard.models.imbalance import ImbalanceAwareLightGBM
from grid_guard.models.splitting import TemporalDataSplitter
from grid_guard.tracking.experiment import MLflowTracker

logger = logging.getLogger(__name__)


class CostSensitiveExperimentPipeline:
    """End-to-end pipeline for cost-sensitive training, candidate sensitivity analysis, and evaluation."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.splitter = TemporalDataSplitter(config=self.settings.baseline)
        self.leakage_estimator = LeakageEstimator(assumptions=self.settings.financial)
        self.cost_evaluator = FinancialCostEvaluator(assumptions=self.settings.financial)

    def run(
        self,
        feature_parquet_path: Path | str,
        output_dir: Path | str | None = None,
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """Execute Phase 6 cost-sensitive learning workflow and benchmarks.

        Args:
            feature_parquet_path: Path to canonical_features.parquet.
            output_dir: Target directory for artifacts.
            enable_mlflow: Whether to log runs to MLflow.

        Returns:
            Dictionary containing comparison results across Phase 4, Phase 5, and Phase 6.
        """
        start_time = time.time()
        in_path = Path(feature_parquet_path)
        out_dir = Path(output_dir or self.settings.artifacts_dir / "cost_sensitive")
        out_dir.mkdir(parents=True, exist_ok=True)
        figures_dir = out_dir / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Loading feature dataset from '{in_path}'...")
        df_raw = (
            pl.scan_parquet(in_path) if in_path.suffix == ".parquet" else pl.read_parquet(in_path)
        )

        # Step 1: Pre-calculate per-meter revenue leakage estimates
        logger.info("Enriching dataset with historical baseline and revenue leakage metrics...")
        df_enriched = self.leakage_estimator.estimate_leakage_polars(df_raw)

        # Step 2: Strict temporal train/val/test splitting
        logger.info("Partitioning data into strict non-overlapping temporal slices...")
        target_col = self.settings.baseline.target_col or "tamper_label"
        train_part, val_part, test_part = self.splitter.split(
            df_enriched,
            target_col=target_col,
            sampling_stride_days=self.settings.baseline.sampling_stride_days,
            test_final_snapshot_only=False,
        )

        # Step 3: Construct financial training weights strictly on training partition
        logger.info("Constructing financial error weights from training partition...")
        train_leakage_costs = (
            train_part.metadata.get_column("estimated_leakage_cost")
            .fill_null(0.0)
            .to_numpy()
            .astype(np.float64)
        )

        w_train_norm, w_train_raw, weight_audit = FinancialWeightBuilder.construct_training_weights(
            y_train=train_part.y,
            estimated_leakage_costs=train_leakage_costs,
            dispatch_cost=self.settings.cost_sensitive.dispatch_cost,
            min_fn_cost=self.settings.cost_sensitive.min_fn_cost,
            normalization=self.settings.cost_sensitive.cost_normalization,
            reference_scale=self.settings.cost_sensitive.reference_scale,
            cost_capping=self.settings.cost_sensitive.cost_capping,
            cost_cap_percentile=self.settings.cost_sensitive.cost_cap_percentile,
        )

        # Step 4: Define candidate experiment configurations on Validation Set
        candidate_configs: list[dict[str, Any]] = [
            {
                "name": "phase4_unweighted_baseline",
                "type": "unweighted_baseline",
                "normalization": "none",
                "capping": False,
            },
            {
                "name": "phase5_imbalance_champion",
                "type": "imbalance_oversample",
                "normalization": "none",
                "capping": False,
            },
            {
                "name": "phase6_cost_sensitive_dispatch_norm",
                "type": "cost_sensitive",
                "normalization": CostNormalizationType.DISPATCH_COST.value,
                "capping": False,
            },
            {
                "name": "phase6_cost_sensitive_mean_norm",
                "type": "cost_sensitive",
                "normalization": CostNormalizationType.MEAN.value,
                "capping": False,
            },
            {
                "name": "phase6_cost_sensitive_capped_p99",
                "type": "cost_sensitive",
                "normalization": CostNormalizationType.DISPATCH_COST.value,
                "capping": True,
                "cap_percentile": 99.0,
            },
        ]

        logger.info(
            f"Beginning validation experimentation across {len(candidate_configs)} candidate models..."
        )
        val_results: dict[str, dict[str, Any]] = {}
        fitted_models: dict[str, Any] = {}
        val_probs: dict[str, np.ndarray] = {}

        y_val_np = val_part.y.to_numpy().astype(np.int32)
        val_leakage_costs = (
            val_part.metadata.get_column("estimated_leakage_cost")
            .fill_null(0.0)
            .to_numpy()
            .astype(np.float64)
            if "estimated_leakage_cost" in val_part.metadata.columns
            else np.zeros(val_part.num_samples, dtype=np.float64)
        )

        for cfg in candidate_configs:
            c_name = cfg["name"]
            c_type = cfg["type"]
            logger.info(f"--- Training candidate model: {c_name} ({c_type}) ---")

            if c_type == "unweighted_baseline":
                model_cand = BaselineLightGBM(config=self.settings.baseline)
                eval_set = [(val_part.X, val_part.y)] if val_part.num_samples > 0 else None
                model_cand.fit(train_part.X, train_part.y, eval_set=eval_set)
                y_val_p = model_cand.predict_proba(val_part.X)
                y_val_hat = model_cand.predict(
                    val_part.X, threshold=self.settings.cost_sensitive.threshold
                )

            elif c_type == "imbalance_oversample":
                X_tr, y_tr, _, _ = controlled_training_resample(
                    X_train=train_part.X,
                    y_train=train_part.y,
                    meta_train=train_part.metadata,
                    strategy="controlled_oversample",
                    target_pos_ratio=0.20,
                    random_seed=self.settings.cost_sensitive.random_seed,
                )
                model_cand = ImbalanceAwareLightGBM(
                    base_config=self.settings.baseline,
                    imbalance_config=self.settings.imbalance,
                    scale_pos_weight=1.0,
                )
                eval_set = [(val_part.X, val_part.y)] if val_part.num_samples > 0 else None
                model_cand.fit(X_tr, y_tr, eval_set=eval_set)
                y_val_p = model_cand.predict_proba(val_part.X)
                y_val_hat = model_cand.predict(
                    val_part.X, threshold=self.settings.cost_sensitive.threshold
                )

            else:  # c_type == "cost_sensitive"
                # Construct candidate-specific weights
                c_norm = cfg["normalization"]
                c_cap = cfg.get("capping", False)
                c_cap_p = cfg.get("cap_percentile", 99.5)

                w_cand, _, _ = FinancialWeightBuilder.construct_training_weights(
                    y_train=train_part.y,
                    estimated_leakage_costs=train_leakage_costs,
                    dispatch_cost=self.settings.cost_sensitive.dispatch_cost,
                    min_fn_cost=self.settings.cost_sensitive.min_fn_cost,
                    normalization=c_norm,
                    cost_capping=c_cap,
                    cost_cap_percentile=c_cap_p,
                )

                model_cand = CostSensitiveLightGBM(
                    base_config=self.settings.baseline,
                    cost_config=self.settings.cost_sensitive,
                )
                eval_set = [(val_part.X, val_part.y)] if val_part.num_samples > 0 else None
                model_cand.fit(train_part.X, train_part.y, weights=w_cand, eval_set=eval_set)

                # Fit post-hoc probability calibration on validation data
                model_cand.fit_calibration(
                    X_val=val_part.X,
                    y_val=val_part.y,
                    method=self.settings.cost_sensitive.calibration_method,
                )

                y_val_p = model_cand.predict_proba(val_part.X)
                y_val_hat = model_cand.predict(
                    val_part.X, threshold=self.settings.cost_sensitive.threshold
                )

            fitted_models[c_name] = model_cand
            val_probs[c_name] = y_val_p

            stat_m = ClassificationMetricsEvaluator.evaluate(
                y_true=y_val_np, y_pred=y_val_hat, y_prob=y_val_p
            )
            topk_m = RankingEvaluator.evaluate_top_k(
                y_true=y_val_np, y_prob=y_val_p, k_values=self.settings.baseline.top_k_values
            )
            calib_m = CalibrationEvaluator.evaluate(y_true=y_val_np, y_prob=y_val_p, n_bins=10)
            fin_m = self.cost_evaluator.evaluate(
                y_true=y_val_np, y_pred=y_val_hat, leakage_costs=val_leakage_costs
            )

            val_results[c_name] = {
                "config": cfg,
                "statistical": stat_m,
                "ranking": topk_m,
                "calibration": calib_m,
                "financial": fin_m,
            }
            logger.info(
                f"Candidate '{c_name}' Validation: PR-AUC={stat_m['pr_auc']:.4f}, "
                f"Recall={stat_m['recall']:.2%}, Total Loss=${fin_m['financial_breakdown']['total_baseline_operational_loss']:,.2f}, "
                f"Brier={calib_m['brier_score']:.4f}"
            )

        # Step 5: Select Champion Cost-Sensitive Strategy strictly on Validation data
        cost_sensitive_cands = [c for c in candidate_configs if c["type"] == "cost_sensitive"]
        selection_metric = self.settings.cost_sensitive.selection_metric

        def get_loss(cand_name: str) -> float:
            return float(
                val_results[cand_name]["financial"]["financial_breakdown"][
                    "total_baseline_operational_loss"
                ]
            )

        def get_prauc(cand_name: str) -> float:
            return float(val_results[cand_name]["statistical"]["pr_auc"])

        if selection_metric == "total_operational_loss":
            champion_name = min(cost_sensitive_cands, key=lambda c: get_loss(c["name"]))["name"]
            logger.info(
                f"Selected Champion Model: '{champion_name}' with lowest validation "
                f"operational loss = ${get_loss(champion_name):,.2f}!"
            )
        else:
            champion_name = max(cost_sensitive_cands, key=lambda c: get_prauc(c["name"]))["name"]
            logger.info(
                f"Selected Champion Model: '{champion_name}' with highest validation "
                f"PR-AUC = {get_prauc(champion_name):.4f}!"
            )

        champion_model: CostSensitiveLightGBM = fitted_models[champion_name]

        # Step 6: Single-Pass Evaluation on Untouched Held-Out Test Partition
        logger.info(
            "Evaluating Phase 4 Baseline, Phase 5 Champion, and Phase 6 Champion on Test Partition..."
        )
        y_test_np = test_part.y.to_numpy().astype(np.int32)
        test_leakage_costs = (
            test_part.metadata.get_column("estimated_leakage_cost")
            .fill_null(0.0)
            .to_numpy()
            .astype(np.float64)
            if "estimated_leakage_cost" in test_part.metadata.columns
            else np.zeros(test_part.num_samples, dtype=np.float64)
        )

        test_evaluations: dict[str, Any] = {}
        test_probs: dict[str, np.ndarray] = {}

        benchmarks = [
            ("phase4_baseline", fitted_models["phase4_unweighted_baseline"]),
            ("phase5_imbalance_champion", fitted_models["phase5_imbalance_champion"]),
            ("phase6_cost_sensitive_champion", champion_model),
        ]

        for b_name, b_model in benchmarks:
            p_test = b_model.predict_proba(test_part.X)
            pred_test = b_model.predict(
                test_part.X, threshold=self.settings.cost_sensitive.threshold
            )
            test_probs[b_name] = p_test

            stat_test = ClassificationMetricsEvaluator.evaluate(
                y_true=y_test_np, y_pred=pred_test, y_prob=p_test
            )
            topk_test = RankingEvaluator.evaluate_top_k(
                y_true=y_test_np, y_prob=p_test, k_values=self.settings.baseline.top_k_values
            )
            calib_test = CalibrationEvaluator.evaluate(y_true=y_test_np, y_prob=p_test, n_bins=10)
            fin_test = self.cost_evaluator.evaluate(
                y_true=y_test_np, y_pred=pred_test, leakage_costs=test_leakage_costs
            )
            topk_fin = FinancialDiagnosticEvaluator.evaluate_top_k_financial(
                y_true=y_test_np,
                y_prob=p_test,
                leakage_costs=test_leakage_costs,
                k_values=self.settings.baseline.top_k_values,
                dispatch_cost=self.settings.cost_sensitive.dispatch_cost,
            )

            test_evaluations[b_name] = {
                "statistical": stat_test,
                "ranking": topk_test,
                "ranking_financial": topk_fin,
                "calibration": calib_test,
                "financial": fin_test,
            }

        # Threshold grid diagnostic evaluation on Phase 6 Champion
        threshold_grid = FinancialDiagnosticEvaluator.evaluate_threshold_grid(
            y_true=y_test_np,
            y_prob=test_probs["phase6_cost_sensitive_champion"],
            leakage_costs=test_leakage_costs,
            dispatch_cost=self.settings.cost_sensitive.dispatch_cost,
        )

        # Step 7: Export Predictions & Trained Champion Model Checkpoint
        logger.info("Exporting champion predictions artifact on held-out test partition...")
        df_preds = pl.DataFrame(
            {
                "meter_id": test_part.metadata.get_column("meter_id"),
                "timestamp": test_part.metadata.get_column("timestamp"),
                "tamper_label": test_part.y,
                "raw_margin": champion_model.predict_margins(test_part.X),
                "uncalibrated_prob": champion_model.predict_raw_proba(test_part.X),
                "predicted_prob": test_probs["phase6_cost_sensitive_champion"],
                "prediction": (
                    test_probs["phase6_cost_sensitive_champion"]
                    >= self.settings.cost_sensitive.threshold
                ).astype(np.int32),
                "estimated_leakage_cost": test_leakage_costs,
            }
        )
        preds_path = out_dir / "champion_predictions.parquet"
        df_preds.write_parquet(preds_path)

        model_path = out_dir / "champion_model.txt"
        champion_model.save(model_path)

        # Step 8: Generate Diagnostic Figures
        logger.info("Generating publication-grade diagnostic plots...")
        visualizer = CostSensitiveVisualizer(output_dir=figures_dir)
        base_visualizer = BaselineVisualizer(output_dir=figures_dir)

        # 1. Expected cost curve
        visualizer.plot_expected_cost_curve(
            grid_data=threshold_grid, output_filename="expected_cost_curve.png"
        )

        # 2. Financial weight distribution
        visualizer.plot_financial_weight_distribution(
            c_fn_costs=train_leakage_costs[train_part.y.to_numpy() == 1],
            dispatch_cost=self.settings.cost_sensitive.dispatch_cost,
            output_filename="financial_weight_distribution.png",
        )

        # 3. Three-phase PR curves
        pr_curves_data = {}
        for b_name, b_prob in test_probs.items():
            prec_c, rec_c, _ = precision_recall_curve(y_test_np, b_prob)
            pr_curves_data[b_name] = {
                "recall": rec_c,
                "precision": prec_c,
                "pr_auc": test_evaluations[b_name]["statistical"]["pr_auc"],
            }
        visualizer.plot_three_phase_pr_curves(
            curves_dict=pr_curves_data, output_filename="pr_curves_three_phase.png"
        )

        # 4. Three-phase financial loss
        loss_data = {
            "Phase 4 Baseline": {
                "fp_cost": test_evaluations["phase4_baseline"]["financial"]["financial_breakdown"][
                    "total_fp_dispatch_cost"
                ],
                "fn_cost": test_evaluations["phase4_baseline"]["financial"]["financial_breakdown"][
                    "total_fn_leakage_cost"
                ],
                "total_loss": test_evaluations["phase4_baseline"]["financial"][
                    "financial_breakdown"
                ]["total_baseline_operational_loss"],
            },
            "Phase 5 Imbalance": {
                "fp_cost": test_evaluations["phase5_imbalance_champion"]["financial"][
                    "financial_breakdown"
                ]["total_fp_dispatch_cost"],
                "fn_cost": test_evaluations["phase5_imbalance_champion"]["financial"][
                    "financial_breakdown"
                ]["total_fn_leakage_cost"],
                "total_loss": test_evaluations["phase5_imbalance_champion"]["financial"][
                    "financial_breakdown"
                ]["total_baseline_operational_loss"],
            },
            "Phase 6 Cost-Sensitive": {
                "fp_cost": test_evaluations["phase6_cost_sensitive_champion"]["financial"][
                    "financial_breakdown"
                ]["total_fp_dispatch_cost"],
                "fn_cost": test_evaluations["phase6_cost_sensitive_champion"]["financial"][
                    "financial_breakdown"
                ]["total_fn_leakage_cost"],
                "total_loss": test_evaluations["phase6_cost_sensitive_champion"]["financial"][
                    "financial_breakdown"
                ]["total_baseline_operational_loss"],
            },
        }
        visualizer.plot_three_phase_financial_loss(
            losses_dict=loss_data, output_filename="financial_loss_three_phase.png"
        )

        # 5. Feature importance shift
        df_p4_imp = fitted_models["phase4_unweighted_baseline"].get_feature_importance("gain")
        df_p6_imp = champion_model.get_feature_importance("gain")
        visualizer.plot_feature_importance_comparison(
            df_p4=df_p4_imp, df_p6=df_p6_imp, output_filename="feature_importance_shift.png"
        )

        # 6. Confusion matrix for champion
        base_visualizer.plot_confusion_matrix(
            cm_dict=test_evaluations["phase6_cost_sensitive_champion"]["statistical"][
                "confusion_matrix"
            ],
            output_filename="confusion_matrix_cost_sensitive.png",
        )

        # Step 9: Save Comprehensive Comparison Summary & Reports
        summary_results = {
            "execution_time_seconds": round(time.time() - start_time, 2),
            "weight_audit": weight_audit.to_dict(),
            "selection_criterion": {
                "metric": selection_metric,
                "champion_strategy": champion_name,
            },
            "validation_experiments": val_results,
            "test_evaluation": test_evaluations,
            "threshold_grid_diagnostic": threshold_grid,
        }

        # Save JSON audit
        summary_json_path = out_dir / "cost_sensitive_comparison.json"
        with open(summary_json_path, "w", encoding="utf-8") as f:
            json.dump(summary_results, f, indent=2)

        # Save Weight Audit Report
        weight_audit_path = out_dir / "weight_audit_report.json"
        with open(weight_audit_path, "w", encoding="utf-8") as f:
            json.dump(weight_audit.to_dict(), f, indent=2)

        # Save Markdown Report
        self._write_comparison_report(
            summary_results=summary_results,
            report_path=out_dir / "cost_sensitive_comparison_report.md",
        )

        # Step 10: MLflow Logging
        if enable_mlflow:
            logger.info("Logging Phase 6 experiments to MLflow...")
            try:
                tracker = MLflowTracker(
                    experiment_name=self.settings.tracking.experiment_name,
                    tracking_uri=self.settings.tracking.tracking_uri,
                )
                c_test = test_evaluations["phase6_cost_sensitive_champion"]
                with tracker.start_run(
                    run_name=f"cost_sensitive_{champion_name}",
                    tags={
                        "phase": "6",
                        "model": "cost_sensitive_lightgbm",
                        "objective": self.settings.cost_sensitive.objective_name,
                        "normalization": str(self.settings.cost_sensitive.cost_normalization),
                    },
                ):
                    tracker.log_params(
                        {
                            "objective_name": self.settings.cost_sensitive.objective_name,
                            "dispatch_cost": self.settings.cost_sensitive.dispatch_cost,
                            "min_fn_cost": self.settings.cost_sensitive.min_fn_cost,
                            "cost_normalization": str(
                                self.settings.cost_sensitive.cost_normalization
                            ),
                            "cost_capping": self.settings.cost_sensitive.cost_capping,
                            "calibration_method": str(
                                self.settings.cost_sensitive.calibration_method
                            ),
                            "threshold": self.settings.cost_sensitive.threshold,
                            "train_samples": train_part.num_samples,
                            "features_count": len(train_part.feature_names),
                        }
                    )
                    tracker.log_metrics(
                        {
                            "test_pr_auc": c_test["statistical"]["pr_auc"],
                            "test_roc_auc": c_test["statistical"]["roc_auc"],
                            "test_precision": c_test["statistical"]["precision"],
                            "test_recall": c_test["statistical"]["recall"],
                            "test_f1": c_test["statistical"]["f1_score"],
                            "test_tp": float(c_test["statistical"]["confusion_matrix"]["tp"]),
                            "test_fp": float(c_test["statistical"]["confusion_matrix"]["fp"]),
                            "test_fn": float(c_test["statistical"]["confusion_matrix"]["fn"]),
                            "test_brier_score": c_test["calibration"]["brier_score"],
                            "test_fp_dispatch_cost": c_test["financial"]["financial_breakdown"][
                                "total_fp_dispatch_cost"
                            ],
                            "test_fn_leakage_cost": c_test["financial"]["financial_breakdown"][
                                "total_fn_leakage_cost"
                            ],
                            "test_total_loss": c_test["financial"]["financial_breakdown"][
                                "total_baseline_operational_loss"
                            ],
                            "test_gross_recovery": c_test["financial"]["financial_breakdown"][
                                "estimated_gross_recovery"
                            ],
                            "test_net_recovery": c_test["financial"]["financial_breakdown"][
                                "estimated_net_recovery"
                            ],
                        }
                    )
                    tracker.log_artifact(str(summary_json_path))
                    tracker.log_artifact(str(out_dir / "cost_sensitive_comparison_report.md"))
                    tracker.log_artifact(str(out_dir / "figures"))
            except Exception as e:
                logger.warning(f"Failed to log run to MLflow: {e}")

        logger.info(
            f"Phase 6 Cost-Sensitive pipeline completed in {time.time() - start_time:.2f}s! "
            f"Champion='{champion_name}', Test PR-AUC={test_evaluations['phase6_cost_sensitive_champion']['statistical']['pr_auc']:.4f}, "
            f"Total Loss=${test_evaluations['phase6_cost_sensitive_champion']['financial']['financial_breakdown']['total_baseline_operational_loss']:,.2f}."
        )
        return summary_results

    def _write_comparison_report(
        self,
        summary_results: dict[str, Any],
        report_path: Path,
    ) -> None:
        """Generate human-readable Markdown comparison report for Phase 4 -> Phase 5 -> Phase 6."""
        wa = summary_results["weight_audit"]
        p4 = summary_results["test_evaluation"]["phase4_baseline"]
        p5 = summary_results["test_evaluation"]["phase5_imbalance_champion"]
        p6 = summary_results["test_evaluation"]["phase6_cost_sensitive_champion"]
        champ_name = summary_results["selection_criterion"]["champion_strategy"]

        # Ranking table rows
        ranking_rows = []
        for k_str, k_data in p4["ranking"].items():
            p5_data = p5["ranking"].get(k_str, {})
            p6_data = p6["ranking"].get(k_str, {})
            ranking_rows.append(
                f"| **Top {k_str}** | `{k_data.get('precision_at_k', 0.0):.1%}` | "
                f"`{p5_data.get('precision_at_k', 0.0):.1%}` | `{p6_data.get('precision_at_k', 0.0):.1%}` | "
                f"`{k_data.get('true_positives', 0):,}` | `{p5_data.get('true_positives', 0):,}` | `{p6_data.get('true_positives', 0):,}` |"
            )
        ranking_table_body = "\n".join(ranking_rows)

        md_content = f"""# Grid-Guard Phase 6: Cost-Sensitive Custom Objective & Financially Weighted Learning Report

## 1. Executive Summary

In electricity Non-Technical Loss (NTL) detection, classification errors carry severely asymmetric financial consequences:
- **False Positive ($FP$)**: Wastes a fixed inspection crew dispatch fee ($C_{{FP}} = $100.00).
- **False Negative ($FN$)**: Allows unmetered consumption to persist undetected, forfeiting thousands of dollars in cumulative tariff revenue ($C_{{FN, i}}$).

In Phase 6, we implemented a mathematically verified, second-order differentiable **Cost-Sensitive Weighted Logistic Objective**:
$$\\mathcal{{L}}_i(z_i) = w_i \\left[ -y_i \\ln(p_i) - (1 - y_i) \\ln(1 - p_i) \\right]$$
where $w_i = C_{{FN, i}}$ for tampering examples and $w_i = C_{{FP}}$ for honest examples, with exact gradient $g_i = w_i (p_i - y_i)$ and strictly positive Hessian $h_i = w_i p_i (1 - p_i)$.

- **Selected Champion Variant**: `{champ_name}`
- **Selection Criterion**: Validation `{summary_results["selection_criterion"]["metric"]}`
- **Evaluation Protocol**: Evaluated strictly once on the untouched held-out test partition (`2016-06-01` to `2016-10-31`).

---

## 2. Financial Training Weight Audit (Training Partition)

| Financial Parameter | Source Type | Value / Distribution | Operational Description |
|---|---|---|---|
| **Fixed Dispatch Cost ($C_{{FP}}$)** | Assumed | **${wa["c_fp_dispatch_cost"]:,.2f}** | Fixed crew dispatch expense per physical inspection |
| **Minimum Positive Cost Floor** | Assumed | **$100.00** | Floor on positive class error cost ensuring $h_i > 0$ |
| **Min Leakage Cost ($C_{{FN, \\min}}$)** | Derived | **${wa["c_fn_min"]:,.2f}** | Smallest positive error consequence |
| **Median Leakage Cost ($C_{{FN, \\text{{median}}}}$)** | Derived | **${wa["c_fn_median"]:,.2f}** | 50th percentile of annual theft leakage |
| **Mean Leakage Cost ($C_{{FN, \\text{{mean}}}}$)** | Derived | **${wa["c_fn_mean"]:,.2f}** | Average unmetered revenue loss |
| **99th Percentile Leakage Cost** | Derived | **${wa["c_fn_p99"]:,.2f}** | High-volume industrial/commercial theft threshold |
| **Max Leakage Cost ($C_{{FN, \\max}}$)** | Derived | **${wa["c_fn_max"]:,.2f}** | Maximum single-premise annual theft |
| **Median Penalty Ratio ($C_{{FN}} / C_{{FP}}$)** | Derived | **{wa["weight_ratio_median_pos_to_neg"]:.2f} : 1** | Ratio of positive error penalty to false alarm |
| **Global Reference Scale ($S_{{\\text{{ref}}}}$)** | Derived | **${wa["reference_scale"]:,.2f}** | Normalization scale (Method: `{wa["normalization_strategy"]}`) |
| **Normalized Weight Range** | Derived | **[{wa["weight_min"]:.3f}, {wa["weight_max"]:.3f}]** | Well-conditioned boosting weight range |

---

## 3. Three-Phase Performance Evolution: Baseline vs. Imbalance vs. Cost-Sensitive

| Metric | Phase 4 (Unweighted Baseline) | Phase 5 (Imbalance-Aware) | Phase 6 (Cost-Sensitive) | Absolute Shift (P4 $\\to$ P6) |
|---|---|---|---|---|
| **PR-AUC** | `{p4["statistical"]["pr_auc"]:.4f}` | `{p5["statistical"]["pr_auc"]:.4f}` | `{p6["statistical"]["pr_auc"]:.4f}` | `{p6["statistical"]["pr_auc"] - p4["statistical"]["pr_auc"]:+.4f}` |
| **ROC-AUC** | `{p4["statistical"]["roc_auc"]:.4f}` | `{p5["statistical"]["roc_auc"]:.4f}` | `{p6["statistical"]["roc_auc"]:.4f}` | `{p6["statistical"]["roc_auc"] - p4["statistical"]["roc_auc"]:+.4f}` |
| **Theft Recall** | `{p4["statistical"]["recall"]:.2%}` | `{p5["statistical"]["recall"]:.2%}` | `{p6["statistical"]["recall"]:.2%}` | `{p6["statistical"]["recall"] - p4["statistical"]["recall"]:+.2%}` |
| **Precision** | `{p4["statistical"]["precision"]:.2%}` | `{p5["statistical"]["precision"]:.2%}` | `{p6["statistical"]["precision"]:.2%}` | `{p6["statistical"]["precision"] - p4["statistical"]["precision"]:+.2%}` |
| **F1-Score** | `{p4["statistical"]["f1_score"]:.4f}` | `{p5["statistical"]["f1_score"]:.4f}` | `{p6["statistical"]["f1_score"]:.4f}` | `{p6["statistical"]["f1_score"] - p4["statistical"]["f1_score"]:+.4f}` |
| **True Positives ($TP$)** | `{p4["statistical"]["confusion_matrix"]["tp"]:,}` | `{p5["statistical"]["confusion_matrix"]["tp"]:,}` | `{p6["statistical"]["confusion_matrix"]["tp"]:,}` | `{p6["statistical"]["confusion_matrix"]["tp"] - p4["statistical"]["confusion_matrix"]["tp"]:+,}` |
| **False Negatives ($FN$)** | `{p4["statistical"]["confusion_matrix"]["fn"]:,}` | `{p5["statistical"]["confusion_matrix"]["fn"]:,}` | `{p6["statistical"]["confusion_matrix"]["fn"]:,}` | `{p6["statistical"]["confusion_matrix"]["fn"] - p4["statistical"]["confusion_matrix"]["fn"]:+,}` |
| **False Positives ($FP$)** | `{p4["statistical"]["confusion_matrix"]["fp"]:,}` | `{p5["statistical"]["confusion_matrix"]["fp"]:,}` | `{p6["statistical"]["confusion_matrix"]["fp"]:,}` | `{p6["statistical"]["confusion_matrix"]["fp"] - p4["statistical"]["confusion_matrix"]["fp"]:+,}` |
| **Brier Score (Calibration)** | `{p4["calibration"]["brier_score"]:.4f}` | `{p5["calibration"]["brier_score"]:.4f}` | `{p6["calibration"]["brier_score"]:.4f}` | `{p6["calibration"]["brier_score"] - p4["calibration"]["brier_score"]:+.4f}` |
| **Wasted FP Dispatch Cost** | `${p4["financial"]["financial_breakdown"]["total_fp_dispatch_cost"]:,.2f}` | `${p5["financial"]["financial_breakdown"]["total_fp_dispatch_cost"]:,.2f}` | `${p6["financial"]["financial_breakdown"]["total_fp_dispatch_cost"]:,.2f}` | `${p6["financial"]["financial_breakdown"]["total_fp_dispatch_cost"] - p4["financial"]["financial_breakdown"]["total_fp_dispatch_cost"]:+,.2f}` |
| **Undetected FN Leakage** | `${p4["financial"]["financial_breakdown"]["total_fn_leakage_cost"]:,.2f}` | `${p5["financial"]["financial_breakdown"]["total_fn_leakage_cost"]:,.2f}` | `${p6["financial"]["financial_breakdown"]["total_fn_leakage_cost"]:,.2f}` | `${p6["financial"]["financial_breakdown"]["total_fn_leakage_cost"] - p4["financial"]["financial_breakdown"]["total_fn_leakage_cost"]:+,.2f}` |
| **Total Operational Loss** | `${p4["financial"]["financial_breakdown"]["total_baseline_operational_loss"]:,.2f}` | `${p5["financial"]["financial_breakdown"]["total_baseline_operational_loss"]:,.2f}` | `${p6["financial"]["financial_breakdown"]["total_baseline_operational_loss"]:,.2f}` | `${p6["financial"]["financial_breakdown"]["total_baseline_operational_loss"] - p4["financial"]["financial_breakdown"]["total_baseline_operational_loss"]:+,.2f}` |

---

## 4. Operational Inspection Ranking (Precision@K & Cumulative Value)

| Inspection Capacity ($K$) | Phase 4 Precision@K | Phase 5 Precision@K | Phase 6 Precision@K | Phase 4 TP | Phase 5 TP | Phase 6 TP |
|---|---|---|---|---|---|---|
{ranking_table_body}

---

## 5. Technical Insights & Mathematical Distinctions

1. **Why Financial Weighting Differs from Class Imbalance Handling**:
   - Class weighting (Phase 5) assigns a uniform scalar $w_{{\\text{{pos}}}}$ to all positive instances based purely on relative empirical frequency ($N_{{\\text{{neg}}}} / N_{{\\text{{pos}}}}$). It treats a tiny $50 theft identically to a $15,000 industrial diversion.
   - Cost-sensitive weighting (Phase 6) assigns per-instance financial penalties $w_i = C_{{FN, i}}$, compelling tree splitters to prioritize splits that isolate large-volume diversions.

2. **Differentiable Surrogate vs. Business Objective**:
   - The business loss $L_{{\\text{{business}}}} = \\sum [ y_i (1 - p_i) C_{{FN, i}} + (1 - y_i) p_i C_{{FP}} ]$ is linear in probability and yields zero second derivatives.
   - The weighted logistic surrogate $\\mathcal{{L}}_i(z_i)$ provides the strictly positive Hessian $h_i = w_i p_i (1 - p_i) > 0$ required for stable second-order gradient boosting.
"""
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info(f"Saved Markdown comparison report to '{report_path}'.")
