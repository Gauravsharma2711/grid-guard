"""End-to-end baseline training, financial evaluation, artifact export, and MLflow logging."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from grid_guard.config.settings import Settings, get_settings
from grid_guard.evaluation.financial import FinancialCostEvaluator, LeakageEstimator
from grid_guard.evaluation.metrics import (
    ClassificationMetricsEvaluator,
    RankingEvaluator,
)
from grid_guard.evaluation.plots import BaselineVisualizer
from grid_guard.models.baseline import BaselineLightGBM
from grid_guard.models.splitting import TemporalDataSplitter
from grid_guard.tracking.experiment import ExperimentTracker

logger = logging.getLogger(__name__)


class BaselinePipeline:
    """Orchestrates temporal splitting, unweighted training, financial evaluation, and reporting."""

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
        """Execute complete Phase 4 baseline modeling and evaluation workflow.

        Args:
            feature_parquet_path: Path to canonical_features.parquet.
            output_dir: Directory to save baseline artifacts and figures.
            enable_mlflow: Whether to log run to MLflow experiment tracker.

        Returns:
            Dictionary containing combined statistical, ranking, and financial metrics.
        """
        start_time = time.time()
        in_path = Path(feature_parquet_path)
        out_dir = Path(output_dir or self.settings.artifacts_dir / "baseline")
        out_dir.mkdir(parents=True, exist_ok=True)
        figures_dir = out_dir / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Loading canonical feature dataset from '{in_path}'...")
        df_raw = (
            pl.scan_parquet(in_path) if in_path.suffix == ".parquet" else pl.read_parquet(in_path)
        )

        # Step 1: Compute per-meter revenue leakage estimates
        logger.info("Computing revenue leakage volume and financial impact estimates...")
        df_enriched = self.leakage_estimator.estimate_leakage_polars(df_raw)

        # Step 2: Temporal Train/Val/Test Splitting
        logger.info("Partitioning data into strict temporal train, val, and test slices...")
        train_part, val_part, test_part = self.splitter.split(
            df_enriched,
            target_col=self.settings.baseline.target_col or "tamper_label",
            sampling_stride_days=self.settings.baseline.sampling_stride_days,
            test_final_snapshot_only=False,
        )

        # Step 3: Train unweighted LightGBM baseline
        logger.info("Training unweighted LightGBM baseline classifier...")
        model = BaselineLightGBM(config=self.settings.baseline)
        eval_set = [(val_part.X, val_part.y)] if val_part.num_samples > 0 else None
        model.fit(train_part.X, train_part.y, eval_set=eval_set)

        # Save trained model artifact
        model_path = out_dir / "baseline_lightgbm.txt"
        model.save(model_path)

        # Step 4: Evaluate ONCE on held-out test partition
        logger.info(f"Scoring {test_part.num_samples:,} held-out test observations...")
        y_test_np = test_part.y.to_numpy().astype(np.int32)
        y_prob = model.predict_proba(test_part.X)
        y_pred = model.predict(test_part.X, threshold=self.settings.baseline.threshold)

        # Extract per-sample leakage cost from test metadata
        if "estimated_leakage_cost" in test_part.metadata.columns:
            leakage_costs = (
                test_part.metadata.get_column("estimated_leakage_cost")
                .fill_null(0.0)
                .to_numpy()
                .astype(np.float64)
            )
        else:
            leakage_costs = np.zeros(test_part.num_samples, dtype=np.float64)

        # Step 5: Calculate statistical metrics
        logger.info("Computing statistical classification metrics...")
        stat_metrics = ClassificationMetricsEvaluator.evaluate(
            y_true=y_test_np, y_pred=y_pred, y_prob=y_prob
        )

        # Step 6: Calculate Top-K ranking metrics
        logger.info("Computing operational Top-K ranking metrics...")
        top_k_metrics = RankingEvaluator.evaluate_top_k(
            y_true=y_test_np,
            y_prob=y_prob,
            k_values=self.settings.baseline.top_k_values,
        )

        # Step 7: Calculate financial outcome metrics
        logger.info("Computing financial cost and revenue recovery metrics...")
        fin_metrics = self.cost_evaluator.evaluate(
            y_true=y_test_np,
            y_pred=y_pred,
            leakage_costs=leakage_costs,
        )

        # Step 8: Extract feature importance (Gain & Split)
        df_imp_gain = model.get_feature_importance(importance_type="gain")
        df_imp_split = model.get_feature_importance(importance_type="split")
        df_imp_gain.write_csv(out_dir / "feature_importance_gain.csv")
        df_imp_split.write_csv(out_dir / "feature_importance_split.csv")

        # Step 9: Save baseline predictions artifact
        logger.info("Exporting baseline predictions artifact...")
        ranks = np.argsort(np.argsort(y_prob)[::-1]) + 1
        df_preds = pl.DataFrame(
            {
                "meter_id": test_part.metadata.get_column("meter_id"),
                "timestamp": test_part.metadata.get_column("timestamp"),
                "true_label": test_part.y,
                "predicted_probability": pl.Series(y_prob, dtype=pl.Float32),
                "predicted_class": pl.Series(y_pred, dtype=pl.Int8),
                "estimated_leakage_cost": pl.Series(leakage_costs, dtype=pl.Float32),
                "inspection_rank": pl.Series(ranks, dtype=pl.Int32),
            }
        )
        preds_parquet = out_dir / "baseline_predictions.parquet"
        df_preds.write_parquet(preds_parquet, compression="zstd")

        # Step 10: Generate diagnostic visualizations
        logger.info("Generating publication-grade diagnostic plots...")
        visualizer = BaselineVisualizer(output_dir=figures_dir)
        pr_chart = visualizer.plot_pr_curve(y_test_np, y_prob, pr_auc=stat_metrics["pr_auc"])
        roc_chart = visualizer.plot_roc_curve(y_test_np, y_prob, roc_auc=stat_metrics["roc_auc"])
        cm_chart = visualizer.plot_confusion_matrix(stat_metrics["confusion_matrix"])
        prob_chart = visualizer.plot_probability_distribution(y_test_np, y_prob)
        imp_chart = visualizer.plot_feature_importance(df_imp_gain, top_n=20)
        fin_chart = visualizer.plot_financial_loss_breakdown(fin_metrics)
        topk_chart = visualizer.plot_precision_at_k(top_k_metrics)

        # Step 11: Export JSON and Markdown Reports
        combined_results = {
            "model_type": self.settings.baseline.model_type,
            "threshold": self.settings.baseline.threshold,
            "split_dates": {
                "train": [self.settings.baseline.train_start, self.settings.baseline.train_end],
                "val": [self.settings.baseline.val_start, self.settings.baseline.val_end],
                "test": [self.settings.baseline.test_start, self.settings.baseline.test_end],
            },
            "sample_counts": {
                "train_samples": train_part.num_samples,
                "train_meters": train_part.num_meters,
                "val_samples": val_part.num_samples,
                "val_meters": val_part.num_meters,
                "test_samples": test_part.num_samples,
                "test_meters": test_part.num_meters,
            },
            "statistical_metrics": stat_metrics,
            "top_k_ranking_metrics": top_k_metrics,
            "financial_metrics": fin_metrics,
            "execution_time_seconds": round(time.time() - start_time, 2),
        }

        # Save metrics JSON
        metrics_json_path = out_dir / "baseline_metrics.json"
        with open(metrics_json_path, "w", encoding="utf-8") as f:
            json.dump(combined_results, f, indent=2)

        # Save Financial Markdown Report
        fin_report_path = out_dir / "financial_cost_report.md"
        self.cost_evaluator.export_report_markdown(fin_metrics, fin_report_path)

        # Step 12: MLflow Experiment Tracking
        if enable_mlflow:
            logger.info("Logging baseline run to MLflow...")
            try:
                tracker = ExperimentTracker(
                    experiment_name=self.settings.tracking.experiment_name,
                    tracking_uri=self.settings.tracking.tracking_uri,
                )
                with tracker.start_run(run_name="unweighted_lightgbm_baseline"):
                    # Log parameters
                    tracker.log_params(
                        {
                            "model_type": self.settings.baseline.model_type,
                            "learning_rate": self.settings.baseline.learning_rate,
                            "n_estimators": self.settings.baseline.n_estimators,
                            "max_depth": self.settings.baseline.max_depth,
                            "num_leaves": self.settings.baseline.num_leaves,
                            "threshold": self.settings.baseline.threshold,
                            "dispatch_cost": self.settings.financial.dispatch_cost,
                            "default_tariff": self.settings.financial.default_tariff,
                            "undetected_cycles": self.settings.financial.undetected_cycles,
                            "train_samples": train_part.num_samples,
                            "test_samples": test_part.num_samples,
                            "num_features": len(model.feature_names),
                        }
                    )

                    # Log metrics
                    flat_metrics = {
                        "pr_auc": stat_metrics["pr_auc"],
                        "roc_auc": stat_metrics["roc_auc"],
                        "precision": stat_metrics["precision"],
                        "recall": stat_metrics["recall"],
                        "f1_score": stat_metrics["f1_score"],
                        "total_loss": fin_metrics["financial_breakdown"][
                            "total_baseline_operational_loss"
                        ],
                        "fp_cost": fin_metrics["financial_breakdown"]["total_fp_dispatch_cost"],
                        "fn_cost": fin_metrics["financial_breakdown"]["total_fn_leakage_cost"],
                        "precision_at_100": top_k_metrics.get("100", {}).get("precision_at_k", 0.0),
                        "precision_at_500": top_k_metrics.get("500", {}).get("precision_at_k", 0.0),
                        "precision_at_1000": top_k_metrics.get("1000", {}).get(
                            "precision_at_k", 0.0
                        ),
                    }
                    tracker.log_metrics(flat_metrics)

                    tracker.log_artifact(str(metrics_json_path))
                    tracker.log_artifact(str(fin_report_path))
                    tracker.log_artifact(str(pr_chart))
                    tracker.log_artifact(str(roc_chart))
                    tracker.log_artifact(str(cm_chart))
                    tracker.log_artifact(str(prob_chart))
                    tracker.log_artifact(str(imp_chart))
                    tracker.log_artifact(str(fin_chart))
                    tracker.log_artifact(str(topk_chart))
            except Exception as e:
                logger.warning(f"MLflow logging encountered warning: {e}")

        logger.info(
            f"Baseline pipeline completed in {combined_results['execution_time_seconds']:.2f}s! "
            f"Artifacts saved in '{out_dir}'."
        )
        return combined_results
