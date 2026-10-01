"""Unit tests for dataset validation engine."""

from __future__ import annotations

import polars as pl

from grid_guard.config.settings import DatasetColumnMapping
from grid_guard.data.validation import DataValidator


def test_validation_passes_on_clean_long_data(synthetic_long_df: pl.DataFrame) -> None:
    """Verify clean dataset passes all checks."""
    mapping = DatasetColumnMapping(
        meter_id="meter_id",
        timestamp="timestamp",
        consumption="consumption_kwh",
        label="is_tampered",
    )
    validator = DataValidator(allow_negative_consumption=False)
    report = validator.validate(synthetic_long_df, mapping=mapping)

    assert report.is_valid is True
    assert report.failed_checks == 0
    assert "Overall Status: PASSED" in report.summary()


def test_validation_fails_on_missing_meter_id(synthetic_long_df: pl.DataFrame) -> None:
    """Verify validation fails when meter_id column is absent."""
    df_missing_meter = synthetic_long_df.drop("meter_id")
    mapping = DatasetColumnMapping(
        meter_id="meter_id",
        timestamp="timestamp",
        consumption="consumption_kwh",
        label="is_tampered",
    )
    validator = DataValidator()
    report = validator.validate(df_missing_meter, mapping=mapping)

    assert report.is_valid is False
    assert report.failed_checks > 0
    checks_by_name = {c.name: c for c in report.checks}
    assert checks_by_name["meter_id_availability"].passed is False


def test_validation_fails_on_null_meter_id() -> None:
    """Verify validation fails when meter_id contains nulls."""
    df = pl.DataFrame(
        {
            "meter_id": ["M1", None, "M3"],
            "timestamp": ["2024-01-01", "2024-01-01", "2024-01-01"],
            "consumption": [1.0, 2.0, 3.0],
            "FLAG": [0, 0, 1],
        }
    )
    mapping = DatasetColumnMapping(
        meter_id="meter_id", timestamp="timestamp", consumption="consumption", label="FLAG"
    )
    validator = DataValidator()
    report = validator.validate(df, mapping=mapping)

    assert report.is_valid is False
    checks_by_name = {c.name: c for c in report.checks}
    assert checks_by_name["meter_id_integrity"].passed is False


def test_validation_negative_consumption_handling() -> None:
    """Verify negative consumption triggers error by default, but warning if allowed."""
    df_with_negatives = pl.DataFrame(
        {
            "meter_id": ["M1", "M2"],
            "timestamp": ["2024-01-01", "2024-01-01"],
            "consumption_kwh": [5.0, -1.2],
            "FLAG": [0, 1],
        }
    )
    mapping = DatasetColumnMapping(
        meter_id="meter_id",
        timestamp="timestamp",
        consumption="consumption_kwh",
        label="FLAG",
    )

    # 1. Negative disallowed (default) -> should fail
    validator_strict = DataValidator(allow_negative_consumption=False)
    report_strict = validator_strict.validate(df_with_negatives, mapping=mapping)
    assert report_strict.is_valid is False
    checks_strict = {c.name: c for c in report_strict.checks}
    assert checks_strict["consumption_sanity_check"].passed is False
    assert checks_strict["consumption_sanity_check"].severity == "ERROR"

    # 2. Negative allowed (e.g. solar net metering) -> should pass with warning
    validator_lenient = DataValidator(allow_negative_consumption=True)
    report_lenient = validator_lenient.validate(df_with_negatives, mapping=mapping)
    assert report_lenient.is_valid is True
    checks_lenient = {c.name: c for c in report_lenient.checks}
    assert checks_lenient["consumption_sanity_check"].severity == "WARNING"


def test_validation_wide_sgcc_format(synthetic_wide_df: pl.DataFrame) -> None:
    """Verify validation operates on wide-format SGCC benchmark data."""
    mapping = DatasetColumnMapping(
        meter_id="CONS_NO",
        label="FLAG",
    )
    validator = DataValidator()
    report = validator.validate(synthetic_wide_df, mapping=mapping)

    assert report.is_valid is True
    checks_by_name = {c.name: c for c in report.checks}
    assert checks_by_name["schema_layout_detection"].details["layout"] == "wide"
    assert checks_by_name["meter_id_availability"].passed is True
    assert checks_by_name["target_label_integrity"].passed is True


def test_validation_detects_excessive_nulls() -> None:
    """Verify validation warns when missing values exceed tolerance ratio."""
    df = pl.DataFrame(
        {
            "meter_id": ["M1", "M2", "M3", "M4"],
            "col_many_nulls": [1.0, None, None, None],  # 75% null
        }
    )
    validator = DataValidator(max_allowed_null_ratio=0.50)
    report = validator.validate(df)
    checks_by_name = {c.name: c for c in report.checks}
    assert checks_by_name["null_statistics_check"].passed is False
    assert checks_by_name["null_statistics_check"].severity == "WARNING"
