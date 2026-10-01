"""Automated temporal and target leakage audit tests for Grid-Guard features."""

from __future__ import annotations

from datetime import date, timedelta

import polars as pl
import pytest

from grid_guard.features.pipeline import FeaturePipeline
from grid_guard.features.registry import FeatureRegistry
from tests.fixtures.synthetic_ami import generate_synthetic_series


def test_strict_temporal_leakage_audit() -> None:
    """Verify that future observations (> t) strictly cannot alter features at (<= t).

    Methodology:
    1. Take a 90-day time series.
    2. Pick cutoff day T = 50.
    3. Calculate features on original series F1.
    4. Create series 2 with identical values for t <= 50, but radical anomalies for t > 50.
    5. Calculate features on series 2: F2.
    6. Verify that for all rows t <= 50, all engineered feature values in F1 and F2 are identical.
    """
    pipeline = FeaturePipeline()

    # Original series
    df_orig = generate_synthetic_series(num_days=90, pattern="normal")
    f_orig = pipeline.transform(df_orig)

    # Cutoff date: day 50
    cutoff_date = date(2020, 1, 1) + timedelta(days=50)

    # Modified series: strictly identical <= day 50, wildly corrupted > day 50
    df_corrupted = df_orig.with_columns(
        consumption_kwh=pl.when(pl.col("timestamp") <= cutoff_date)
        .then(pl.col("consumption_kwh"))
        .otherwise(pl.col("consumption_kwh") * 500.0 + 9999.0)
    )
    f_corrupted = pipeline.transform(df_corrupted)

    # Filter to historical evaluation window (<= cutoff_date)
    hist_orig = f_orig.filter(pl.col("timestamp") <= cutoff_date)
    hist_corrupted = f_corrupted.filter(pl.col("timestamp") <= cutoff_date)

    # Columns to check: all engineered features
    exclude_cols = {"meter_id", "timestamp", "tamper_label", "data_quality_status", "feeder_id"}
    feature_cols = [c for c in f_orig.columns if c not in exclude_cols]

    for col in feature_cols:
        v1 = hist_orig.get_column(col).to_list()
        v2 = hist_corrupted.get_column(col).to_list()

        assert len(v1) == len(v2), f"Row count mismatch for column '{col}'"

        for idx, (val1, val2) in enumerate(zip(v1, v2, strict=True)):
            if val1 is None:
                assert val2 is None, (
                    f"Temporal leakage in '{col}' at index {idx} on "
                    f"{hist_orig['timestamp'][idx]}: original was None, corrupted is {val2}"
                )
            else:
                assert val2 is not None, (
                    f"Temporal leakage in '{col}' at index {idx} on "
                    f"{hist_orig['timestamp'][idx]}: original={val1}, corrupted is None"
                )
                assert pytest.approx(val1, rel=1e-5, abs=1e-5) == val2, (
                    f"Temporal leakage detected in feature '{col}' on date "
                    f"{hist_orig['timestamp'][idx]}! Original={val1}, Corrupted future gave={val2}"
                )


def test_target_leakage_audit() -> None:
    """Verify that ground truth tamper_label is never used as an input feature."""
    reg = FeatureRegistry()
    pipeline = FeaturePipeline(registry=reg)

    # Check registered source columns
    for feat in reg.list_features():
        assert "tamper_label" not in feat.source_columns, (
            f"Target leakage: Feature '{feat.name}' references target 'tamper_label'!"
        )
        assert feat.name != "tamper_label"

    # Transform a dataset and ensure target column is unchanged
    df = generate_synthetic_series(num_days=30, tamper_label=1)
    res = pipeline.transform(df)

    assert "tamper_label" in res.columns
    # Ensure label column was not modified
    assert res.get_column("tamper_label").to_list() == [1] * 30
