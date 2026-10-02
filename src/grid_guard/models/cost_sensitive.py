"""Cost-sensitive LightGBM classifier with custom financially-weighted objective and post-hoc calibration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import polars as pl
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from grid_guard.config.cost_sensitive import CostSensitiveSettings, ProbabilityCalibrationType
from grid_guard.config.financial import BaselineModelSettings
from grid_guard.models.objectives import (
    CostSensitiveWeightedLogisticObjective,
    sigmoid_stable,
)

logger = logging.getLogger(__name__)


class CostSensitiveLightGBM:
    """Gradient boosted decision tree trained with mathematically-derived financial cost objective."""

    def __init__(
        self,
        base_config: BaselineModelSettings | None = None,
        cost_config: CostSensitiveSettings | None = None,
    ) -> None:
        """Initialize the cost-sensitive model.

        Args:
            base_config: Base tree architecture hyperparameters.
            cost_config: Financial cost-sensitive parameters.
        """
        self.base_config = base_config or BaselineModelSettings()
        self.cost_config = cost_config or CostSensitiveSettings()
        self.feature_names: list[str] = []
        self.booster: lgb.Booster | None = None
        self.calibrator: Any = None
        self.calibration_method: ProbabilityCalibrationType = (
            self.cost_config.calibration_method
            if isinstance(self.cost_config.calibration_method, ProbabilityCalibrationType)
            else ProbabilityCalibrationType(self.cost_config.calibration_method)
        )

        # Build LightGBM parameters dictionary
        self.params: dict[str, Any] = {
            "learning_rate": self.base_config.learning_rate,
            "max_depth": self.base_config.max_depth,
            "num_leaves": self.base_config.num_leaves,
            "subsample": self.base_config.subsample,
            "colsample_bytree": self.base_config.colsample_bytree,
            "random_state": self.base_config.random_state,
            "metric": self.base_config.metric or "binary_logloss",
            "verbose": -1,
            "min_child_samples": 20,
        }

    def fit(
        self,
        X_train: pl.DataFrame,
        y_train: pl.Series,
        weights: np.ndarray,
        eval_set: list[tuple[pl.DataFrame, pl.Series]] | None = None,
    ) -> CostSensitiveLightGBM:
        """Fit model using custom cost-sensitive weighted logistic objective.

        Args:
            X_train: Feature matrix of training observations.
            y_train: Binary target labels (1=theft, 0=normal).
            weights: Point-wise financial training weights w_i > 0.
            eval_set: Optional validation set(s) for early stopping / monitoring.

        Returns:
            Fitted CostSensitiveLightGBM instance.
        """
        self.feature_names = X_train.columns
        X_train_np = X_train.to_numpy().astype(np.float32)
        y_train_np = y_train.to_numpy().astype(np.float32)
        w_train_np = np.asarray(weights, dtype=np.float32).ravel()

        if len(X_train_np) != len(w_train_np):
            raise ValueError(
                f"Features count ({len(X_train_np)}) must match weights count ({len(w_train_np)})."
            )

        # Create LightGBM Dataset with financial weights embedded
        train_ds = lgb.Dataset(
            data=X_train_np,
            label=y_train_np,
            weight=w_train_np,
            feature_name=self.feature_names,
            free_raw_data=False,
        )

        valid_sets = [train_ds]
        valid_names = ["train"]

        if eval_set:
            for idx, (X_v, y_v) in enumerate(eval_set):
                X_v_np = X_v.to_numpy().astype(np.float32)
                y_v_np = y_v.to_numpy().astype(np.float32)
                val_ds = lgb.Dataset(
                    data=X_v_np,
                    label=y_v_np,
                    reference=train_ds,
                    feature_name=self.feature_names,
                    free_raw_data=False,
                )
                valid_sets.append(val_ds)
                valid_names.append(f"valid_{idx + 1}")

        # Instantiate custom objective callback
        objective_cb = CostSensitiveWeightedLogisticObjective(default_weights=w_train_np)
        train_params = dict(self.params)
        train_params["objective"] = objective_cb

        callbacks = []
        if len(valid_sets) > 1:
            callbacks.append(lgb.early_stopping(stopping_rounds=30, verbose=False))

        logger.info(
            f"Training CostSensitiveLightGBM on {len(X_train_np):,} samples x {len(self.feature_names)} features "
            f"(custom objective: {self.cost_config.objective_name})..."
        )

        self.booster = lgb.train(
            params=train_params,
            train_set=train_ds,
            num_boost_round=self.base_config.n_estimators,
            valid_sets=valid_sets,
            valid_names=valid_names,
            callbacks=callbacks if callbacks else None,
        )

        best_iter = (
            self.booster.best_iteration
            if self.booster.best_iteration > 0
            else self.base_config.n_estimators
        )
        logger.info(f"CostSensitiveLightGBM fitted successfully (iterations={best_iter}).")
        return self

    def predict_margins(self, X: pl.DataFrame) -> np.ndarray:
        """Predict raw logit margins z_i in (-inf, +inf)."""
        if self.booster is None:
            raise RuntimeError("Model has not been fitted. Call fit() first.")
        X_np = X.to_numpy().astype(np.float32)
        return self.booster.predict(X_np, raw_score=True)

    def predict_raw_proba(self, X: pl.DataFrame) -> np.ndarray:
        """Predict uncalibrated sigmoid probabilities p_i in (0, 1)."""
        margins = self.predict_margins(X)
        return sigmoid_stable(margins)

    def predict_proba(self, X: pl.DataFrame) -> np.ndarray:
        """Predict class probabilities, applying post-hoc calibration if fitted.

        Returns:
            1D array of positive class probabilities in [0, 1].
        """
        raw_prob = self.predict_raw_proba(X)
        if self.calibrator is not None:
            if isinstance(self.calibrator, IsotonicRegression):
                return np.clip(self.calibrator.predict(raw_prob), 0.0, 1.0)
            if isinstance(self.calibrator, LogisticRegression):
                margins = self.predict_margins(X).reshape(-1, 1)
                return self.calibrator.predict_proba(margins)[:, 1]
        return raw_prob

    def predict(self, X: pl.DataFrame, threshold: float | None = None) -> np.ndarray:
        """Predict binary class labels using decision threshold."""
        th = threshold if threshold is not None else self.cost_config.threshold
        probs = self.predict_proba(X)
        return (probs >= th).astype(np.int32)

    def fit_calibration(
        self,
        X_val: pl.DataFrame,
        y_val: pl.Series,
        method: ProbabilityCalibrationType | str = ProbabilityCalibrationType.ISOTONIC,
    ) -> CostSensitiveLightGBM:
        """Fit post-hoc probability calibration strictly on validation data.

        Args:
            X_val: Validation features.
            y_val: Validation ground truth binary labels.
            method: 'isotonic', 'platt', or 'none'.

        Returns:
            Self with fitted calibrator.
        """
        cal_type = (
            method
            if isinstance(method, ProbabilityCalibrationType)
            else ProbabilityCalibrationType(method)
        )
        self.calibration_method = cal_type

        if cal_type == ProbabilityCalibrationType.NONE:
            self.calibrator = None
            logger.info("Probability calibration disabled (raw sigmoid retained).")
            return self

        y_val_np = y_val.to_numpy().astype(np.int32)

        if cal_type == ProbabilityCalibrationType.ISOTONIC:
            raw_p = self.predict_raw_proba(X_val)
            iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
            iso.fit(raw_p, y_val_np)
            self.calibrator = iso
            logger.info(
                f"Fitted Isotonic probability calibration on {len(raw_p):,} validation samples."
            )

        elif cal_type == ProbabilityCalibrationType.PLATT:
            margins = self.predict_margins(X_val).reshape(-1, 1)
            lr = LogisticRegression(solver="lbfgs", max_iter=1000, random_state=42)
            lr.fit(margins, y_val_np)
            self.calibrator = lr
            logger.info(
                f"Fitted Platt (logistic) calibration on {len(margins):,} validation samples."
            )

        return self

    def get_feature_importance(self, importance_type: str = "gain") -> pl.DataFrame:
        """Extract ranked feature importances."""
        if self.booster is None:
            raise RuntimeError("Model has not been fitted.")

        importances = self.booster.feature_importance(importance_type=importance_type)
        return (
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

    def save(self, output_path: Path | str) -> Path:
        """Save LightGBM model booster to disk."""
        if self.booster is None:
            raise RuntimeError("Cannot save an unfitted model.")
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        self.booster.save_model(str(target))
        logger.info(f"Saved cost-sensitive LightGBM model to '{target}'.")
        return target

    def load(self, model_path: Path | str, feature_names: list[str]) -> CostSensitiveLightGBM:
        """Load LightGBM model booster from disk."""
        target = Path(model_path)
        self.booster = lgb.Booster(model_file=str(target))
        self.feature_names = feature_names
        logger.info(f"Loaded cost-sensitive LightGBM model from '{target}'.")
        return self
