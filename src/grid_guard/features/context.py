"""Peer, feeder, and contextual grouping feature extraction."""

from __future__ import annotations

import logging

import polars as pl

from grid_guard.features.ratios import safe_div_expr
from grid_guard.features.registry import (
    FeatureCategory,
    FeatureDefinition,
    FeatureRegistry,
    LeakageRisk,
)

logger = logging.getLogger(__name__)


def register_context_features(registry: FeatureRegistry) -> None:
    """Register contextual and peer-group features in registry."""
    features = [
        FeatureDefinition(
            name="peer_group_mean",
            category=FeatureCategory.PEER_CONTEXT,
            source_columns=("consumption_kwh", "feeder_id"),
            window_days=None,
            lag_days=None,
            description="Leave-one-out peer average consumption for the same timestamp and feeder",
            dtype="Float32",
            leakage_risk=LeakageRisk.CONTEXT_DEPENDENT,
            min_history_days=1,
            requires_context=True,
        ),
        FeatureDefinition(
            name="meter_to_peer_ratio",
            category=FeatureCategory.PEER_CONTEXT,
            source_columns=("consumption_kwh", "feeder_id"),
            window_days=None,
            lag_days=None,
            description="Ratio of meter consumption to leave-one-out peer group average",
            dtype="Float32",
            leakage_risk=LeakageRisk.CONTEXT_DEPENDENT,
            min_history_days=1,
            requires_context=True,
        ),
        FeatureDefinition(
            name="peer_group_deviation",
            category=FeatureCategory.PEER_CONTEXT,
            source_columns=("consumption_kwh", "feeder_id"),
            window_days=None,
            lag_days=None,
            description="Absolute difference between meter consumption and leave-one-out peer group mean",
            dtype="Float32",
            leakage_risk=LeakageRisk.CONTEXT_DEPENDENT,
            min_history_days=1,
            requires_context=True,
        ),
    ]
    for feat in features:
        registry.register(feat)


class ContextFeatureExtractor:
    """Extracts peer-group and feeder-level contextual features using leave-one-out aggregation."""

    def __init__(
        self,
        feeder_col: str = "feeder_id",
        epsilon: float = 1e-4,
        registry: FeatureRegistry | None = None,
    ) -> None:
        self.feeder_col = feeder_col
        self.epsilon = epsilon
        self.registry = registry
        if self.registry is not None:
            register_context_features(self.registry)

    def is_available(self, schema_or_cols: set[str] | list[str]) -> bool:
        """Check whether required contextual metadata columns are present in schema."""
        return self.feeder_col in schema_or_cols

    def extract(
        self,
        df: pl.DataFrame,
        value_col: str = "consumption_kwh",
        timestamp_col: str = "timestamp",
        meter_col: str = "meter_id",
    ) -> pl.DataFrame:
        """Compute leave-one-out peer aggregate features if feeder column is present.

        If feeder column is missing, returns df unmodified.

        Args:
            df: Input DataFrame.
            value_col: Consumption column name.
            timestamp_col: Timestamp column name.
            meter_col: Meter identifier column.

        Returns:
            DataFrame with peer contextual features appended if metadata is present.
        """
        if not self.is_available(df.columns):
            logger.info(
                f"Contextual column '{self.feeder_col}' not present; peer features skipped."
            )
            return df

        # Compute total sum and count per (feeder, timestamp)
        group_cols = [self.feeder_col, timestamp_col]
        agg_exprs = [
            pl.col(value_col).sum().alias("_group_sum"),
            pl.col(value_col).count().alias("_group_count"),
        ]

        df_with_aggs = df.join(
            df.group_by(group_cols).agg(agg_exprs),
            on=group_cols,
            how="left",
        )

        # Leave-one-out peer mean: (group_sum - my_value) / (group_count - 1)
        peer_sum = pl.col("_group_sum") - pl.col(value_col)
        peer_count = (pl.col("_group_count") - 1).clip(lower_bound=1)
        peer_mean = (peer_sum / peer_count).cast(pl.Float32)

        peer_ratio = safe_div_expr(
            pl.col(value_col),
            peer_mean,
            epsilon=self.epsilon,
            default_zero_over_zero=1.0,
        ).cast(pl.Float32)

        peer_dev = (pl.col(value_col) - peer_mean).cast(pl.Float32)

        result = df_with_aggs.with_columns(
            [
                peer_mean.alias("peer_group_mean"),
                peer_ratio.alias("meter_to_peer_ratio"),
                peer_dev.alias("peer_group_deviation"),
            ]
        ).drop(["_group_sum", "_group_count"])
        return result
