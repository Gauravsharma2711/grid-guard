"""Unit tests for CostSensitiveLightGBM model fitting, prediction, and calibration."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl
import pytest

from grid_guard.config.cost_sensitive import CostSensitiveSettings, ProbabilityCalibrationType
from grid_guard.config.financial import BaselineModelSettings
from grid_guard.models.cost_sensitive import CostSensitiveLightGBM


@pytest.fixture
def synthetic_cost_data() -> tuple[pl.DataFrame, pl.Series, np.ndarray, pl.DataFrame, pl.Series]:
    """Generate reproducible small dataset for testing CostSensitiveLightGBM."""
    rng = np.random.default_rng(42)
    n_train = 120
    n_val = 40

    X_train = pl.DataFrame(
        {
            "f1": rng.normal(5.0, 1.0, n_train).astype(np.float32),
            "f2": rng.normal(10.0, 2.0, n_train).astype(np.float32),
            "f3": rng.uniform(0.0, 1.0, n_train).astype(np.float32),
        }
    )
    y_train = pl.Series("label", [1] * 15 + [0] * (n_train - 15), dtype=pl.Int32)
    weights = np.ones(n_train, dtype=np.float32)
    weights[:15] = rng.uniform(2.0, 15.0, 15).astype(np.float32)

    X_val = pl.DataFrame(
        {
            "f1": rng.normal(5.0, 1.0, n_val).astype(np.float32),
            "f2": rng.normal(10.0, 2.0, n_val).astype(np.float32),
            "f3": rng.uniform(0.0, 1.0, n_val).astype(np.float32),
        }
    )
    y_val = pl.Series("label", [1] * 5 + [0] * (n_val - 5), dtype=pl.Int32)

    return X_train, y_train, weights, X_val, y_val


def test_cost_sensitive_model_fit_and_predict(
    synthetic_cost_data: tuple[pl.DataFrame, pl.Series, np.ndarray, pl.DataFrame, pl.Series],
) -> None:
    """Verify that CostSensitiveLightGBM fits and predicts probabilities in [0, 1]."""
    X_train, y_train, weights, X_val, y_val = synthetic_cost_data

    base_cfg = BaselineModelSettings(n_estimators=10, min_child_samples=2)
    cost_cfg = CostSensitiveSettings(calibration_method=ProbabilityCalibrationType.NONE)

    model = CostSensitiveLightGBM(base_config=base_cfg, cost_config=cost_cfg)
    model.fit(X_train, y_train, weights=weights, eval_set=[(X_val, y_val)])

    margins = model.predict_margins(X_val)
    raw_probs = model.predict_raw_proba(X_val)
    probs = model.predict_proba(X_val)
    preds = model.predict(X_val, threshold=0.5)

    assert len(margins) == len(X_val)
    assert len(raw_probs) == len(X_val)
    assert len(preds) == len(X_val)
    assert np.all(probs >= 0.0)
    assert np.all(probs <= 1.0)
    assert set(np.unique(preds)).issubset({0, 1})


def test_calibration_fitting(
    synthetic_cost_data: tuple[pl.DataFrame, pl.Series, np.ndarray, pl.DataFrame, pl.Series],
) -> None:
    """Verify that post-hoc Isotonic and Platt calibrations fit and produce valid probabilities."""
    X_train, y_train, weights, X_val, y_val = synthetic_cost_data

    base_cfg = BaselineModelSettings(n_estimators=10, min_child_samples=2)
    model = CostSensitiveLightGBM(base_config=base_cfg)
    model.fit(X_train, y_train, weights=weights)

    # Test Isotonic
    model.fit_calibration(X_val, y_val, method=ProbabilityCalibrationType.ISOTONIC)
    p_iso = model.predict_proba(X_val)
    assert np.all(p_iso >= 0.0)
    assert np.all(p_iso <= 1.0)

    # Test Platt
    model.fit_calibration(X_val, y_val, method=ProbabilityCalibrationType.PLATT)
    p_platt = model.predict_proba(X_val)
    assert np.all(p_platt >= 0.0)
    assert np.all(p_platt <= 1.0)


def test_model_save_and_load(
    tmp_path: Path,
    synthetic_cost_data: tuple[pl.DataFrame, pl.Series, np.ndarray, pl.DataFrame, pl.Series],
) -> None:
    """Verify model save and load roundtrip."""
    X_train, y_train, weights, _, _ = synthetic_cost_data

    base_cfg = BaselineModelSettings(n_estimators=10, min_child_samples=2)
    model = CostSensitiveLightGBM(base_config=base_cfg)
    model.fit(X_train, y_train, weights=weights)

    save_path = tmp_path / "model.txt"
    model.save(save_path)
    assert save_path.is_file()

    loaded_model = CostSensitiveLightGBM(base_config=base_cfg)
    loaded_model.load(save_path, feature_names=X_train.columns)

    p1 = model.predict_raw_proba(X_train)
    p2 = loaded_model.predict_raw_proba(X_train)
    assert np.allclose(p1, p2, atol=1e-5)
