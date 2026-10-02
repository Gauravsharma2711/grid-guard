"""SHAP TreeExplainer integration and local/global attribution engine for LightGBM models."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
import polars as pl
import shap

from grid_guard.explainability.feature_mapping import FeatureMapper
from grid_guard.explainability.schemas import FeatureContribution

logger = logging.getLogger(__name__)


class ShapExplainer:
    """Wrapper around shap.TreeExplainer for Tree-Boosted NTL anomaly models."""

    def __init__(
        self,
        model: lgb.Booster | str | Path,
        feature_mapper: FeatureMapper | None = None,
    ) -> None:
        """Initialize with loaded Booster or path to checkpoint file."""
        if isinstance(model, (str, Path)):
            self.model = lgb.Booster(model_file=str(model))
        else:
            self.model = model

        self.feature_names = list(self.model.feature_name())
        self.feature_mapper = feature_mapper or FeatureMapper()

        # Initialize SHAP TreeExplainer
        self.explainer = shap.TreeExplainer(self.model)
        raw_ev = self.explainer.expected_value
        if isinstance(raw_ev, (list, np.ndarray)):
            self.base_value = float(raw_ev[0])
        else:
            self.base_value = float(raw_ev)

        logger.info(
            f"Initialized TreeExplainer for {len(self.feature_names)} features; "
            f"base log-odds value: {self.base_value:.4f}"
        )

    def explain(
        self,
        X: pd.DataFrame | pl.DataFrame | np.ndarray,
        verify_reconstruction: bool = True,
        tolerance: float = 1e-4,
    ) -> np.ndarray:
        """Compute SHAP values in the model's native raw margin (log-odds) space.

        Args:
            X: Input feature matrix matching model's feature_names.
            verify_reconstruction: If True, validates base_value + sum(shap) == raw_margin.
            tolerance: Maximum allowable absolute discrepancy for reconstruction.

        Returns:
            2D numpy array of shape (n_samples, n_features) containing SHAP values.
        """
        if isinstance(X, pl.DataFrame):
            X_df = X.select(self.feature_names).to_pandas()
        elif isinstance(X, pd.DataFrame):
            X_df = X[self.feature_names]
        else:
            X_df = pd.DataFrame(X, columns=self.feature_names)

        shap_vals = self.explainer.shap_values(X_df)
        if isinstance(shap_vals, list):
            shap_matrix = np.asarray(shap_vals[0], dtype=np.float64)
        else:
            shap_matrix = np.asarray(shap_vals, dtype=np.float64)

        if verify_reconstruction:
            raw_margins = self.model.predict(X_df, raw_score=True)
            reconstructed = self.base_value + shap_matrix.sum(axis=1)
            discrepancies = np.abs(reconstructed - raw_margins)
            max_disc = float(np.max(discrepancies))
            if max_disc > tolerance:
                raise ValueError(
                    f"SHAP additive reconstruction failed: max discrepancy {max_disc:.2e} "
                    f"exceeds tolerance {tolerance:.2e}"
                )

        return shap_matrix

    def get_global_importance(
        self,
        shap_matrix: np.ndarray,
    ) -> list[dict[str, Any]]:
        """Calculate global feature importance ranked by mean absolute SHAP value."""
        mean_abs = np.mean(np.abs(shap_matrix), axis=0)
        mean_signed = np.mean(shap_matrix, axis=0)
        sorted_indices = np.argsort(mean_abs)[::-1]

        records: list[dict[str, Any]] = []
        for rank, idx in enumerate(sorted_indices, 1):
            fname = self.feature_names[idx]
            meta = self.feature_mapper.resolve(fname)
            records.append(
                {
                    "rank": rank,
                    "feature_name": fname,
                    "display_name": meta.display_name,
                    "category": meta.category,
                    "mean_abs_shap": float(mean_abs[idx]),
                    "mean_signed_shap": float(mean_signed[idx]),
                    "description": meta.description,
                }
            )
        return records

    def explain_instance(
        self,
        instance_row: dict[str, Any] | pd.Series,
        shap_row: np.ndarray,
        max_positive: int = 4,
        max_negative: int = 2,
    ) -> tuple[list[FeatureContribution], list[FeatureContribution]]:
        """Extract top positive and top negative contributing features for a single sample."""
        row_dict = instance_row.to_dict() if isinstance(instance_row, pd.Series) else instance_row

        pos_items: list[tuple[int, float]] = []
        neg_items: list[tuple[int, float]] = []

        for idx, s_val in enumerate(shap_row):
            if s_val > 1e-4:
                pos_items.append((idx, float(s_val)))
            elif s_val < -1e-4:
                neg_items.append((idx, float(s_val)))

        # Sort positive by magnitude descending
        pos_items.sort(key=lambda x: x[1], reverse=True)
        # Sort negative by signed value ascending (most negative first)
        neg_items.sort(key=lambda x: x[1])

        # Build FeatureContribution objects for top positive
        pos_contributions: list[FeatureContribution] = []
        for rank, (idx, s_val) in enumerate(pos_items[:max_positive], 1):
            fname = self.feature_names[idx]
            meta = self.feature_mapper.resolve(fname)
            f_val = float(row_dict.get(fname, 0.0))
            base_ref = (
                float(row_dict[meta.reference_feature])
                if meta.reference_feature and meta.reference_feature in row_dict
                else None
            )
            pos_contributions.append(
                FeatureContribution(
                    feature_name=fname,
                    display_name=meta.display_name,
                    category=meta.category,
                    feature_value=f_val,
                    baseline_value=base_ref,
                    shap_value=s_val,
                    contribution_direction="positive",
                    rank=rank,
                    description=meta.description,
                )
            )

        # Build FeatureContribution objects for top negative (counter-evidence)
        neg_contributions: list[FeatureContribution] = []
        for rank, (idx, s_val) in enumerate(neg_items[:max_negative], 1):
            fname = self.feature_names[idx]
            meta = self.feature_mapper.resolve(fname)
            f_val = float(row_dict.get(fname, 0.0))
            base_ref = (
                float(row_dict[meta.reference_feature])
                if meta.reference_feature and meta.reference_feature in row_dict
                else None
            )
            neg_contributions.append(
                FeatureContribution(
                    feature_name=fname,
                    display_name=meta.display_name,
                    category=meta.category,
                    feature_value=f_val,
                    baseline_value=base_ref,
                    shap_value=s_val,
                    contribution_direction="negative",
                    rank=rank,
                    description=meta.description,
                )
            )

        return pos_contributions, neg_contributions
