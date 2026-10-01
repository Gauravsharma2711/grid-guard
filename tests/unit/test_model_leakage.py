"""Strict unit tests auditing temporal and label leakage in baseline modeling."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import polars as pl
import pytest

from grid_guard.config.financial import BaselineModelSettings
from grid_guard.models.baseline import BaselineLightGBM
from grid_guard.models.splitting import TemporalDataSplitter


@pytest.fixture
def synthetic_temporal_df() -> pl.DataFrame:
    """Generate multi-meter time-series with distinct historical features."""
    num_meters = 10
    days = 150
    start_date = date(2020, 1, 1)

    meter_ids = []
    timestamps = []
    feat_baseline = []
    feat_ratio = []
    labels = []

    for m in range(num_meters):
        m_id = f"MTR_{m:03d}"
        for d in range(days):
            cur_date = start_date + timedelta(days=d)
            meter_ids.append(m_id)
            timestamps.append(cur_date)
            # Feature purely derived from past
            feat_baseline.append(float(10.0 + (m % 3) * 2.0))
            # Some drift or pattern
            feat_ratio.append(float(0.8 + 0.1 * np.sin(d)))
            # Label
            labels.append(1 if m % 5 == 0 and d > 30 else 0)

    return pl.DataFrame(
        {
            "meter_id": meter_ids,
            "timestamp": timestamps,
            "baseline_consumption_60d": feat_baseline,
            "consumption_ratio_30d_over_60d": feat_ratio,
            "tamper_label": labels,
        }
    )


def test_target_and_metadata_strictly_excluded_from_x(synthetic_temporal_df: pl.DataFrame) -> None:
    """Verify target and identifier columns are NEVER present in feature matrix X."""
    config = BaselineModelSettings(
        train_start="2020-01-01",
        train_end="2020-02-29",
        val_start="2020-03-01",
        val_end="2020-03-31",
        test_start="2020-04-01",
        test_end="2020-05-29",
        sampling_stride_days=1,
    )
    splitter = TemporalDataSplitter(config=config)
    train_part, val_part, test_part = splitter.split(
        synthetic_temporal_df, target_col="tamper_label", sampling_stride_days=1
    )

    forbidden_cols = {"tamper_label", "meter_id", "timestamp", "FLAG"}
    for part_name, part in [("train", train_part), ("val", val_part), ("test", test_part)]:
        for forbidden in forbidden_cols:
            assert forbidden not in part.X.columns, f"{forbidden} leaked into {part_name} X matrix!"

    # Target series matches y
    assert set(train_part.y.unique().to_list()).issubset({0, 1})
    assert set(test_part.y.unique().to_list()).issubset({0, 1})


def test_strict_temporal_non_overlap(synthetic_temporal_df: pl.DataFrame) -> None:
    """Verify that temporal partitions strictly do not overlap."""
    config = BaselineModelSettings(
        train_start="2020-01-01",
        train_end="2020-02-29",
        val_start="2020-03-01",
        val_end="2020-03-31",
        test_start="2020-04-01",
        test_end="2020-05-29",
        sampling_stride_days=1,
    )
    splitter = TemporalDataSplitter(config=config)
    train_part, val_part, test_part = splitter.split(
        synthetic_temporal_df, target_col="tamper_label", sampling_stride_days=1
    )

    # Train max timestamp < val min timestamp
    assert train_part.end_date < val_part.start_date
    # Val max timestamp < test min timestamp
    assert val_part.end_date < test_part.start_date


def test_future_test_labels_do_not_affect_trained_model(
    synthetic_temporal_df: pl.DataFrame,
) -> None:
    """Verify that modifying future test data or test labels has zero effect on trained model."""
    config = BaselineModelSettings(
        train_start="2020-01-01",
        train_end="2020-02-29",
        val_start="2020-03-01",
        val_end="2020-03-31",
        test_start="2020-04-01",
        test_end="2020-05-29",
        sampling_stride_days=1,
        random_seed=42,
    )
    splitter = TemporalDataSplitter(config=config)

    # Split original
    train_part_1, val_part_1, _ = splitter.split(
        synthetic_temporal_df, target_col="tamper_label", sampling_stride_days=1
    )

    # Create mutated copy where test period labels and features are completely inverted/scrambled
    mutated_df = synthetic_temporal_df.with_columns(
        [
            pl.when(pl.col("timestamp") >= date(2020, 4, 1))
            .then(1 - pl.col("tamper_label"))
            .otherwise(pl.col("tamper_label"))
            .alias("tamper_label"),
            pl.when(pl.col("timestamp") >= date(2020, 4, 1))
            .then(pl.col("baseline_consumption_60d") * 999.0)
            .otherwise(pl.col("baseline_consumption_60d"))
            .alias("baseline_consumption_60d"),
        ]
    )

    train_part_2, val_part_2, _ = splitter.split(
        mutated_df, target_col="tamper_label", sampling_stride_days=1
    )

    # Train two models
    model_1 = BaselineLightGBM(config=config)
    model_1.fit(train_part_1.X, train_part_1.y)

    model_2 = BaselineLightGBM(config=config)
    model_2.fit(train_part_2.X, train_part_2.y)

    # Feature importance and predictions on validation set must be strictly identical
    preds_1 = model_1.predict_proba(val_part_1.X)
    preds_2 = model_2.predict_proba(val_part_2.X)

    np.testing.assert_allclose(preds_1, preds_2, err_msg="Future data leaked into trained model!")
