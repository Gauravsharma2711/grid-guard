"""Unit tests for financial weight generation, normalization, and outlier capping."""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from grid_guard.config.cost_sensitive import CostNormalizationType
from grid_guard.evaluation.cost_analysis import FinancialWeightBuilder


def test_positive_and_negative_weight_assignment() -> None:
    """Verify that honest consumers receive C_FP and theft consumers receive C_FN."""
    y = pl.Series("label", [0, 0, 1, 1], dtype=pl.Int32)
    c_fn = pl.Series("leakage", [0.0, 0.0, 500.0, 2500.0], dtype=pl.Float64)
    dispatch_cost = 100.0

    w_norm, w_raw, audit = FinancialWeightBuilder.construct_training_weights(
        y_train=y,
        estimated_leakage_costs=c_fn,
        dispatch_cost=dispatch_cost,
        normalization=CostNormalizationType.NONE,
    )

    # Honest consumers must receive exact dispatch cost
    assert w_raw[0] == 100.0
    assert w_raw[1] == 100.0

    # Theft consumers must receive per-consumer leakage cost
    assert w_raw[2] == 500.0
    assert w_raw[3] == 2500.0

    # Relative ordering check: higher leakage = strictly higher training weight
    assert w_raw[3] > w_raw[2] > w_raw[0]


def test_dispatch_cost_normalization() -> None:
    """Verify dispatch_cost normalization scales negative weight to exactly 1.0."""
    y = np.array([0, 0, 1, 1], dtype=np.int32)
    c_fn = np.array([0.0, 0.0, 400.0, 1200.0], dtype=np.float64)
    dispatch_cost = 100.0

    w_norm, w_raw, audit = FinancialWeightBuilder.construct_training_weights(
        y_train=y,
        estimated_leakage_costs=c_fn,
        dispatch_cost=dispatch_cost,
        normalization=CostNormalizationType.DISPATCH_COST,
    )

    # Negative weights must be exactly 1.0 (dispatch_cost / dispatch_cost)
    assert np.isclose(w_norm[0], 1.0)
    assert np.isclose(w_norm[1], 1.0)

    # Positive weights must equal exact economic ratio C_FN / C_FP
    assert np.isclose(w_norm[2], 4.0)  # $400 / $100
    assert np.isclose(w_norm[3], 12.0)  # $1,200 / $100


def test_outlier_capping() -> None:
    """Verify that cost capping clips extreme values above configured percentile."""
    y = np.ones(100, dtype=np.int32)
    # 99 values around $500, 1 extreme outlier at $100,000
    c_fn = np.full(100, fill_value=500.0, dtype=np.float64)
    c_fn[-1] = 100000.0

    _, w_raw_uncapped, _ = FinancialWeightBuilder.construct_training_weights(
        y_train=y,
        estimated_leakage_costs=c_fn,
        dispatch_cost=100.0,
        cost_capping=False,
    )
    assert w_raw_uncapped[-1] == 100000.0

    _, w_raw_capped, audit_capped = FinancialWeightBuilder.construct_training_weights(
        y_train=y,
        estimated_leakage_costs=c_fn,
        dispatch_cost=100.0,
        cost_capping=True,
        cost_cap_percentile=95.0,
    )
    assert w_raw_capped[-1] < 100000.0
    assert audit_capped.samples_capped >= 1
    assert audit_capped.cost_cap_value is not None


def test_empty_positives_raises_error() -> None:
    """Verify ValueError is raised if training set contains zero positives."""
    y = np.zeros(20, dtype=np.int32)
    c_fn = np.zeros(20, dtype=np.float64)

    with pytest.raises(ValueError, match="zero positive"):
        FinancialWeightBuilder.construct_training_weights(
            y_train=y, estimated_leakage_costs=c_fn, dispatch_cost=100.0
        )
