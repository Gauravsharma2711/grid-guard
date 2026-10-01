"""Standard unweighted LightGBM baseline model for electricity theft classification."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import polars as pl

from grid_guard.config.financial import BaselineModelSettings

logger = logging.getLogger(__name__)


class BaselineLightGBM:
    """Conventional unweighted LightGBM classifier establishing the Phase 4 benchmark."""

    def __init__(self, config: BaselineModelSettings | None = None) -> None:
        self.config = config or BaselineModelSettings()
        self.feature_names: list[str] = []
        self.model: lgb.LGBMClassifier | None = None

        # Build standard unweighted LightGBM parameters (NO class weighting, NO scale_pos_weight)
        self.params: dict[str, Any] = {
            "objective": self.config.objective,
            "learning_rate": self.config.learning_rate,
            "n_estimators": self.config.n_estimators,
            "max_depth": self.config.max_depth,
            "num_leaves": self.config.num_leaves,
            "subsample": self.config.subsample,
            "colsample_bytree": self.config.colsample_bytree,
            "random_state": self.config.random_state,
            "class_weight": None,  # Strictly unweighted
            "scale_pos_weight": 1.0,  # Strictly unweighted
            "verbose": -1,
        }

    def fit(
        self,
        X_train: pl.DataFrame,
        y_train: pl.Series,
        eval_set: list[tuple[pl.DataFrame, pl.Series]] | None = None,
    ) -> BaselineLightGBM:
        """Fit unweighted LightGBM model on training partition.

        Args:
            X_train: Training feature DataFrame.
            y_train: Training binary label Series.
            eval_set: Optional validation sets for early stopping / monitoring.

        Returns:
            self.
        """
        self.feature_names = X_train.columns
        X_np = X_train.to_numpy().astype(np.float32)
        y_np = y_train.to_numpy().astype(np.int32)

        callbacks: list[Any] = [lgb.early_stopping(stopping_rounds=30, verbose=False)]

        self.model = lgb.LGBMClassifier(**self.params)
        if eval_set and len(eval_set) > 0:
            es_x, es_y = eval_set[0]
            eval_x_np = es_x.to_numpy().astype(np.float32)
            eval_y_np = es_y.to_numpy().astype(np.int32)
            self.model.fit(
                X_np,
                y_np,
                eval_X=eval_x_np,
                eval_y=eval_y_np,
                callbacks=callbacks,
            )
        else:
            self.model.fit(X_np, y_np)
        logger.info(
            f"Fitted LightGBM model across {len(self.feature_names)} features on {len(y_np):,} samples."
        )
        return self

    def predict_proba(self, X: pl.DataFrame) -> np.ndarray:
        """Predict positive class (tampering) probabilities.

        Args:
            X: Input feature DataFrame.

        Returns:
            1D NumPy array of positive class probabilities in [0.0, 1.0].
        """
        if self.model is None:
            raise RuntimeError("Model has not been fitted. Call fit() first.")
        X_np = X.to_numpy().astype(np.float32)
        # Class 1 probabilities
        return self.model.predict_proba(X_np)[:, 1]

    def predict(self, X: pl.DataFrame, threshold: float | None = None) -> np.ndarray:
        """Predict binary class labels using the conventional threshold.

        Args:
            X: Input feature DataFrame.
            threshold: Decision threshold. Defaults to conventional 0.5.

        Returns:
            1D NumPy array of binary predictions (0 or 1).
        """
        th = threshold if threshold is not None else self.config.threshold
        probs = self.predict_proba(X)
        return (probs >= th).astype(np.int32)

    def get_feature_importance(self, importance_type: str = "gain") -> pl.DataFrame:
        """Extract ranked feature importances.

        Args:
            importance_type: 'gain' (total gains of splits) or 'split' (number of splits).

        Returns:
            Polars DataFrame with columns [feature, importance, importance_type, rank].
        """
        if self.model is None:
            raise RuntimeError("Model has not been fitted.")

        importances = self.model.booster_.feature_importance(importance_type=importance_type)
        df_imp = (
            pl.DataFrame(
                {
                    "feature": self.feature_names,
                    "importance": importances.astype(np.float64),
                }
            )
            .sort("importance", descending=True)
            .with_columns(
                [
                    pl.lit(importance_type).alias("importance_type"),
                    (pl.int_range(0, pl.len()) + 1).alias("rank"),
                ]
            )
        )
        return df_imp

    def save(self, output_path: Path | str) -> Path:
        """Save LightGBM model booster to disk."""
        if self.model is None:
            raise RuntimeError("Cannot save an unfitted model.")
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        self.model.booster_.save_model(str(target))
        logger.info(f"Saved baseline LightGBM model to '{target}'.")
        return target

    def load(self, model_path: Path | str, feature_names: list[str]) -> BaselineLightGBM:
        """Load LightGBM model booster from disk."""
        target = Path(model_path)
        booster = lgb.Booster(model_file=str(target))
        self.feature_names = feature_names
        self.model = lgb.LGBMClassifier(**self.params)
        self.model._Booster = booster
        self.model._n_features = len(feature_names)
        self.model._classes = np.array([0, 1])
        logger.info(f"Loaded baseline LightGBM model from '{target}'.")
        return self
