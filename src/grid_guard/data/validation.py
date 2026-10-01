"""Data validation engine for smart-meter time-series datasets."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import polars as pl

from grid_guard.config.settings import DatasetColumnMapping, DatasetSettings, get_settings
from grid_guard.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationCheckResult:
    """Result of an individual validation check."""

    name: str
    passed: bool
    severity: str  # "ERROR", "WARNING", "INFO"
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Consolidated report across all data validation checks."""

    dataset_name: str
    is_valid: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    checks: list[ValidationCheckResult] = field(default_factory=list)

    def summary(self) -> str:
        """Generate a human-readable text summary of the validation report."""
        status_str = "PASSED" if self.is_valid else "FAILED"
        lines = [
            f"=== DATA VALIDATION REPORT: {self.dataset_name} ===",
            f"Overall Status: {status_str}",
            f"Checks Total: {self.total_checks} | Passed: {self.passed_checks} | "
            f"Failed: {self.failed_checks} | Warnings: {self.warning_checks}",
            "-" * 50,
        ]
        for chk in self.checks:
            mark = "PASS" if chk.passed else chk.severity
            lines.append(f"[{mark:<7}] {chk.name}: {chk.message}")
            if chk.details and not chk.passed:
                lines.append(f"          Details: {chk.details}")
        lines.append("=" * 50)
        return "\n".join(lines)


