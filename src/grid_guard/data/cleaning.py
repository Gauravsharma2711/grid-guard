"""Reproducible data cleaning and canonical time-series pipeline for Grid-Guard."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from grid_guard.config.settings import get_settings
from grid_guard.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ImputationSummary:
    """Summary of localized temporal imputation metrics."""

    max_gap_allowed: int
    missing_before: int
    values_imputed: int
    missing_after: int
    imputation_percentage: float
    meters_affected: int


@dataclass
class DataLineage:
    """Provenance and transformation lineage metadata."""

    source_name: str
    source_rows: int
    source_cols: int
    output_rows: int
    output_cols: int
    start_date: str
    end_date: str
    observed_days: int
    duplicates_removed: int
    imputation: ImputationSummary
    execution_timestamp: str = field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert lineage to serializable dictionary."""
        return asdict(self)

    def to_json(self, path: Path) -> None:
        """Export lineage to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info("Saved data lineage record to %s", path)


@dataclass
class CleaningResult:
    """Result of the data cleaning pipeline."""

    df_clean_wide: pl.DataFrame
    imputation_summary: ImputationSummary
    lineage: DataLineage
    canonical_date_columns: list[str]


class AMICleaningPipeline:
    """Production cleaning and standardization pipeline for AMI time-series datasets."""

    def __init__(
        self,
        max_impute_gap: int = 3,
        allow_negative_consumption: bool = False,
        meter_col: str = "CONS_NO",
        label_col: str = "FLAG",
    ) -> None:
        """Initialize pipeline with cleaning hyperparameters.

        Args:
            max_impute_gap: Maximum consecutive missing days to interpolate. Gaps larger
                than this threshold remain null.
            allow_negative_consumption: Whether to permit negative values or clip them to zero.
            meter_col: Source meter identifier column name.
            label_col: Source tampering label column name.
        """
        self.max_impute_gap = max_impute_gap
        self.allow_negative = allow_negative_consumption
        self.meter_col = meter_col
        self.label_col = label_col

    def clean(
        self,
        df: pl.DataFrame,
        source_name: str = "sgcc_electricity_theft",
    ) -> CleaningResult:
        """Execute the full end-to-end cleaning and standardization pipeline.

        Args:
            df: Ingested raw DataFrame (wide format).
            source_name: Name of the input dataset.

        Returns:
            CleaningResult containing cleaned wide DataFrame, lineage, and metrics.
        """
        logger.info(
            "Starting AMI cleaning pipeline for '%s' (input shape: %s)", source_name, df.shape
        )
        source_rows = df.height
        source_cols = df.width

        # 1. Deduplicate by meter identifier if duplicates exist (maintaining row order)
        initial_meters = df.height
        df_dedup = df.unique(subset=[self.meter_col], keep="first", maintain_order=True)
        duplicates_removed = initial_meters - df_dedup.height
        if duplicates_removed > 0:
            logger.warning("Removed %d duplicate meter records", duplicates_removed)

        # 2. Identify, parse, and chronologically sort date columns
        exclude_cols = {self.meter_col, self.label_col}
        raw_date_cols = [c for c in df_dedup.columns if c not in exclude_cols]

        date_tuples: list[tuple[str, datetime.date, str]] = []
        for c in raw_date_cols:
            for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
                try:
                    dt = datetime.strptime(c, fmt).date()
                    iso_str = dt.strftime("%Y-%m-%d")
                    date_tuples.append((c, dt, iso_str))
                    break
                except ValueError:
                    continue

        if not date_tuples:
            raise ValueError("No recognizable date columns found in dataset")

        # Sort chronologically
        date_tuples.sort(key=lambda x: x[1])
        sorted_raw_cols = [t[0] for t in date_tuples]
        canonical_date_cols = [t[2] for t in date_tuples]

        start_date = canonical_date_cols[0]
        end_date = canonical_date_cols[-1]
        observed_days = len(canonical_date_cols)

        logger.info(
            "Standardized %d date columns spanning %s to %s",
            observed_days,
            start_date,
            end_date,
        )

        # 3. Cast to numeric matrix (Float64)
        raw_numeric = df_dedup.select(
            [pl.col(c).cast(pl.Float64, strict=False) for c in sorted_raw_cols]
        )
        matrix = raw_numeric.to_numpy().astype(np.float64)

        # Handle negative consumption if configured
        if not self.allow_negative:
            neg_mask = (matrix < 0.0) & (~np.isnan(matrix))
            if np.any(neg_mask):
                logger.warning(
                    "Clipping %d negative consumption readings to 0.0", int(np.sum(neg_mask))
                )
                matrix[neg_mask] = 0.0

        missing_before = int(np.sum(np.isnan(matrix)))

        # 4. Perform Localized Bounded-Gap Temporal Interpolation
        logger.info(
            "Performing localized temporal interpolation (max_gap: %d days)...",
            self.max_impute_gap,
        )
        matrix_cleaned, imputed_mask = self._interpolate_bounded_gaps(
            matrix, max_gap=self.max_impute_gap
        )

        values_imputed = int(np.sum(imputed_mask))
        missing_after = int(np.sum(np.isnan(matrix_cleaned)))
        meters_affected = int(np.sum(np.any(imputed_mask, axis=1)))

        imputation_pct = round(values_imputed / max(missing_before, 1) * 100, 2)
        logger.info(
            "Imputation complete: %d values imputed (%.2f%% of missing) across %d meters",
            values_imputed,
            imputation_pct,
            meters_affected,
        )

        # 5. Compute Meter-Level Quality Metrics
        meter_missing_counts = np.sum(np.isnan(matrix_cleaned), axis=1)
        meter_imputed_counts = np.sum(imputed_mask, axis=1)
        meter_valid_counts = observed_days - meter_missing_counts

        coverage_ratio = np.round(meter_valid_counts / observed_days, 4)
        missing_ratio = np.round(meter_missing_counts / observed_days, 4)
        imputation_ratio = np.round(meter_imputed_counts / observed_days, 4)

        # Assign discrete quality status tiers
        quality_status: list[str] = []
        for mr in missing_ratio:
            if mr == 1.0:
                quality_status.append("EMPTY")
            elif mr > 0.50:
                quality_status.append("SPARSE")
            elif mr > 0.20:
                quality_status.append("PARTIAL")
            elif mr > 0.05:
                quality_status.append("GOOD")
            else:
                quality_status.append("EXCELLENT")

        # 6. Assemble Clean Wide Polars DataFrame
        clean_cols_dict: dict[str, Any] = {
            "meter_id": df_dedup[self.meter_col],
        }

        # Include ground truth label if present
        if self.label_col in df_dedup.columns:
            clean_cols_dict["tamper_label"] = df_dedup[self.label_col].cast(pl.Int8)

        # Add data quality indicators
        clean_cols_dict["data_quality_status"] = pl.Series(quality_status, dtype=pl.Utf8)
        clean_cols_dict["coverage_ratio"] = pl.Series(coverage_ratio, dtype=pl.Float32)
        clean_cols_dict["missing_ratio"] = pl.Series(missing_ratio, dtype=pl.Float32)
        clean_cols_dict["imputation_ratio"] = pl.Series(imputation_ratio, dtype=pl.Float32)

        # Add clean date columns
        for idx, col_name in enumerate(canonical_date_cols):
            clean_cols_dict[col_name] = pl.Series(matrix_cleaned[:, idx], dtype=pl.Float32)

        df_clean_wide = pl.DataFrame(clean_cols_dict)

        # 7. Build Summaries and Lineage
        imp_summary = ImputationSummary(
            max_gap_allowed=self.max_impute_gap,
            missing_before=missing_before,
            values_imputed=values_imputed,
            missing_after=missing_after,
            imputation_percentage=imputation_pct,
            meters_affected=meters_affected,
        )

        lineage = DataLineage(
            source_name=source_name,
            source_rows=source_rows,
            source_cols=source_cols,
            output_rows=df_clean_wide.height,
            output_cols=df_clean_wide.width,
            start_date=start_date,
            end_date=end_date,
            observed_days=observed_days,
            duplicates_removed=duplicates_removed,
            imputation=imp_summary,
        )

        return CleaningResult(
            df_clean_wide=df_clean_wide,
            imputation_summary=imp_summary,
            lineage=lineage,
            canonical_date_columns=canonical_date_cols,
        )

    def _interpolate_bounded_gaps(
        self, matrix: np.ndarray, max_gap: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """Interpolate short missing gaps bounded by valid values without altering long gaps.

        Args:
            matrix: 2D numpy array of shape (meters, days).
            max_gap: Maximum contiguous missing length to linearly interpolate.

        Returns:
            Tuple of (imputed_matrix, boolean_mask_of_imputed_cells).
        """
        out = matrix.copy()
        imputed_mask = np.zeros_like(matrix, dtype=bool)
        n_rows, n_cols = matrix.shape

        for r in range(n_rows):
            row = out[r]
            isnan = np.isnan(row)
            if not np.any(isnan):
                continue

            # Identify contiguous gap slices using diff on padded array
            padded = np.pad(isnan, (1, 1), mode="constant", constant_values=False).astype(np.int8)
            diff = np.diff(padded)
            starts = np.where(diff == 1)[0]
            ends = np.where(diff == -1)[0]

            for s, e in zip(starts, ends, strict=False):
                gap_len = e - s
                # Only interpolate if strictly bounded by valid readings and gap <= max_gap
                if s > 0 and e < n_cols and gap_len <= max_gap:
                    y0 = row[s - 1]
                    y1 = row[e]
                    step = (y1 - y0) / (gap_len + 1)
                    for k in range(gap_len):
                        row[s + k] = y0 + step * (k + 1)
                        imputed_mask[r, s + k] = True

        return out, imputed_mask

    def to_long_format(
        self,
        df_clean_wide: pl.DataFrame,
        canonical_date_cols: list[str],
    ) -> pl.DataFrame:
        """Reshape clean wide DataFrame into canonical normalized long time-series format.

        Args:
            df_clean_wide: DataFrame produced by `clean()`.
            canonical_date_cols: List of ISO date columns.

        Returns:
            polars.DataFrame in long format:
                [meter_id, timestamp, consumption_kwh, tamper_label, data_quality_status]
        """
        logger.info("Reshaping clean dataset to canonical long time-series...")
        index_cols = ["meter_id", "data_quality_status"]
        if "tamper_label" in df_clean_wide.columns:
            index_cols.append("tamper_label")

        # Unpivot dates to rows
        df_long = df_clean_wide.unpivot(
            index=index_cols,
            on=canonical_date_cols,
            variable_name="date_str",
            value_name="consumption_kwh",
        )

        # Convert date_str to Date dtype
        df_long = df_long.with_columns(
            pl.col("date_str").str.to_date("%Y-%m-%d").alias("timestamp")
        ).drop("date_str")

        # Reorder columns
        ordered_cols = ["meter_id", "timestamp", "consumption_kwh"]
        if "tamper_label" in df_long.columns:
            ordered_cols.append("tamper_label")
        ordered_cols.append("data_quality_status")

        df_long = df_long.select(ordered_cols)
        logger.info(
            "Long format reshaped successfully: %d rows x %d columns",
            df_long.height,
            df_long.width,
        )
        return df_long

    def export_canonical(
        self,
        result: CleaningResult,
        output_dir: Path | None = None,
        export_long: bool = True,
    ) -> tuple[Path, Path | None]:
        """Save canonical cleaned datasets to Parquet files.

        Args:
            result: CleaningResult instance.
            output_dir: Destination directory. Defaults to `data/processed/`.
            export_long: Whether to also generate and export long-format dataset.

        Returns:
            Tuple of (wide_parquet_path, long_parquet_path_or_None).
        """
        settings = get_settings()
        dest_dir = (
            output_dir.resolve()
            if output_dir is not None
            else (
                settings.processed_data_dir or settings.project_root / "data" / "processed"
            ).resolve()
        )
        dest_dir.mkdir(parents=True, exist_ok=True)

        wide_path = dest_dir / "canonical_ami_clean.parquet"
        logger.info("Writing clean wide Parquet to %s...", wide_path)
        result.df_clean_wide.write_parquet(wide_path, compression="zstd")

        long_path: Path | None = None
        if export_long:
            long_path = dest_dir / "canonical_ami_series.parquet"
            logger.info("Writing clean long Parquet to %s...", long_path)
            df_long = self.to_long_format(result.df_clean_wide, result.canonical_date_columns)
            df_long.write_parquet(long_path, compression="zstd")

        return wide_path, long_path
