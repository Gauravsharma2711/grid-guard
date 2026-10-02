"""Imbalance-aware LightGBM model supporting class weighting and controlled resampling."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import polars as pl

from grid_guard.config.financial import BaselineModelSettings
from grid_guard.config.imbalance import ImbalanceSettings

logger = logging.getLogger(__name__)


class ImbalanceAwareLightGBM:
    """LightGBM classifier incorporating class-weighting or controlled training resampling."""

    def __init__(
        self,
        base_config: BaselineModelSettings | None = None,
        imbalance_config: ImbalanceSettings | None = None,
        scale_pos_weight: float = 1.0,
    ) -> None:
        """Initialize imbalance-aware LightGBM model.

        Args:
            base_config: Base tree architecture hyperparameters.
            imbalance_config: Imbalance settings (strategy, target ratio, etc.).
            scale_pos_weight: Weight applied to positive (theft) class loss gradients.
        """
        self.base_config = base_config or BaselineModelSettings()
        self.imbalance_config = imbalance_config or ImbalanceSettings()
        self.scale_pos_weight = float(scale_pos_weight)
        self.feature_names: list[str] = []
        self.model: lgb.LGBMClassifier | None = None
        self.booster: lgb.Booster | None = None

        # Build LightGBM parameters with configured scale_pos_weight
        self.params: dict[str, Any] = {
            "objective": self.base_config.objective,
            "learning_rate": self.base_config.learning_rate,
            "n_estimators": self.base_config.n_estimators,
            "max_depth": self.base_config.max_depth,
            "num_leaves": self.base_config.num_leaves,
            "subsample": self.base_config.subsample,
            "colsample_bytree": self.base_config.colsample_bytree,
            "random_state": self.base_config.random_state,
            "scale_pos_weight": self.scale_pos_weight,
            "verbose": -1,
        }

    def fit(
        self,
        X_train: pl.DataFrame,
        y_train: pl.Series,
        eval_set: list[tuple[pl.DataFrame, pl.Series]] | None = None,
    ) -> ImbalanceAwareLightGBM:
        """Fit imbalance-aware LightGBM model on training data.

        Validation set (eval_set) is used strictly for early stopping and remains unresampled.

        Args:
            X_train: Training feature DataFrame.
            y_train: Training binary label Series.
            eval_set: Optional validation sets (unweighted/unresampled) for early stopping.

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

        self.booster = self.model.booster_
        logger.info(
            f"Fitted Imbalance-Aware LightGBM (scale_pos_weight={self.scale_pos_weight:.2f}) "
            f"across {len(self.feature_names)} features on {len(y_np):,} samples."
        )
        return self

    def predict_proba(self, X: pl.DataFrame) -> np.ndarray:
        """Predict positive class (tampering) probabilities."""
        X_np = X.to_numpy().astype(np.float32)
        if self.booster is not None:
            return self.booster.predict(X_np)
        if self.model is not None:
            return self.model.predict_proba(X_np)[:, 1]
        raise RuntimeError("Model has not been fitted. Call fit() first.")

    def predict(self, X: pl.DataFrame, threshold: float | None = None) -> np.ndarray:
        """Predict binary class labels using decision threshold."""
        th = threshold if threshold is not None else self.imbalance_config.threshold
        probs = self.predict_proba(X)
        return (probs >= th).astype(np.int32)

    def get_feature_importance(self, importance_type: str = "gain") -> pl.DataFrame:
        """Extract ranked feature importances."""
        booster = self.booster or (self.model.booster_ if self.model else None)
        if booster is None:
            raise RuntimeError("Model has not been fitted.")

        importances = booster.feature_importance(importance_type=importance_type)
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
        booster = self.booster or (self.model.booster_ if self.model else None)
        if booster is None:
            raise RuntimeError("Cannot save an unfitted model.")
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        booster.save_model(str(target))
        logger.info(f"Saved imbalance-aware LightGBM model to '{target}'.")
        return target

    def load(self, model_path: Path | str, feature_names: list[str]) -> ImbalanceAwareLightGBM:
        """Load LightGBM model booster from disk."""
        target = Path(model_path)
        self.booster = lgb.Booster(model_file=str(target))
        self.feature_names = feature_names
        logger.info(f"Loaded imbalance-aware LightGBM model from '{target}'.")
        return self
