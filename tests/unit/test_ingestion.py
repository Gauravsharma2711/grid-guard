"""Unit tests for Polars data ingestion engine."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from grid_guard.config.settings import DatasetColumnMapping
from grid_guard.data.ingestion import (
    DataIngestionEngine,
    DataIngestionError,
)


def test_discover_raw_files(
    synthetic_csv_path: Path, synthetic_parquet_path: Path, tmp_path: Path
) -> None:
    """Verify discovery finds CSV and Parquet files while ignoring unsupported files."""
    # Write a dummy unsupported file
    (tmp_path / "notes.txt").write_text("dummy notes", encoding="utf-8")

    engine = DataIngestionEngine(raw_data_dir=tmp_path)
    discovered = engine.discover_raw_files()

    names = [p.name for p in discovered]
    assert "readings.csv" in names
    assert "readings.parquet" in names
    assert "notes.txt" not in names


def test_identify_format(synthetic_csv_path: Path, synthetic_parquet_path: Path) -> None:
    """Verify correct extension identification."""
    engine = DataIngestionEngine()
    assert engine.identify_format(synthetic_csv_path) == "csv"
    assert engine.identify_format(synthetic_parquet_path) == "parquet"


def test_identify_format_invalid(tmp_path: Path) -> None:
    """Verify DataIngestionError raised for missing or unsupported files."""
    engine = DataIngestionEngine()
    non_existent = tmp_path / "ghost.csv"
    with pytest.raises(DataIngestionError, match="File not found"):
        engine.identify_format(non_existent)

    unsupported = tmp_path / "image.png"
    unsupported.write_bytes(b"\x89PNG")
    with pytest.raises(DataIngestionError, match="Unsupported format"):
        engine.identify_format(unsupported)


def test_read_csv(synthetic_csv_path: Path) -> None:
    """Verify eager CSV reading with Polars."""
    engine = DataIngestionEngine()
    df = engine.read_data(synthetic_csv_path)
    assert isinstance(df, pl.DataFrame)
    assert df.height == 5
    assert df.width == 4
    assert "meter_id" in df.columns
    assert "consumption_kwh" in df.columns


def test_read_parquet(synthetic_parquet_path: Path) -> None:
    """Verify eager Parquet reading with Polars."""
    engine = DataIngestionEngine()
    df = engine.read_data(synthetic_parquet_path)
    assert isinstance(df, pl.DataFrame)
    assert df.height == 5
    assert df.width == 4


def test_read_data_with_limits(synthetic_csv_path: Path) -> None:
    """Verify projection and row limit parameters."""
    engine = DataIngestionEngine()
    df = engine.read_data(synthetic_csv_path, n_rows=2, columns=["meter_id", "consumption_kwh"])
    assert df.height == 2
    assert df.columns == ["meter_id", "consumption_kwh"]


def test_scan_data(synthetic_csv_path: Path) -> None:
    """Verify Polars lazy scan."""
    engine = DataIngestionEngine()
    lazy = engine.scan_data(synthetic_csv_path)
    assert isinstance(lazy, pl.LazyFrame)
    collected = lazy.select(pl.col("meter_id")).collect()
    assert collected.height == 5


def test_inspect_metadata(synthetic_csv_path: Path) -> None:
    """Verify metadata inspection without loading dataset."""
    engine = DataIngestionEngine()
    meta = engine.inspect_metadata(synthetic_csv_path)
    assert meta.file_format == "csv"
    assert meta.column_count == 4
    assert meta.row_count == 5
    assert "consumption_kwh" in meta.schema


def test_detect_nulls() -> None:
    """Verify column null detection."""
    df = pl.DataFrame(
        {
            "a": [1.0, None, 3.0],
            "b": ["x", "y", "z"],
            "c": [None, None, 3.0],
        }
    )
    engine = DataIngestionEngine()
    nulls = engine.detect_nulls(df)
    assert nulls["a"] == 1
    assert nulls["b"] == 0
    assert nulls["c"] == 2


def test_detect_duplicates() -> None:
    """Verify duplicate row counting based on uniqueness key."""
    df = pl.DataFrame(
        {
            "meter_id": ["M1", "M1", "M2"],
            "timestamp": ["2024-01-01", "2024-01-01", "2024-01-01"],
            "val": [10.0, 10.0, 5.0],
        }
    )
    engine = DataIngestionEngine()
    dups = engine.detect_duplicates(df, subset=["meter_id", "timestamp"])
    assert dups == 2  # Both rows with ('M1', '2024-01-01') are duplicated


def test_validate_column_mapping(synthetic_long_df: pl.DataFrame) -> None:
    """Verify column mapping validation flags missing fields."""
    engine = DataIngestionEngine()
    valid_mapping = DatasetColumnMapping(
        meter_id="meter_id",
        timestamp="timestamp",
        consumption="consumption_kwh",
        label="is_tampered",
    )
    is_valid, missing = engine.validate_column_mapping(synthetic_long_df, valid_mapping)
    assert is_valid is True
    assert missing == []

    invalid_mapping = DatasetColumnMapping(
        meter_id="missing_meter_col",
        timestamp="timestamp",
        consumption="missing_kwh_col",
        label="is_tampered",
    )
    is_valid, missing = engine.validate_column_mapping(synthetic_long_df, invalid_mapping)
    assert is_valid is False
    assert len(missing) == 2
