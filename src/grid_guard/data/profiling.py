"""Automated dataset and meter-level profiling for AMI time-series data."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from grid_guard.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GapAnalysis:
    """Distribution of contiguous missing observation streaks."""

    total_gaps: int = 0
    gaps_1_day: int = 0
    gaps_2_to_3_days: int = 0
    gaps_4_to_7_days: int = 0
    gaps_8_to_30_days: int = 0
    gaps_over_30_days: int = 0
    median_gap_days: float = 0.0
    max_gap_days: int = 0


@dataclass
class QualityTierCounts:
    """Breakdown of meter coverage quality tiers."""

    excellent_le_5pct: int = 0
    good_5_to_20pct: int = 0
    partial_20_to_50pct: int = 0
    sparse_50_to_99pct: int = 0
    empty_100pct: int = 0


@dataclass
class ConsumptionStats:
    """Global consumption distribution statistics."""

    min_kwh: float = 0.0
    mean_kwh: float = 0.0
    std_kwh: float = 0.0
    median_kwh: float = 0.0
    p25_kwh: float = 0.0
    p75_kwh: float = 0.0
    p95_kwh: float = 0.0
    p99_kwh: float = 0.0
    max_kwh: float = 0.0


@dataclass
class DatasetProfile:
    """Comprehensive statistical profile of an AMI smart-meter dataset."""

    dataset_name: str
    file_size_bytes: int
    total_meters: int
    total_columns: int
    sampling_frequency: str
    start_date: str
    end_date: str
    expected_days: int
    observed_days: int
    missing_calendar_dates: list[str] = field(default_factory=list)
    total_cells: int = 0
    total_nulls: int = 0
    null_ratio: float = 0.0
    total_zeros: int = 0
    zero_ratio: float = 0.0
    total_negatives: int = 0
    tampering_label_available: bool = False
    label_distribution: dict[str, int] = field(default_factory=dict)
    tampering_ratio: float = 0.0
    consumption: ConsumptionStats = field(default_factory=ConsumptionStats)
    quality_tiers: QualityTierCounts = field(default_factory=QualityTierCounts)
    gaps: GapAnalysis = field(default_factory=GapAnalysis)

    def to_dict(self) -> dict[str, Any]:
        """Convert profile to serializable dictionary."""
        return asdict(self)

    def to_json(self, path: Path) -> None:
        """Export profile to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info("Saved dataset profile to %s", path)


