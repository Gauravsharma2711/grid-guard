"""Unit tests for ImbalanceAwareLightGBM model fitting and evaluation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl
import pytest

from grid_guard.config.financial import BaselineModelSettings
from grid_guard.config.imbalance import ImbalanceSettings
from grid_guard.models.imbalance import ImbalanceAwareLightGBM


@pytest.fixture
def synthetic_train_val_data() -> tuple[pl.DataFrame, pl.Series, pl.DataFrame, pl.Series]:
    """Generate synthetic imbalanced training and validation data."""
    rng = np.random.default_rng(42)
    n_train = 100
    n_val = 30

    X_train = pl.DataFrame(
        {
            "f1": rng.normal(5.0, 1.0, n_train).astype(np.float32),
            "f2": rng.normal(10.0, 2.0, n_train).astype(np.float32),
        }
    )
    # 10% positive class
    y_train = pl.Series("label", [1] * 10 + [0] * (n_train - 10), dtype=pl.Int32)

    X_val = pl.DataFrame(
        {
            "f1": rng.normal(5.0, 1.0, n_val).astype(np.float32),
            "f2": rng.normal(10.0, 2.0, n_val).astype(np.float32),
        }
    )
    y_val = pl.Series("label", [1] * 3 + [0] * (n_val - 3), dtype=pl.Int32)

    return X_train, y_train, X_val, y_val


def test_imbalance_model_fit_predict(
    synthetic_train_val_data: tuple[pl.DataFrame, pl.Series, pl.DataFrame, pl.Series],
) -> None:
    """Verify fitting ImbalanceAwareLightGBM with scale_pos_weight."""
    X_train, y_train, X_val, y_val = synthetic_train_val_data

    model = ImbalanceAwareLightGBM(
        base_config=BaselineModelSettings(n_estimators=10, max_depth=3, num_leaves=7),
        imbalance_config=ImbalanceSettings(threshold=0.5),
        scale_pos_weight=5.0,
    )
    eval_set = [(X_val, y_val)]
    model.fit(X_train, y_train, eval_set=eval_set)

    assert model.scale_pos_weight == 5.0
    assert len(model.feature_names) == 2

    # Predict proba
    probs = model.predict_proba(X_val)
    assert len(probs) == len(X_val)
    assert np.all((probs >= 0.0) & (probs <= 1.0))

    # Predict class
    preds = model.predict(X_val, threshold=0.5)
    assert len(preds) == len(X_val)
    assert set(preds).issubset({0, 1})

    # Feature importance
    df_imp = model.get_feature_importance("gain")
    assert len(df_imp) == 2
    assert "importance" in df_imp.columns


def test_imbalance_model_save_load(
    synthetic_train_val_data: tuple[pl.DataFrame, pl.Series, pl.DataFrame, pl.Series],
    tmp_path: Path,
) -> None:
    """Verify save and load round-trip of ImbalanceAwareLightGBM model."""
    X_train, y_train, X_val, _ = synthetic_train_val_data

    model = ImbalanceAwareLightGBM(
        base_config=BaselineModelSettings(n_estimators=5, max_depth=2, num_leaves=3),
        scale_pos_weight=3.0,
    )
    model.fit(X_train, y_train)

    probs_before = model.predict_proba(X_val)

    save_path = tmp_path / "model.txt"
    model.save(save_path)
    assert save_path.exists()

    loaded_model = ImbalanceAwareLightGBM(scale_pos_weight=3.0)
    loaded_model.load(save_path, feature_names=model.feature_names)

    probs_after = loaded_model.predict_proba(X_val)
    np.testing.assert_allclose(probs_before, probs_after, rtol=1e-5)
