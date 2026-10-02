"""Strict leakage audit tests for Phase 6 cost-sensitive learning and financial weight construction."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import polars as pl

from grid_guard.config.cost_sensitive import CostNormalizationType
from grid_guard.config.financial import BaselineModelSettings
from grid_guard.evaluation.cost_analysis import FinancialWeightBuilder
from grid_guard.models.splitting import TemporalDataSplitter


def _create_mock_enriched_time_series() -> pl.DataFrame:
    """Generate multi-meter time series with estimated_leakage_cost column."""
    records = []
    base_date = date(2020, 1, 1)

    for m in range(10):
        m_id = f"METER_{m:03d}"
        for d in range(120):
            cur_date = base_date + timedelta(days=d)
            is_theft = 1 if (m < 2 and d >= 30) else 0
            leakage = 1500.0 if is_theft else 0.0
            records.append(
                {
                    "meter_id": m_id,
                    "timestamp": cur_date,
                    "feat_1": float(10.0 + (m % 3)),
                    "feat_2": float(5.0 + (d % 7)),
                    "estimated_leakage_cost": float(leakage),
                    "tamper_label": is_theft,
                }
            )
    return pl.DataFrame(records)


def test_training_weights_invariant_to_future_test_data() -> None:
    """Verify that training weights and normalization scale are 100% invariant to future test data."""
    df = _create_mock_enriched_time_series()
    config = BaselineModelSettings(
        train_start="2020-01-01",
        train_end="2020-02-29",
        val_start="2020-03-01",
        val_end="2020-03-31",
        test_start="2020-04-01",
        test_end="2020-04-30",
        sampling_stride_days=1,
    )
    splitter = TemporalDataSplitter(config=config)
    train_part, val_part, test_part = splitter.split(df, target_col="tamper_label")

    # Baseline weight generation on training partition
    train_leakage = train_part.metadata.get_column("estimated_leakage_cost").to_numpy()
    w_orig, _, audit_orig = FinancialWeightBuilder.construct_training_weights(
        y_train=train_part.y,
        estimated_leakage_costs=train_leakage,
        dispatch_cost=100.0,
        normalization=CostNormalizationType.DISPATCH_COST,
    )

    # Mutate all future test data: invert labels and multiply test leakage by 1,000x
    _mutated_test_y = 1 - test_part.y.to_numpy()
    _mutated_test_leakage = (
        test_part.metadata.get_column("estimated_leakage_cost").to_numpy() * 1000.0
    )

    # Ensure mutation did not leak into training weight builder
    w_after, _, audit_after = FinancialWeightBuilder.construct_training_weights(
        y_train=train_part.y,
        estimated_leakage_costs=train_leakage,
        dispatch_cost=100.0,
        normalization=CostNormalizationType.DISPATCH_COST,
    )

    assert np.allclose(w_orig, w_after)
    assert audit_orig.reference_scale == audit_after.reference_scale
    assert audit_orig.c_fn_median == audit_after.c_fn_median


def test_target_and_leakage_excluded_from_features() -> None:
    """Verify that tamper_label and estimated_leakage_cost never enter feature matrix X."""
    df = _create_mock_enriched_time_series()
    config = BaselineModelSettings(
        train_start="2020-01-01",
        train_end="2020-02-29",
        val_start="2020-03-01",
        val_end="2020-03-31",
        test_start="2020-04-01",
        test_end="2020-04-30",
        sampling_stride_days=1,
    )
    splitter = TemporalDataSplitter(config=config)
    train_part, val_part, test_part = splitter.split(df, target_col="tamper_label")

    for part_name, part in [("train", train_part), ("val", val_part), ("test", test_part)]:
        cols = part.X.columns
        assert "tamper_label" not in cols, f"Target leaked into {part_name}.X!"
        assert "FLAG" not in cols, f"Target leaked into {part_name}.X!"
        assert "estimated_leakage_cost" not in cols, f"Leakage cost leaked into {part_name}.X!"
        assert "meter_id" not in cols, f"Meter ID leaked into {part_name}.X!"
        assert "timestamp" not in cols, f"Timestamp leaked into {part_name}.X!"
