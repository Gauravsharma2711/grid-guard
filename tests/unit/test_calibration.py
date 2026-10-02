"""Unit tests for probability calibration evaluation and Brier score metrics."""

from __future__ import annotations

import numpy as np

from grid_guard.evaluation.calibration import CalibrationEvaluator


def test_calibration_evaluator_perfect() -> None:
    """Verify Brier score and ECE on perfectly calibrated predictions."""
    y_true = np.array([0, 0, 1, 1], dtype=np.int32)
    y_prob = np.array([0.0, 0.0, 1.0, 1.0], dtype=np.float32)

    res = CalibrationEvaluator.evaluate(y_true, y_prob, n_bins=5)
    assert res["brier_score"] == 0.0
    assert 0.0 <= res["expected_calibration_error"] <= 0.05
    assert len(res["binned_calibration"]) > 0


def test_calibration_evaluator_imbalanced() -> None:
    """Verify calibration evaluator metrics on synthetic imbalanced predictions."""
    rng = np.random.default_rng(42)
    y_true = rng.choice([0, 1], size=200, p=[0.90, 0.10])
    y_prob = rng.uniform(0.0, 0.3, size=200).astype(np.float32)

    res = CalibrationEvaluator.evaluate(y_true, y_prob, n_bins=10)
    assert 0.0 <= res["brier_score"] <= 1.0
    assert 0.0 <= res["expected_calibration_error"] <= 1.0
    assert "prob_true" in res
    assert "prob_pred" in res
