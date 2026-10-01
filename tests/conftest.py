"""Pytest fixtures for Grid-Guard test suite."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

# Allow file store for local tests
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"

import polars as pl
import pytest


@pytest.fixture
def synthetic_long_df() -> pl.DataFrame:
    """Deterministic synthetic smart-meter dataset in canonical long format."""
    return pl.DataFrame(
        {
            "meter_id": ["MTR_001", "MTR_001", "MTR_002", "MTR_002", "MTR_003"],
            "timestamp": [
                "2024-01-01 00:00:00",
                "2024-01-01 01:00:00",
                "2024-01-01 00:00:00",
                "2024-01-01 01:00:00",
                "2024-01-01 00:00:00",
            ],
            "consumption_kwh": [1.45, 1.82, 0.95, 0.12, 3.40],
            "is_tampered": [0, 0, 1, 1, 0],
        }
    )


@pytest.fixture
def synthetic_wide_df() -> pl.DataFrame:
    """Deterministic synthetic smart-meter dataset in wide format (SGCC style)."""
    return pl.DataFrame(
        {
            "CONS_NO": ["CONS_1001", "CONS_1002", "CONS_1003"],
            "2014-08-01": [5.2, 0.0, 12.4],
            "2014-08-02": [6.1, 0.0, 11.8],
            "2014-08-03": [5.8, 0.1, 13.0],
            "FLAG": [0, 1, 0],
        }
    )


@pytest.fixture
def synthetic_csv_path(synthetic_long_df: pl.DataFrame, tmp_path: Path) -> Path:
    """Write synthetic long DataFrame to a temporary CSV file."""
    path = tmp_path / "readings.csv"
    synthetic_long_df.write_csv(path)
    return path


@pytest.fixture
def synthetic_wide_csv_path(synthetic_wide_df: pl.DataFrame, tmp_path: Path) -> Path:
    """Write synthetic wide DataFrame to a temporary CSV file."""
    path = tmp_path / "sgcc_readings.csv"
    synthetic_wide_df.write_csv(path)
    return path


@pytest.fixture
def synthetic_parquet_path(synthetic_long_df: pl.DataFrame, tmp_path: Path) -> Path:
    """Write synthetic long DataFrame to a temporary Parquet file."""
    path = tmp_path / "readings.parquet"
    synthetic_long_df.write_parquet(path)
    return path


@pytest.fixture
def temp_mlruns_uri(tmp_path: Path) -> Generator[str, None, None]:
    """Provide a temporary local tracking URI for MLflow."""
    tracking_dir = tmp_path / "mlruns"
    tracking_dir.mkdir(parents=True, exist_ok=True)
    yield tracking_dir.as_uri()
