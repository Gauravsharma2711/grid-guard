"""Strictly temporal train/validation/test dataset splitting and feature separation."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

import polars as pl

from grid_guard.config.financial import BaselineModelSettings

logger = logging.getLogger(__name__)


@dataclass
class DatasetPartition:
    """Container for features, target, and tracking metadata for a temporal slice."""

    name: str
    X: pl.DataFrame
    y: pl.Series
    metadata: pl.DataFrame
    start_date: date
    end_date: date

    @property
    def num_samples(self) -> int:
        """Return total row count in partition."""
        return len(self.X)

    @property
    def num_meters(self) -> int:
        """Return count of unique meters in partition."""
        return self.metadata.get_column("meter_id").n_unique()

    @property
    def positive_ratio(self) -> float:
        """Return proportion of positive (theft) samples."""
        if len(self.y) == 0:
            return 0.0
        return float(self.y.sum()) / float(len(self.y))


class TemporalDataSplitter:
    """Partitions time-series feature datasets chronologically into train, val, and test slices."""

    def __init__(self, config: BaselineModelSettings | None = None) -> None:
        self.config = config or BaselineModelSettings()
        self.train_start = date.fromisoformat(self.config.train_start)
        self.train_end = date.fromisoformat(self.config.train_end)
        self.val_start = date.fromisoformat(self.config.val_start)
        self.val_end = date.fromisoformat(self.config.val_end)
        self.test_start = date.fromisoformat(self.config.test_start)
        self.test_end = date.fromisoformat(self.config.test_end)

        # Enforce temporal ordering: train < val < test
        if not (
            self.train_start
            <= self.train_end
            < self.val_start
            <= self.val_end
            < self.test_start
            <= self.test_end
        ):
            raise ValueError(
                f"Invalid temporal split boundaries: train=[{self.train_start}, {self.train_end}], "
                f"val=[{self.val_start}, {self.val_end}], test=[{self.test_start}, {self.test_end}]"
            )

    def separate_features(
        self,
        df: pl.DataFrame,
        target_col: str = "tamper_label",
    ) -> tuple[pl.DataFrame, pl.Series, pl.DataFrame]:
        """Strictly separate features X, target y, and tracking metadata.

        Args:
            df: DataFrame containing features, identifiers, and label.
            target_col: Name of the ground truth label column.

        Returns:
            Tuple of (X, y, metadata).
        """
        actual_target = target_col
        if actual_target not in df.columns:
            if "tamper_label" in df.columns:
                actual_target = "tamper_label"
            elif "FLAG" in df.columns:
                actual_target = "FLAG"
            else:
                raise KeyError(f"Target column '{target_col}' not found in DataFrame.")

        # Identifiers and targets excluded from X
        non_feature_cols = {
            actual_target,
            "tamper_label",
            "FLAG",
            "meter_id",
            "timestamp",
            "data_quality_status",
            "feeder_id",
            "leakage_daily_kwh",
            "leakage_monthly_kwh",
            "estimated_leakage_cost",
        }

        feature_cols = [c for c in df.columns if c not in non_feature_cols]
        meta_cols = [
            c
            for c in [
                "meter_id",
                "timestamp",
                "data_quality_status",
                "feeder_id",
                "estimated_leakage_cost",
            ]
            if c in df.columns
        ]

        X = df.select(feature_cols)
        y = df.get_column(actual_target)
        metadata = df.select(meta_cols)

        return X, y, metadata

    def split(
        self,
        df: pl.DataFrame | pl.LazyFrame,
        target_col: str = "tamper_label",
        sampling_stride_days: int | None = None,
        test_final_snapshot_only: bool = False,
    ) -> tuple[DatasetPartition, DatasetPartition, DatasetPartition]:
        """Split DataFrame or LazyFrame into train, validation, and test partitions.

        Args:
            df: Canonical feature DataFrame or LazyFrame containing 'timestamp'.
            target_col: Target column name.
            sampling_stride_days: Optional snapshot sampling stride in days.
            test_final_snapshot_only: If True, test set contains only the final operational date.

        Returns:
            Tuple of (train_partition, val_partition, test_partition).
        """
        stride = (
            sampling_stride_days
            if sampling_stride_days is not None
            else self.config.sampling_stride_days
        )

        # Ensure timestamp is Date
        schema = df.collect_schema() if isinstance(df, pl.LazyFrame) else df.schema
        ts_type = schema["timestamp"]
        if ts_type == pl.Date:
            df_clean = df
        elif ts_type in (pl.String, pl.Utf8):
            df_clean = df.with_columns(pl.col("timestamp").str.to_date())
        elif "Datetime" in str(ts_type):
            df_clean = df.with_columns(pl.col("timestamp").dt.date())
        else:
            df_clean = df.with_columns(pl.col("timestamp").cast(pl.Date))

        # Filter partitions
        train_raw = df_clean.filter(
            (pl.col("timestamp") >= self.train_start) & (pl.col("timestamp") <= self.train_end)
        )
        val_raw = df_clean.filter(
            (pl.col("timestamp") >= self.val_start) & (pl.col("timestamp") <= self.val_end)
        )

        if test_final_snapshot_only:
            test_raw = df_clean.filter(pl.col("timestamp") == self.test_end)
        else:
            test_raw = df_clean.filter(
                (pl.col("timestamp") >= self.test_start) & (pl.col("timestamp") <= self.test_end)
            )

        def _extract_unique_dates(part: pl.DataFrame | pl.LazyFrame) -> list[date]:
            if isinstance(part, pl.LazyFrame):
                u_df = part.select("timestamp").unique().collect()
            else:
                u_df = part.select("timestamp").unique()
            return u_df.sort("timestamp").get_column("timestamp").to_list()

        # Apply snapshot stride if configured
        if stride and stride > 1:
            train_dates = _extract_unique_dates(train_raw)
            sampled_train_dates = train_dates[::stride]
            train_raw = train_raw.filter(pl.col("timestamp").is_in(sampled_train_dates))

            val_dates = _extract_unique_dates(val_raw)
            sampled_val_dates = val_dates[::stride]
            val_raw = val_raw.filter(pl.col("timestamp").is_in(sampled_val_dates))

            if not test_final_snapshot_only:
                test_dates = _extract_unique_dates(test_raw)
                sampled_test_dates = test_dates[::stride]
                test_raw = test_raw.filter(pl.col("timestamp").is_in(sampled_test_dates))

        # Collect if lazy
        if isinstance(train_raw, pl.LazyFrame):
            train_raw = train_raw.collect()
        if isinstance(val_raw, pl.LazyFrame):
            val_raw = val_raw.collect()
        if isinstance(test_raw, pl.LazyFrame):
            test_raw = test_raw.collect()

        X_train, y_train, meta_train = self.separate_features(train_raw, target_col=target_col)
        X_val, y_val, meta_val = self.separate_features(val_raw, target_col=target_col)
        X_test, y_test, meta_test = self.separate_features(test_raw, target_col=target_col)

        train_part = DatasetPartition(
            name="train",
            X=X_train,
            y=y_train,
            metadata=meta_train,
            start_date=self.train_start,
            end_date=self.train_end,
        )
        val_part = DatasetPartition(
            name="val",
            X=X_val,
            y=y_val,
            metadata=meta_val,
            start_date=self.val_start,
            end_date=self.val_end,
        )
        test_part = DatasetPartition(
            name="test",
            X=X_test,
            y=y_test,
            metadata=meta_test,
            start_date=self.test_start,
            end_date=self.test_end,
        )

        logger.info(
            f"Temporal split complete: Train={train_part.num_samples:,} rows ({train_part.num_meters:,} meters, "
            f"{train_part.positive_ratio:.2%} pos), Val={val_part.num_samples:,} rows ({val_part.positive_ratio:.2%} pos), "
            f"Test={test_part.num_samples:,} rows ({test_part.positive_ratio:.2%} pos)."
        )
        return train_part, val_part, test_part
