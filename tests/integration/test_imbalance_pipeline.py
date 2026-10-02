"""Integration test for end-to-end ImbalanceExperimentPipeline execution and artifact generation."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import polars as pl
import pytest

from grid_guard.config.financial import BaselineModelSettings, FinancialAssumptions
from grid_guard.config.imbalance import ImbalanceSettings
from grid_guard.config.settings import Settings
from grid_guard.models.imbalance_pipeline import ImbalanceExperimentPipeline


@pytest.fixture
def synthetic_imbalance_parquet(tmp_path: Path) -> Path:
    """Create a minimal synthetic canonical features parquet file spanning 2014 to 2016."""
    num_meters = 20
    start_date = date(2014, 6, 1)
    num_days = 800

    records = []
    for m in range(num_meters):
        meter_id = f"1337{m:04d}"
        is_theft = 1 if m in (0, 1) else 0  # 10% positive meters
        for d in range(num_days):
            cur_date = start_date + timedelta(days=d)
            kwh = 10.0 + (m % 3) * 1.5 + (0.5 if d % 7 in (5, 6) else 0.0)
            records.append(
                {
                    "meter_id": meter_id,
                    "timestamp": cur_date,
                    "daily_consumption_kwh": float(kwh),
                    "rolling_mean_14d": float(kwh * 0.95),
                    "rolling_mean_60d": float(kwh * 1.05),
                    "ratio_14d_60d": 0.95,
                    "zero_count_30d": 0.0,
                    "tamper_label": is_theft,
                }
            )

    df = pl.DataFrame(records)
    parquet_path = tmp_path / "canonical_features_mock.parquet"
    df.write_parquet(parquet_path)
    return parquet_path


def test_imbalance_pipeline_end_to_end(synthetic_imbalance_parquet: Path, tmp_path: Path) -> None:
    """Verify ImbalanceExperimentPipeline runs end-to-end, selects champion, and exports artifacts."""
    out_dir = tmp_path / "artifacts" / "imbalance"

    custom_baseline = BaselineModelSettings(
        train_start="2014-06-01",
        train_end="2015-06-30",
        val_start="2015-07-01",
        val_end="2015-12-31",
        test_start="2016-01-01",
        test_end="2016-06-30",
        n_estimators=5,
        max_depth=2,
        num_leaves=3,
        sampling_stride_days=15,
        threshold=0.5,
        top_k_values=[5, 10],
    )
    custom_financial = FinancialAssumptions(
        dispatch_cost=80.0,
        default_tariff=0.15,
        undetected_cycles=6,
        currency="USD",
    )
    custom_imbalance = ImbalanceSettings(
        selection_metric="pr_auc",
        smote_sample_size_cap=1000,
        random_seed=42,
    )

    settings = Settings(
        baseline=custom_baseline,
        financial=custom_financial,
        imbalance=custom_imbalance,
    )

    pipeline = ImbalanceExperimentPipeline(settings=settings)
    results = pipeline.run(
        feature_parquet_path=synthetic_imbalance_parquet,
        output_dir=out_dir,
        enable_mlflow=False,
    )

    # 1. Structure assertions
    assert "selection_criterion" in results
    assert "validation_experiments" in results
    assert "test_evaluation" in results
    assert len(results["validation_experiments"]) >= 5

    # 2. Check Champion vs Baseline test evaluation
    test_eval = results["test_evaluation"]
    assert "baseline" in test_eval
    assert "champion" in test_eval
    assert "delta" in test_eval

    # 3. Check artifacts exist
    assert (out_dir / "champion_model.txt").exists()
    assert (out_dir / "champion_predictions.parquet").exists()
    assert (out_dir / "imbalance_comparison.json").exists()
    assert (out_dir / "imbalance_comparison_report.md").exists()
    assert (out_dir / "champion_feature_importance_gain.csv").exists()
    assert (out_dir / "champion_feature_importance_split.csv").exists()

    # 4. Check figures exist
    figures_dir = out_dir / "figures"
    assert (figures_dir / "pr_curves_comparison.png").exists()
    assert (figures_dir / "roc_curves_comparison.png").exists()
    assert (figures_dir / "calibration_curves.png").exists()
    assert (figures_dir / "probability_distributions_comparison.png").exists()
    assert (figures_dir / "precision_at_k_comparison.png").exists()
    assert (figures_dir / "confusion_matrix_champion.png").exists()
    assert (figures_dir / "financial_loss_comparison.png").exists()

    # 5. Check prediction artifact schema
    df_preds = pl.read_parquet(out_dir / "champion_predictions.parquet")
    expected_cols = {
        "meter_id",
        "timestamp",
        "true_label",
        "predicted_probability",
        "predicted_class",
        "inspection_rank",
    }
    assert expected_cols.issubset(set(df_preds.columns))
    assert len(df_preds) > 0
