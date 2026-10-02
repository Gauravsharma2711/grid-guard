"""Integration test for end-to-end CostSensitiveExperimentPipeline execution and artifact generation."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import polars as pl
import pytest

from grid_guard.config.cost_sensitive import CostSensitiveSettings
from grid_guard.config.financial import BaselineModelSettings, FinancialAssumptions
from grid_guard.config.settings import Settings
from grid_guard.models.cost_sensitive_pipeline import CostSensitiveExperimentPipeline


@pytest.fixture
def synthetic_features_parquet(tmp_path: Path) -> Path:
    """Generate minimal synthetic feature Parquet dataset covering train, val, and test dates."""
    records = []
    base_date = date(2020, 1, 1)

    for m in range(8):
        meter_id = f"METER_{m:03d}"
        for d in range(120):
            cur_date = base_date + timedelta(days=d)
            is_theft = 1 if (m < 2 and d >= 25) else 0
            kwh = 10.0 + (m % 3) * 1.5 + (0.5 if d % 7 in (5, 6) else 0.0)
            if is_theft:
                kwh = kwh * 0.3

            records.append(
                {
                    "meter_id": meter_id,
                    "timestamp": cur_date,
                    "daily_consumption_kwh": float(kwh),
                    "rolling_mean_14d": float(kwh * 0.95),
                    "rolling_mean_60d": float(kwh * 1.5 if is_theft else kwh * 1.05),
                    "ratio_14d_60d": 0.6 if is_theft else 0.95,
                    "zero_count_30d": 5.0 if is_theft else 0.0,
                    "tamper_label": is_theft,
                }
            )

    df = pl.DataFrame(records)
    out_file = tmp_path / "test_features.parquet"
    df.write_parquet(out_file)
    return out_file


def test_cost_sensitive_pipeline_end_to_end(
    tmp_path: Path,
    synthetic_features_parquet: Path,
) -> None:
    """Verify that CostSensitiveExperimentPipeline runs cleanly and exports all required artifacts."""
    output_dir = tmp_path / "artifacts_cost_sensitive"

    settings = Settings(
        baseline=BaselineModelSettings(
            train_start="2020-01-01",
            train_end="2020-02-20",
            val_start="2020-02-21",
            val_end="2020-03-20",
            test_start="2020-03-21",
            test_end="2020-04-30",
            sampling_stride_days=1,
            n_estimators=5,
            num_leaves=7,
            min_child_samples=2,
            top_k_values=[5, 10],
        ),
        cost_sensitive=CostSensitiveSettings(
            dispatch_cost=100.0,
            default_tariff=0.15,
            selection_metric="total_operational_loss",
        ),
        financial=FinancialAssumptions(
            dispatch_cost=100.0,
            default_tariff=0.15,
        ),
    )

    pipeline = CostSensitiveExperimentPipeline(settings=settings)
    results = pipeline.run(
        feature_parquet_path=synthetic_features_parquet,
        output_dir=output_dir,
        enable_mlflow=False,
    )

    # 1. Verify return dictionary structure
    assert "weight_audit" in results
    assert "selection_criterion" in results
    assert "validation_experiments" in results
    assert "test_evaluation" in results
    assert "threshold_grid_diagnostic" in results

    # 2. Check exported disk artifacts
    assert (output_dir / "cost_sensitive_comparison.json").is_file()
    assert (output_dir / "cost_sensitive_comparison_report.md").is_file()
    assert (output_dir / "weight_audit_report.json").is_file()
    assert (output_dir / "champion_predictions.parquet").is_file()
    assert (output_dir / "champion_model.txt").is_file()

    # 3. Check figures directory
    fig_dir = output_dir / "figures"
    assert (fig_dir / "expected_cost_curve.png").is_file()
    assert (fig_dir / "financial_weight_distribution.png").is_file()
    assert (fig_dir / "pr_curves_three_phase.png").is_file()
    assert (fig_dir / "financial_loss_three_phase.png").is_file()
    assert (fig_dir / "feature_importance_shift.png").is_file()
    assert (fig_dir / "confusion_matrix_cost_sensitive.png").is_file()