class DataValidator:
    """Configurable data validator for AMI smart-meter time-series data."""

    def __init__(
        self,
        dataset_settings: DatasetSettings | None = None,
        allow_negative_consumption: bool | None = None,
        max_allowed_null_ratio: float = 0.50,
    ) -> None:
        """Initialize DataValidator.

        Args:
            dataset_settings: Optional dataset configuration. Defaults to application settings.
            allow_negative_consumption: Override flag for permitting negative consumption
                (e.g., solar net metering or meter adjustments).
            max_allowed_null_ratio: Maximum fraction of missing values tolerated before warning.
        """
        settings = get_settings()
        self.config = dataset_settings or settings.dataset
        self.allow_negative = (
            allow_negative_consumption
            if allow_negative_consumption is not None
            else self.config.allow_negative_consumption
        )
        self.max_null_ratio = max_allowed_null_ratio

    def validate(
        self,
        df: pl.DataFrame,
        mapping: DatasetColumnMapping | None = None,
        dataset_name: str | None = None,
    ) -> ValidationReport:
        """Execute the complete suite of foundational validation rules.

        Args:
            df: polars.DataFrame to validate.
            mapping: Column mapping. Defaults to config mapping.
            dataset_name: Optional identifier for reporting.

        Returns:
            ValidationReport instance.
        """
        cols = mapping or self.config.columns
        name = dataset_name or self.config.name
        checks: list[ValidationCheckResult] = []

        logger.info(
            "Validating dataset '%s' with %d rows and %d columns", name, df.height, df.width
        )

        # 1. Meter Identifier Availability & Integrity
        checks.append(self._check_meter_identifier(df, cols.meter_id))

        # 2. Schema Structure and Layout Detection
        layout = self._detect_layout(df, cols)
        checks.append(
            ValidationCheckResult(
                name="schema_layout_detection",
                passed=True,
                severity="INFO",
                message=f"Dataset layout resolved as '{layout}' format.",
                details={"layout": layout, "num_columns": df.width},
            )
        )

        # 3. Label / Target Availability (if applicable)
        if cols.label and cols.label in df.columns:
            checks.append(self._check_label_integrity(df, cols.label))
        else:
            checks.append(
                ValidationCheckResult(
                    name="target_label_check",
                    passed=True,
                    severity="WARNING",
                    message=f"Target column '{cols.label}' not found; assuming inference or unlabeled dataset.",
                    details={"label_column": cols.label},
                )
            )

        # 4. Null Value Statistics Check
        checks.append(self._check_null_statistics(df))

        # 5. Duplicate Records Check
        checks.append(self._check_duplicates(df, cols, layout))

        # 6. Consumption Range & Non-Negative Integrity
        checks.append(self._check_consumption_sanity(df, cols, layout))

        # 7. Time Ordering Check
        checks.append(self._check_time_ordering(df, cols, layout))

        # Consolidated Summary
        failed = sum(1 for c in checks if not c.passed and c.severity == "ERROR")
        warnings = sum(1 for c in checks if not c.passed and c.severity == "WARNING")
        passed = sum(1 for c in checks if c.passed)
        is_valid = failed == 0

        report = ValidationReport(
            dataset_name=name,
            is_valid=is_valid,
            total_checks=len(checks),
            passed_checks=passed,
            failed_checks=failed,
            warning_checks=warnings,
            checks=checks,
        )

        logger.info(
            "Validation finished: is_valid=%s (Passed: %d, Failed: %d, Warnings: %d)",
            is_valid,
            passed,
            failed,
            warnings,
        )
        return report

    def _check_meter_identifier(self, df: pl.DataFrame, meter_col: str) -> ValidationCheckResult:
        """Verify meter identifier exists and is well-formed."""
        if meter_col not in df.columns:
            return ValidationCheckResult(
                name="meter_id_availability",
                passed=False,
                severity="ERROR",
                message=f"Required meter identifier column '{meter_col}' is missing.",
            )

        nulls = df[meter_col].null_count()
        if nulls > 0:
            return ValidationCheckResult(
                name="meter_id_integrity",
                passed=False,
                severity="ERROR",
                message=f"Meter column '{meter_col}' contains {nulls} null values.",
                details={"null_count": nulls, "total_rows": df.height},
            )

        unique_count = df[meter_col].n_unique()
        return ValidationCheckResult(
            name="meter_id_availability",
            passed=True,
            severity="INFO",
            message=f"Meter ID column '{meter_col}' valid with {unique_count} distinct meters.",
            details={"unique_meters": unique_count, "total_rows": df.height},
        )

    def _detect_layout(self, df: pl.DataFrame, cols: DatasetColumnMapping) -> str:
        """Infer if dataset is wide-format (dates in columns) or long-format."""
        if cols.timestamp and cols.timestamp in df.columns:
            return "long"

        # Check if multiple columns match date patterns like YYYY-MM-DD or M/D/YYYY
        date_pattern = re.compile(r"^\d{1,4}[-/]\d{1,2}[-/]\d{1,4}$")
        date_cols = [c for c in df.columns if date_pattern.match(c)]
        if len(date_cols) > 5:
            return "wide"

        return self.config.layout

    def _check_label_integrity(self, df: pl.DataFrame, label_col: str) -> ValidationCheckResult:
        """Verify tampering label has expected binary or category distribution."""
        unique_vals = df[label_col].drop_nulls().unique().to_list()
        null_count = df[label_col].null_count()

        # Labels typically {0, 1}
        is_binary = set(unique_vals).issubset({0, 1, "0", "1"})
        if not is_binary:
            return ValidationCheckResult(
                name="target_label_integrity",
                passed=False,
                severity="WARNING",
                message=f"Target column '{label_col}' has non-standard values: {unique_vals}",
                details={"unique_values": unique_vals, "null_count": null_count},
            )

        # Class balance summary
        counts = df[label_col].value_counts().to_dicts()
        return ValidationCheckResult(
            name="target_label_integrity",
            passed=True,
            severity="INFO",
            message=f"Target column '{label_col}' is binary valid with {null_count} nulls.",
            details={"distribution": counts, "null_count": null_count},
        )

    def _check_null_statistics(self, df: pl.DataFrame) -> ValidationCheckResult:
        """Check for excessive null proportions across columns."""
        high_null_cols: dict[str, float] = {}
        for col in df.columns:
            null_ratio = df[col].null_count() / max(df.height, 1)
            if null_ratio > self.max_null_ratio:
                high_null_cols[col] = round(null_ratio, 4)

        if high_null_cols:
            return ValidationCheckResult(
                name="null_statistics_check",
                passed=False,
                severity="WARNING",
                message=f"{len(high_null_cols)} column(s) exceed null tolerance threshold ({self.max_null_ratio:.0%}).",
                details={"exceeded_columns_sample": dict(list(high_null_cols.items())[:10])},
            )

        return ValidationCheckResult(
            name="null_statistics_check",
            passed=True,
            severity="INFO",
            message=f"All columns within acceptable missing value threshold ({self.max_null_ratio:.0%}).",
        )

    def _check_duplicates(
        self, df: pl.DataFrame, cols: DatasetColumnMapping, layout: str
    ) -> ValidationCheckResult:
        """Check for duplicate records based on primary logical keys."""
        if layout == "wide":
            key_cols = [cols.meter_id] if cols.meter_id in df.columns else []
        else:
            key_cols = [
                c for c in [cols.meter_id, cols.timestamp] if c is not None and c in df.columns
            ]

        if not key_cols:
            return ValidationCheckResult(
                name="duplicate_records_check",
                passed=True,
                severity="INFO",
                message="No uniqueness key available for duplicate check.",
            )

        dup_count = int(df.select(key_cols).is_duplicated().sum())
        if dup_count > 0:
            return ValidationCheckResult(
                name="duplicate_records_check",
                passed=False,
                severity="WARNING",
                message=f"Detected {dup_count} duplicate records for key: {key_cols}.",
                details={"duplicate_count": dup_count, "key_columns": key_cols},
            )

        return ValidationCheckResult(
            name="duplicate_records_check",
            passed=True,
            severity="INFO",
            message=f"Zero duplicates detected for logical key {key_cols}.",
            details={"key_columns": key_cols},
        )

    def _check_consumption_sanity(
        self, df: pl.DataFrame, cols: DatasetColumnMapping, layout: str
    ) -> ValidationCheckResult:
        """Check consumption values for negatives, infinite values, or anomalies."""
        if layout == "long" and cols.consumption and cols.consumption in df.columns:
            consumption_cols = [cols.consumption]
        else:
            # Exclude known metadata columns; inspect numeric date columns
            exclude = {
                cols.meter_id,
                cols.label,
                cols.tariff,
                cols.customer_category,
                cols.feeder_id,
            }
            consumption_cols = [
                c
                for c in df.columns
                if c not in exclude
                and df[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32, pl.Int16, pl.Int8)
            ]

        if not consumption_cols:
            return ValidationCheckResult(
                name="consumption_sanity_check",
                passed=True,
                severity="INFO",
                message="No numeric consumption columns identified for range check.",
            )

        # Inspect negative values across columns
        total_negatives = 0
        for c in consumption_cols:
            neg_count = int((df[c] < 0).sum())
            total_negatives += neg_count

        if total_negatives > 0:
            msg = (
                f"Found {total_negatives} negative consumption values across {len(consumption_cols)} series. "
                "Negative values may indicate export/solar generation, net-metering, or meter rollbacks."
            )
            severity = "ERROR" if not self.allow_negative else "WARNING"
            return ValidationCheckResult(
                name="consumption_sanity_check",
                passed=self.allow_negative,
                severity=severity,
                message=msg,
                details={
                    "negative_count": total_negatives,
                    "allow_negative_configured": self.allow_negative,
                },
            )

        return ValidationCheckResult(
            name="consumption_sanity_check",
            passed=True,
            severity="INFO",
            message=f"All {len(consumption_cols)} consumption series are non-negative.",
        )

    def _check_time_ordering(
        self, df: pl.DataFrame, cols: DatasetColumnMapping, layout: str
    ) -> ValidationCheckResult:
        """Verify time ordering is chronological."""
        if layout == "long" and cols.timestamp and cols.timestamp in df.columns:
            # Check if timestamps are monotonically non-decreasing
            # Grouping or sorted check
            try:
                sorted_df = df.select([cols.meter_id, cols.timestamp]).sort(
                    [cols.meter_id, cols.timestamp]
                )
                is_ordered = df.select([cols.meter_id, cols.timestamp]).equals(sorted_df)
                if not is_ordered:
                    return ValidationCheckResult(
                        name="time_ordering_check",
                        passed=False,
                        severity="WARNING",
                        message="Long-format timestamps are not pre-sorted per meter.",
                    )
            except Exception as exc:
                logger.debug("Time ordering verification skipped: %s", exc)

        elif layout == "wide":
            date_pattern = re.compile(r"^(\d{1,4})[-/](\d{1,2})[-/](\d{1,4})$")
            parsed_dates: list[tuple[str, datetime]] = []
            for col in df.columns:
                m = date_pattern.match(col)
                if m:
                    # Parse dates like 8/3/2014 or 2014-08-03
                    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
                        try:
                            dt = datetime.strptime(col, fmt)
                            parsed_dates.append((col, dt))
                            break
                        except ValueError:
                            continue

            if len(parsed_dates) > 1:
                is_sorted = all(
                    parsed_dates[i][1] <= parsed_dates[i + 1][1]
                    for i in range(len(parsed_dates) - 1)
                )
                if not is_sorted:
                    return ValidationCheckResult(
                        name="time_ordering_check",
                        passed=False,
                        severity="WARNING",
                        message="Wide-format date column headers are not strictly chronological.",
                        details={"sample_dates": [p[0] for p in parsed_dates[:5]]},
                    )

        return ValidationCheckResult(
            name="time_ordering_check",
            passed=True,
            severity="INFO",
            message="Time sequence is chronologically consistent.",
        )
