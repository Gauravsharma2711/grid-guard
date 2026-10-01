"""Canonical temporal feature engineering pipeline for smart-meter AMI data."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import polars as pl

from grid_guard.config.settings import FeatureSettings, get_settings
from grid_guard.features.calendar import CalendarFeatureExtractor
from grid_guard.features.context import ContextFeatureExtractor
from grid_guard.features.lags import LagFeatureExtractor
from grid_guard.features.periodicity import PeriodicityFeatureExtractor
from grid_guard.features.quality import QualityFeatureExtractor
from grid_guard.features.ratios import RatioFeatureExtractor
from grid_guard.features.registry import FeatureCategory, FeatureRegistry
from grid_guard.features.rolling import RollingFeatureExtractor
from grid_guard.features.signatures import TamperingSignatureExtractor

logger = logging.getLogger(__name__)


class FeaturePipeline:
    """End-to-end temporal feature engineering pipeline for Grid-Guard."""

    def __init__(
        self,
        config: FeatureSettings | None = None,
        registry: FeatureRegistry | None = None,
    ) -> None:
        self.config = config or get_settings().features
        self.registry = registry or FeatureRegistry()

        # Initialize modular feature extractors with shared registry
        self.calendar_extractor = CalendarFeatureExtractor(registry=self.registry)
        self.lag_extractor = LagFeatureExtractor(lags=self.config.lags, registry=self.registry)
        self.rolling_extractor = RollingFeatureExtractor(
            windows=self.config.rolling_windows, registry=self.registry
        )
        self.ratio_extractor = RatioFeatureExtractor(
            epsilon=self.config.epsilon, registry=self.registry
        )
        self.signature_extractor = TamperingSignatureExtractor(
            zero_threshold=self.config.zero_threshold,
            flatline_tolerance=self.config.flatline_tolerance,
            epsilon=self.config.epsilon,
            registry=self.registry,
        )
        self.periodicity_extractor = PeriodicityFeatureExtractor(
            epsilon=self.config.epsilon, registry=self.registry
        )
        self.context_extractor = ContextFeatureExtractor(
            epsilon=self.config.epsilon, registry=self.registry
        )
        self.quality_extractor = QualityFeatureExtractor(registry=self.registry)

    def transform(
        self,
        df: pl.DataFrame,
        value_col: str = "consumption_kwh",
        timestamp_col: str = "timestamp",
        meter_col: str = "meter_id",
    ) -> pl.DataFrame:
        """Execute feature engineering across all modular extractors.

        Args:
            df: Input DataFrame containing meter_id, timestamp, consumption_kwh.
            value_col: Consumption column name.
            timestamp_col: Timestamp column name.
            meter_col: Meter identifier column name.

        Returns:
            DataFrame with all engineered features appended in temporal order.
        """
        # Step 1: Ensure chronological ordering per meter
        df_sorted = df.sort([meter_col, timestamp_col])

        # Step 2: Calendar expressions
        cal_exprs = self.calendar_extractor.get_expressions(timestamp_col=timestamp_col)

        # Step 3: Backward lag expressions
        lag_exprs = self.lag_extractor.get_expressions(value_col=value_col, meter_col=meter_col)

        # Step 4: Trailing rolling statistics
        rolling_exprs = self.rolling_extractor.get_expressions(
            value_col=value_col, meter_col=meter_col
        )

        # Step 5: Trailing data quality indicators
        quality_exprs = self.quality_extractor.get_expressions(
            value_col=value_col, meter_col=meter_col
        )

        # Apply calendar, lags, rolling, and quality features
        df_transformed = df_sorted.with_columns(
            cal_exprs + lag_exprs + rolling_exprs + quality_exprs
        )

        # Step 6: Ratio expressions (depend on rolling statistics)
        ratio_exprs = self.ratio_extractor.get_expressions(meter_col=meter_col)

        # Step 7: Tampering signatures (depend on rolling and lags)
        sig_exprs = self.signature_extractor.get_expressions(
            value_col=value_col, meter_col=meter_col
        )

        # Step 8: Periodicity and autocorrelation expressions
        period_exprs = self.periodicity_extractor.get_expressions(
            value_col=value_col, meter_col=meter_col
        )

        df_transformed = df_transformed.with_columns(ratio_exprs + sig_exprs + period_exprs)

        # Step 9: Contextual features (if feeder metadata is present)
        df_transformed = self.context_extractor.extract(
            df_transformed,
            value_col=value_col,
            timestamp_col=timestamp_col,
            meter_col=meter_col,
        )

        return df_transformed

    def process_dataset(
        self,
        input_series_path: Path | str,
        output_feature_path: Path | str,
        clean_wide_path: Path | str | None = None,
        batch_size_meters: int | None = None,
    ) -> Path:
        """Process entire AMI series dataset with memory-safe chunking and save canonical Parquet.

        Args:
            input_series_path: Path to canonical_ami_series.parquet.
            output_feature_path: Destination path for canonical feature Parquet dataset.
            clean_wide_path: Optional path to clean wide dataset to join quality metrics.
            batch_size_meters: Number of meters to process per chunk. Defaults to config.

        Returns:
            Path to generated output feature dataset.
        """
        in_path = Path(input_series_path)
        out_path = Path(output_feature_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        batch_size = batch_size_meters or self.config.batch_size_meters
        logger.info(
            f"Starting feature engineering on '{in_path}' with batch size {batch_size} meters..."
        )
        start_time = time.time()

        # Read unique meter IDs
        unique_meters = (
            pl.scan_parquet(in_path)
            .select("meter_id")
            .unique()
            .collect()
            .get_column("meter_id")
            .to_list()
        )
        total_meters = len(unique_meters)
        logger.info(f"Discovered {total_meters:,} unique meters to process.")

        # Read quality metrics if available
        quality_df: pl.DataFrame | None = None
        if clean_wide_path and Path(clean_wide_path).is_file():
            q_cols = ["meter_id", "coverage_ratio", "missing_ratio", "imputation_ratio"]
            schema_cols = pl.scan_parquet(clean_wide_path).collect_schema().names()
            avail_q_cols = [c for c in q_cols if c in schema_cols]
            quality_df = pl.read_parquet(clean_wide_path, columns=avail_q_cols)

        # Process in batches
        num_batches = (total_meters + batch_size - 1) // batch_size
        temp_dir = out_path.parent / "_feature_chunks"
        temp_dir.mkdir(parents=True, exist_ok=True)
        chunk_files: list[Path] = []

        try:
            for b_idx in range(num_batches):
                b_meters = unique_meters[b_idx * batch_size : (b_idx + 1) * batch_size]
                b_start = time.time()

                # Filter series for this batch of meters
                batch_raw = (
                    pl.scan_parquet(in_path)
                    .filter(pl.col("meter_id").is_in(pl.lit(b_meters)))
                    .collect()
                )

                # Attach meter-level quality indicators if available
                if quality_df is not None:
                    batch_raw = batch_raw.join(
                        quality_df.filter(pl.col("meter_id").is_in(pl.lit(b_meters))),
                        on="meter_id",
                        how="left",
                    )

                # Transform batch
                batch_features = self.transform(batch_raw)

                # Write chunk Parquet
                chunk_file = temp_dir / f"chunk_{b_idx:04d}.parquet"
                batch_features.write_parquet(chunk_file, compression="zstd")
                chunk_files.append(chunk_file)

                b_elapsed = time.time() - b_start
                logger.info(
                    f"Batch {b_idx + 1}/{num_batches} ({len(b_meters):,} meters, "
                    f"{len(batch_features):,} rows) processed in {b_elapsed:.2f}s."
                )

            # Combine chunks into single canonical Parquet dataset
            logger.info(f"Merging {len(chunk_files)} chunk files into '{out_path}'...")
            pl.concat([pl.read_parquet(f) for f in chunk_files]).write_parquet(
                out_path, compression="zstd"
            )

        finally:
            # Clean up temporary chunks
            for f in chunk_files:
                if f.is_file():
                    f.unlink()
            if temp_dir.is_dir():
                temp_dir.rmdir()

        elapsed = time.time() - start_time
        logger.info(
            f"Feature engineering pipeline complete in {elapsed:.2f}s! Saved to '{out_path}'."
        )
        return out_path

    def generate_quality_report(
        self,
        df: pl.DataFrame,
        output_json: Path | str | None = None,
        output_md: Path | str | None = None,
    ) -> dict[str, Any]:
        """Validate feature properties: row granularity, uniqueness, null rates, and finite numbers.

        Args:
            df: Transformed feature DataFrame.
            output_json: Path to save JSON quality report.
            output_md: Path to save Markdown summary report.

        Returns:
            Dictionary containing audit report statistics.
        """
        total_rows = len(df)
        total_meters = df.get_column("meter_id").n_unique()

        # Timestamp uniqueness check per meter
        dup_count = total_rows - len(df.unique(subset=["meter_id", "timestamp"]))

        # Analyze feature columns
        non_feature_cols = {
            "meter_id",
            "timestamp",
            "tamper_label",
            "data_quality_status",
            "feeder_id",
        }
        feature_cols = [c for c in df.columns if c not in non_feature_cols]

        feature_stats: dict[str, dict[str, Any]] = {}
        infinite_columns: list[str] = []
        high_null_columns: list[str] = []
        constant_columns: list[str] = []

        for col in feature_cols:
            series = df.get_column(col)
            nan_count = int(series.is_nan().sum()) if series.dtype.is_float() else 0
            missing_count = series.null_count() + nan_count
            null_pct = round((missing_count / total_rows) * 100.0, 2)

            is_numeric = series.dtype.is_numeric()
            inf_count = 0
            min_val: float | None = None
            max_val: float | None = None
            mean_val: float | None = None
            std_val: float | None = None

            if is_numeric and missing_count < total_rows:
                non_null = series.drop_nulls()
                if series.dtype.is_float():
                    non_null = non_null.drop_nans()

                if len(non_null) > 0:
                    # Check for infinite values
                    inf_count = int(non_null.is_infinite().sum())
                    if inf_count > 0:
                        infinite_columns.append(col)

                    min_val = (
                        round(float(non_null.min()), 4) if non_null.min() is not None else None
                    )
                    max_val = (
                        round(float(non_null.max()), 4) if non_null.max() is not None else None
                    )
                    mean_val = (
                        round(float(non_null.mean()), 4) if non_null.mean() is not None else None
                    )
                    std_val = (
                        round(float(non_null.std()), 4) if non_null.std() is not None else None
                    )

                    # Check constant column
                    if min_val == max_val and min_val is not None:
                        constant_columns.append(col)

            if null_pct > 80.0:
                high_null_columns.append(col)

            feature_stats[col] = {
                "dtype": str(series.dtype),
                "null_count": missing_count,
                "null_pct": null_pct,
                "infinite_count": inf_count,
                "min": min_val,
                "max": max_val,
                "mean": mean_val,
                "std": std_val,
            }

        report: dict[str, Any] = {
            "total_rows": total_rows,
            "total_meters": total_meters,
            "total_features": len(feature_cols),
            "duplicate_meter_timestamp_pairs": dup_count,
            "infinite_value_columns": infinite_columns,
            "high_null_columns": high_null_columns,
            "constant_columns": constant_columns,
            "features_by_category": {
                cat.value: len(self.registry.by_category(cat)) for cat in FeatureCategory
            },
            "feature_details": feature_stats,
        }

        # Save JSON if requested
        if output_json:
            j_path = Path(output_json)
            j_path.parent.mkdir(parents=True, exist_ok=True)
            with open(j_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)

        # Save Markdown if requested
        if output_md:
            m_path = Path(output_md)
            m_path.parent.mkdir(parents=True, exist_ok=True)
            md_lines = [
                "# Grid-Guard Feature Quality & Validation Report",
                "",
                f"**Total Records Processed**: {total_rows:,}",
                f"**Unique Meters**: {total_meters:,}",
                f"**Total Engineered Features**: {len(feature_cols)}",
                f"**Duplicate (meter_id, timestamp) Pairs**: {dup_count}",
                f"**Infinite Value Anomalies**: {len(infinite_columns)}",
                "",
                "## Integrity Checks",
                f"- **Finite Values**: {'PASSED (0 infinite values)' if not infinite_columns else f'FAILED ({infinite_columns})'}",
                f"- **Timestamp Uniqueness**: {'PASSED (0 duplicates)' if dup_count == 0 else f'FAILED ({dup_count} duplicates)'}",
                f"- **Constant Features**: {len(constant_columns)} ({', '.join(constant_columns) if constant_columns else 'None'})",
                "",
                "## Feature Distributions & Null Rates",
                "",
                "| Feature | Dtype | Null % | Min | Max | Mean | Std |",
                "|---|---|---|---|---|---|---|",
            ]
            for col, stats in feature_stats.items():
                md_lines.append(
                    f"| `{col}` | {stats['dtype']} | {stats['null_pct']}% | "
                    f"{stats['min']} | {stats['max']} | {stats['mean']} | {stats['std']} |"
                )

            with open(m_path, "w", encoding="utf-8") as f:
                f.write("\n".join(md_lines) + "\n")

        return report
