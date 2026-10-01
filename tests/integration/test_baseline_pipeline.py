"""Integration test for end-to-end BaselinePipeline execution and artifact generation."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import polars as pl
import pytest

from grid_guard.config.financial import BaselineModelSettings, FinancialAssumptions
from grid_guard.config.settings import Settings
from grid_guard.models.pipeline import BaselinePipeline


@pytest.fixture
def synthetic_canonical_parquet(tmp_path: Path) -> Path:
    """Create a minimal canonical features parquet file spanning 2014 to 2016."""
    num_meters = 15
    start_date = date(2014, 6, 1)
    num_days = 800  # reaches late 2016

    records = []
    for m in range(num_meters):
        meter_id = f"1337{m:04d}"
        for d in range(num_days):
            cur_date = start_date + timedelta(days=d)
            # Create features
            kwh = 10.0 + (m % 4) * 2.0 + (0.5 if d % 7 in (5, 6) else 0.0)
            records.append(
                {
                    "meter_id": meter_id,
                    "timestamp": cur_date,
                    "daily_consumption_kwh": float(kwh),
                    "baseline_consumption_60d": float(kwh * 1.05),
                    "consumption_ratio_14d_over_60d": 0.95,
                    "zero_consumption_ratio_30d": 0.0,
                    "mean_daily_drop_severity_30d": 0.1,
                    "tamper_label": 1 if m % 5 == 0 else 0,
                }
            )

    df = pl.DataFrame(records)
    parquet_path = tmp_path / "canonical_features_mock.parquet"
    df.write_parquet(parquet_path)
    return parquet_path


def test_baseline_pipeline_end_to_end(synthetic_canonical_parquet: Path, tmp_path: Path) -> None:
    """Verify BaselinePipeline runs end-to-end, evaluates properly, and generates all required artifacts."""
    out_dir = tmp_path / "artifacts" / "baseline"

    # Custom settings with matching dates
    custom_baseline = BaselineModelSettings(
        train_start="2014-06-01",
        train_end="2015-06-30",
        val_start="2015-07-01",
        val_end="2015-12-31",
        test_start="2016-01-01",
        test_end="2016-06-30",
        n_estimators=10,
        max_depth=3,
        num_leaves=7,
        sampling_stride_days=15,
        threshold=0.5,
        top_k_values=[5, 10],
    )
    custom_financial = FinancialAssumptions(
        dispatch_cost=75.0,
        default_tariff=0.18,
        undetected_cycles=6,
        currency="USD",
    )

    settings = Settings(
        baseline=custom_baseline,
        financial=custom_financial,
    )

    pipeline = BaselinePipeline(settings=settings)
    results = pipeline.run(
        feature_parquet_path=synthetic_canonical_parquet,
        output_dir=out_dir,
        enable_mlflow=False,
    )

    # 1. Verify returned result structure
    assert "statistical_metrics" in results
    assert "top_k_ranking_metrics" in results
    assert "financial_metrics" in results
    assert "sample_counts" in results
    assert results["sample_counts"]["train_samples"] > 0
    assert results["sample_counts"]["test_samples"] > 0

    # 2. Verify statistical metrics
    stat_metrics = results["statistical_metrics"]
    assert "pr_auc" in stat_metrics
    assert "roc_auc" in stat_metrics
    assert "confusion_matrix" in stat_metrics
    assert 0.0 <= stat_metrics["pr_auc"] <= 1.0

    # 3. Verify financial metrics
    fin_metrics = results["financial_metrics"]
    assert "financial_breakdown" in fin_metrics
    breakdown = fin_metrics["financial_breakdown"]
    assert "total_baseline_operational_loss" in breakdown
    assert breakdown["total_baseline_operational_loss"] >= 0.0

    # 4. Verify artifact files exist
    assert (out_dir / "baseline_lightgbm.txt").exists()
    assert (out_dir / "baseline_predictions.parquet").exists()
    assert (out_dir / "baseline_metrics.json").exists()
    assert (out_dir / "financial_cost_report.md").exists()
    assert (out_dir / "feature_importance_gain.csv").exists()
    assert (out_dir / "feature_importance_split.csv").exists()

    # 5. Verify figures exist
    figures_dir = out_dir / "figures"
    assert (figures_dir / "pr_curve.png").exists()
    assert (figures_dir / "roc_curve.png").exists()
    assert (figures_dir / "confusion_matrix.png").exists()
    assert (figures_dir / "probability_distribution.png").exists()
    assert (figures_dir / "feature_importance.png").exists()
    assert (figures_dir / "financial_loss_breakdown.png").exists()
    assert (figures_dir / "precision_at_k.png").exists()

    # 6. Verify predictions artifact schema and content
    preds_df = pl.read_parquet(out_dir / "baseline_predictions.parquet")
    expected_cols = {
        "meter_id",
        "timestamp",
        "true_label",
        "predicted_probability",
        "predicted_class",
        "estimated_leakage_cost",
        "inspection_rank",
    }
    assert expected_cols.issubset(set(preds_df.columns))
    assert len(preds_df) == results["sample_counts"]["test_samples"]
