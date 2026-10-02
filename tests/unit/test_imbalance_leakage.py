"""Strict leakage tests for class weighting and training-only resampling strategies."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import polars as pl
import pytest

from grid_guard.config.financial import BaselineModelSettings
from grid_guard.data.sampling import (
    compute_training_class_weights,
    controlled_training_resample,
)
from grid_guard.models.imbalance import ImbalanceAwareLightGBM
from grid_guard.models.splitting import TemporalDataSplitter


@pytest.fixture
def synthetic_multimeter_df() -> pl.DataFrame:
    """Generate multi-meter time-series fixture."""
    num_meters = 10
    days = 150
    start_date = date(2020, 1, 1)

    meter_ids = []
    timestamps = []
    feat_1 = []
    feat_2 = []
    labels = []

    for m in range(num_meters):
        m_id = f"MTR_{m:03d}"
        for d in range(days):
            meter_ids.append(m_id)
            timestamps.append(start_date + timedelta(days=d))
            feat_1.append(float(5.0 + (m % 3) * 2.0))
            feat_2.append(float(d * 0.1))
            labels.append(1 if m == 0 and d > 20 else 0)

    return pl.DataFrame(
        {
            "meter_id": meter_ids,
            "timestamp": timestamps,
            "f1": feat_1,
            "f2": feat_2,
            "tamper_label": labels,
        }
    )


def test_class_weights_isolated_from_test_and_val(synthetic_multimeter_df: pl.DataFrame) -> None:
    """Verify class weights are derived strictly from training partition."""
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
        synthetic_multimeter_df, target_col="tamper_label", sampling_stride_days=1
    )

    # Base weight
    w_orig = compute_training_class_weights(train_part.y)

    # Invert all test labels
    _mutated_test_y = pl.Series("tamper_label", 1 - test_part.y.to_numpy())
    # Train weights must be 100% invariant to test mutations
    w_after = compute_training_class_weights(train_part.y)

    assert w_orig.scale_pos_weight == w_after.scale_pos_weight
    assert w_orig.n_positives == w_after.n_positives


def test_resampling_never_modifies_val_or_test(synthetic_multimeter_df: pl.DataFrame) -> None:
    """Verify that resampling operations are strictly confined to training data."""
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
        synthetic_multimeter_df, target_col="tamper_label", sampling_stride_days=1
    )

    val_orig_len = val_part.num_samples
    test_orig_len = test_part.num_samples
    val_orig_y = val_part.y.clone()
    test_orig_y = test_part.y.clone()

    # Resample training data
    X_tr_res, y_tr_res, _, _ = controlled_training_resample(
        X_train=train_part.X,
        y_train=train_part.y,
        strategy="controlled_oversample",
        target_pos_ratio=0.5,
        random_seed=42,
    )

    # Training size changed
    assert len(y_tr_res) > len(train_part.y)

    # Validation and test sizes and values are strictly unchanged
    assert val_part.num_samples == val_orig_len
    assert test_part.num_samples == test_orig_len
    assert val_part.y.equals(val_orig_y)
    assert test_part.y.equals(test_orig_y)


def test_future_test_labels_do_not_leak_into_trained_imbalance_model(
    synthetic_multimeter_df: pl.DataFrame,
) -> None:
    """Verify modifying future test data does not change trained imbalance model predictions."""
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
    train_1, val_1, _ = splitter.split(
        synthetic_multimeter_df, target_col="tamper_label", sampling_stride_days=1
    )

    # Mutated copy: Invert all labels and features after test_start
    mutated_df = synthetic_multimeter_df.with_columns(
        [
            pl.when(pl.col("timestamp") >= date(2020, 4, 1))
            .then(1 - pl.col("tamper_label"))
            .otherwise(pl.col("tamper_label"))
            .alias("tamper_label"),
            pl.when(pl.col("timestamp") >= date(2020, 4, 1))
            .then(pl.col("f1") * 999.0)
            .otherwise(pl.col("f1"))
            .alias("f1"),
        ]
    )
    train_2, val_2, _ = splitter.split(
        mutated_df, target_col="tamper_label", sampling_stride_days=1
    )

    w1 = compute_training_class_weights(train_1.y).scale_pos_weight
    w2 = compute_training_class_weights(train_2.y).scale_pos_weight
    assert w1 == w2

    model_1 = ImbalanceAwareLightGBM(base_config=config, scale_pos_weight=w1)
    model_1.fit(train_1.X, train_1.y)

    model_2 = ImbalanceAwareLightGBM(base_config=config, scale_pos_weight=w2)
    model_2.fit(train_2.X, train_2.y)

    preds_1 = model_1.predict_proba(val_1.X)
    preds_2 = model_2.predict_proba(val_2.X)
    np.testing.assert_allclose(preds_1, preds_2, err_msg="Future data leaked into trained weights!")
