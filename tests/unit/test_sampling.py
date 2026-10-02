"""Unit tests for class weighting and training-only resampling strategies."""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from grid_guard.data.sampling import (
    compute_training_class_weights,
    controlled_training_resample,
)


def test_compute_training_class_weights_valid() -> None:
    """Verify class weight computation on binary training labels."""
    # 100 samples: 10 positives, 90 negatives -> ratio 9.0
    y = pl.Series("label", [1] * 10 + [0] * 90, dtype=pl.Int32)
    res = compute_training_class_weights(y, multiplier=1.0)

    assert res.total_samples == 100
    assert res.n_positives == 10
    assert res.n_negatives == 90
    assert res.imbalance_ratio == 9.0
    assert res.scale_pos_weight == 9.0
    assert res.class_weights[1] == 9.0

    # With multiplier 2.0
    res_2x = compute_training_class_weights(y, multiplier=2.0)
    assert res_2x.scale_pos_weight == 18.0


def test_compute_training_class_weights_errors() -> None:
    """Verify error handling on invalid class labels."""
    # Empty
    with pytest.raises(ValueError, match="y_train is empty"):
        compute_training_class_weights(pl.Series("label", [], dtype=pl.Int32))

    # No positives
    with pytest.raises(ValueError, match="0 positive instances"):
        compute_training_class_weights(pl.Series("label", [0, 0, 0], dtype=pl.Int32))


def test_controlled_oversample() -> None:
    """Verify controlled minority oversampling in training set."""
    X = pl.DataFrame(
        {
            "f1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "f2": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        }
    )
    y = pl.Series("y", [1, 1, 0, 0, 0, 0, 0, 0, 0, 0], dtype=pl.Int32)  # 2 pos, 8 neg

    X_res, y_res, _, audit = controlled_training_resample(
        X_train=X,
        y_train=y,
        strategy="controlled_oversample",
        target_pos_ratio=0.50,  # 8 neg * 0.50 = 4 pos
        random_seed=42,
    )

    y_arr = y_res.to_numpy()
    assert (y_arr == 0).sum() == 8  # Negative count unchanged
    assert (y_arr == 1).sum() == 4  # Positive count increased from 2 to 4
    assert len(X_res) == 12
    assert audit["resampled_counts"]["total"] == 12


def test_controlled_undersample() -> None:
    """Verify controlled majority undersampling in training set."""
    X = pl.DataFrame(
        {
            "f1": [float(i) for i in range(20)],
        }
    )
    y = pl.Series("y", [1] * 2 + [0] * 18, dtype=pl.Int32)  # 2 pos, 18 neg

    X_res, y_res, _, audit = controlled_training_resample(
        X_train=X,
        y_train=y,
        strategy="controlled_undersample",
        target_pos_ratio=0.50,  # 2 pos / 0.50 = 4 neg
        random_seed=42,
    )

    y_arr = y_res.to_numpy()
    assert (y_arr == 1).sum() == 2  # Positives unchanged
    assert (y_arr == 0).sum() == 4  # Negatives reduced from 18 to 4
    assert len(X_res) == 6


def test_smote_safety_checks_and_generation() -> None:
    """Verify SMOTE safety checks against non-numeric columns and synthetic generation."""
    # Test violation: Non-numeric timestamp in SMOTE features
    X_bad = pl.DataFrame(
        {
            "f1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
            "date_col": ["2020-01-01"] * 8,
        }
    )
    y = pl.Series("y", [1] * 3 + [0] * 5, dtype=pl.Int32)

    with pytest.raises(TypeError, match="SMOTE feature safety violation"):
        controlled_training_resample(
            X_train=X_bad,
            y_train=y,
            strategy="smote",
            target_pos_ratio=0.5,
            k_neighbors=2,
            random_seed=42,
        )

    # Valid numeric SMOTE
    rng = np.random.default_rng(42)
    X_good = pl.DataFrame(
        {
            "f1": rng.normal(10.0, 1.0, 20).astype(np.float32),
            "f2": rng.normal(5.0, 0.5, 20).astype(np.float32),
        }
    )
    y_good = pl.Series("y", [1] * 6 + [0] * 14, dtype=pl.Int32)  # 6 pos, 14 neg

    X_res, y_res, _, audit = controlled_training_resample(
        X_train=X_good,
        y_train=y_good,
        strategy="smote",
        target_pos_ratio=0.70,  # 14 * 0.70 ~ 9 pos
        k_neighbors=3,
        random_seed=42,
    )

    y_arr = y_res.to_numpy()
    assert (y_arr == 0).sum() == 14  # Negatives unchanged
    assert (y_arr == 1).sum() >= 9  # Synthetic samples created
    assert len(X_res) == len(y_res)