class AMIProfiler:
    """Statistical profiling engine for AMI time-series datasets."""

    def __init__(self, meter_col: str = "CONS_NO", label_col: str = "FLAG") -> None:
        """Initialize profiler.

        Args:
            meter_col: Name of meter identifier column.
            label_col: Name of tampering/theft label column.
        """
        self.meter_col = meter_col
        self.label_col = label_col

    def profile_dataset(
        self,
        df: pl.DataFrame,
        dataset_name: str = "sgcc_electricity_theft",
        file_size_bytes: int = 0,
        sample_gap_meters: int = 5000,
    ) -> DatasetProfile:
        """Generate full statistical profile of the AMI dataset.

        Args:
            df: Ingested Polars DataFrame (wide format).
            dataset_name: Identifier name for the dataset.
            file_size_bytes: Physical size of source file in bytes.
            sample_gap_meters: Number of meters to sample for detailed gap streak analysis.

        Returns:
            DatasetProfile instance with full metrics.
        """
        logger.info("Generating statistical profile for '%s'...", dataset_name)
        total_meters = df.height
        total_cols = df.width

        # Identify date columns
        exclude_cols = {self.meter_col, self.label_col}
        date_cols = [c for c in df.columns if c not in exclude_cols]
        observed_days = len(date_cols)

        # 1. Parse and verify calendar sequence
        date_tuples = []
        for c in date_cols:
            for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
                try:
                    dt = datetime.strptime(c, fmt).date()
                    date_tuples.append((c, dt))
                    break
                except ValueError:
                    continue

        if date_tuples:
            date_tuples.sort(key=lambda x: x[1])
            start_date_obj = date_tuples[0][1]
            end_date_obj = date_tuples[-1][1]
            start_date_str = str(start_date_obj)
            end_date_str = str(end_date_obj)

            # Generate full expected calendar
            expected_calendar: set[datetime.date] = set()
            curr = start_date_obj
            while curr <= end_date_obj:
                expected_calendar.add(curr)
                curr += timedelta(days=1)

            expected_days = len(expected_calendar)
            observed_calendar = {dt for _, dt in date_tuples}
            missing_dates = sorted([str(d) for d in (expected_calendar - observed_calendar)])
        else:
            start_date_str = "unknown"
            end_date_str = "unknown"
            expected_days = observed_days
            missing_dates = []

        # 2. Inspect label distribution if available
        has_label = self.label_col in df.columns
        label_dist: dict[str, int] = {}
        tampering_ratio = 0.0

        if has_label:
            counts = df[self.label_col].value_counts().to_dicts()
            for r in counts:
                label_dist[str(r[self.label_col])] = r["count"]
            theft_count = label_dist.get("1", 0)
            tampering_ratio = round(theft_count / max(total_meters, 1), 4)

        # 3. Cast numeric date matrix to compute global missingness, zeros, and stats
        logger.info("Computing global null and zero statistics...")
        total_cells = total_meters * observed_days

        # Extract numeric array
        numeric_df = df.select([pl.col(c).cast(pl.Float64, strict=False) for c in date_cols])
        matrix = numeric_df.to_numpy()  # shape (total_meters, observed_days)

        is_nan = np.isnan(matrix)
        total_nulls = int(np.sum(is_nan))
        null_ratio = round(total_nulls / max(total_cells, 1), 4)

        is_zero = (matrix == 0.0) & (~is_nan)
        total_zeros = int(np.sum(is_zero))
        zero_ratio = round(total_zeros / max(total_cells, 1), 4)

        is_neg = (matrix < 0.0) & (~is_nan)
        total_negs = int(np.sum(is_neg))

        # 4. Consumption distribution metrics (computed over valid non-null readings)
        valid_vals = matrix[~is_nan]
        if len(valid_vals) > 0:
            # Deterministic quantile sampling if array is huge
            if len(valid_vals) > 2_000_000:
                np.random.seed(42)
                sample_vals = np.random.choice(valid_vals, size=2_000_000, replace=False)
            else:
                sample_vals = valid_vals

            consumption = ConsumptionStats(
                min_kwh=round(float(np.min(valid_vals)), 4),
                mean_kwh=round(float(np.mean(sample_vals)), 4),
                std_kwh=round(float(np.std(sample_vals)), 4),
                median_kwh=round(float(np.median(sample_vals)), 4),
                p25_kwh=round(float(np.percentile(sample_vals, 25)), 4),
                p75_kwh=round(float(np.percentile(sample_vals, 75)), 4),
                p95_kwh=round(float(np.percentile(sample_vals, 95)), 4),
                p99_kwh=round(float(np.percentile(sample_vals, 99)), 4),
                max_kwh=round(float(np.max(valid_vals)), 4),
            )
        else:
            consumption = ConsumptionStats()

        # 5. Meter-level quality tiers
        logger.info("Computing meter quality tiers...")
        meter_null_counts = np.sum(is_nan, axis=1)
        meter_null_ratios = meter_null_counts / max(observed_days, 1)

        quality_tiers = QualityTierCounts(
            excellent_le_5pct=int(np.sum(meter_null_ratios <= 0.05)),
            good_5_to_20pct=int(np.sum((meter_null_ratios > 0.05) & (meter_null_ratios <= 0.20))),
            partial_20_to_50pct=int(
                np.sum((meter_null_ratios > 0.20) & (meter_null_ratios <= 0.50))
            ),
            sparse_50_to_99pct=int(np.sum((meter_null_ratios > 0.50) & (meter_null_ratios < 1.00))),
            empty_100pct=int(np.sum(meter_null_ratios == 1.00)),
        )

        # 6. Detailed missing streak / gap analysis
        logger.info("Analyzing consecutive missing day streak lengths...")
        n_sample = min(sample_gap_meters, total_meters)
        sample_nan_mask = is_nan[:n_sample]

        gap_lengths: list[int] = []
        for row in sample_nan_mask:
            streak = 0
            for val in row:
                if val:
                    streak += 1
                else:
                    if streak > 0:
                        gap_lengths.append(streak)
                        streak = 0
            if streak > 0:
                gap_lengths.append(streak)

        if gap_lengths:
            gaps_arr = np.array(gap_lengths)
            gaps = GapAnalysis(
                total_gaps=len(gaps_arr),
                gaps_1_day=int(np.sum(gaps_arr == 1)),
                gaps_2_to_3_days=int(np.sum((gaps_arr >= 2) & (gaps_arr <= 3))),
                gaps_4_to_7_days=int(np.sum((gaps_arr >= 4) & (gaps_arr <= 7))),
                gaps_8_to_30_days=int(np.sum((gaps_arr >= 8) & (gaps_arr <= 30))),
                gaps_over_30_days=int(np.sum(gaps_arr > 30)),
                median_gap_days=round(float(np.median(gaps_arr)), 1),
                max_gap_days=int(np.max(gaps_arr)),
            )
        else:
            gaps = GapAnalysis()

        profile = DatasetProfile(
            dataset_name=dataset_name,
            file_size_bytes=file_size_bytes,
            total_meters=total_meters,
            total_columns=total_cols,
            sampling_frequency="daily",
            start_date=start_date_str,
            end_date=end_date_str,
            expected_days=expected_days,
            observed_days=observed_days,
            missing_calendar_dates=missing_dates,
            total_cells=total_cells,
            total_nulls=total_nulls,
            null_ratio=null_ratio,
            total_zeros=total_zeros,
            zero_ratio=zero_ratio,
            total_negatives=total_negs,
            tampering_label_available=has_label,
            label_distribution=label_dist,
            tampering_ratio=tampering_ratio,
            consumption=consumption,
            quality_tiers=quality_tiers,
            gaps=gaps,
        )

        logger.info(
            "Profile complete: %d meters, %d dates (%s to %s), null ratio: %.2f%%, theft ratio: %.2f%%",
            profile.total_meters,
            profile.observed_days,
            profile.start_date,
            profile.end_date,
            profile.null_ratio * 100,
            profile.tampering_ratio * 100,
        )
        return profile
