"""High-performance dataset-agnostic ingestion engine using Polars."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import polars as pl

from grid_guard.config.settings import DatasetColumnMapping, get_settings
from grid_guard.utils.logging import get_logger

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {
    ".csv": "csv",
    ".tsv": "tsv",
    ".parquet": "parquet",
    ".pq": "parquet",
}


class DataIngestionError(Exception):
    """Raised when data discovery, reading, or schema mapping fails."""


@dataclass
class DatasetMetadata:
    """Metadata summary of an ingested or discovered dataset."""

    filepath: Path
    file_format: str
    file_size_bytes: int
    row_count: int | None
    column_count: int
    column_names: list[str]
    schema: dict[str, str] = field(default_factory=dict)


class DataIngestionEngine:
    """High-performance data ingestion engine powered by Polars."""

    def __init__(self, raw_data_dir: Path | None = None) -> None:
        """Initialize the ingestion engine with an optional raw data directory.

        Args:
            raw_data_dir: Directory containing raw data files. Defaults to configured path.
        """
        settings = get_settings()
        self.raw_data_dir = (
            raw_data_dir.resolve()
            if raw_data_dir is not None
            else (settings.raw_data_dir or settings.project_root / "data" / "raw").resolve()
        )

    def discover_raw_files(self, search_dir: Path | None = None) -> list[Path]:
        """Locate supported raw data files in the specified directory.

        Args:
            search_dir: Directory to search. Defaults to self.raw_data_dir.

        Returns:
            Sorted list of file paths found.
        """
        target_dir = search_dir.resolve() if search_dir is not None else self.raw_data_dir
        if not target_dir.is_dir():
            logger.warning("Target directory does not exist: %s", target_dir)
            return []

        found_files = [
            f
            for f in target_dir.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        found_files.sort(key=lambda p: p.name)
        logger.info("Discovered %d supported data file(s) in %s", len(found_files), target_dir)
        return found_files

    def identify_format(self, filepath: Path) -> str:
        """Determine file format based on extension.

        Args:
            filepath: Path to the target file.

        Returns:
            Format string ('csv', 'tsv', 'parquet').

        Raises:
            DataIngestionError: If file extension is unsupported or file missing.
        """
        if not filepath.exists():
            raise DataIngestionError(f"File not found: {filepath}")

        ext = filepath.suffix.lower()
        fmt = SUPPORTED_EXTENSIONS.get(ext)
        if fmt is None:
            raise DataIngestionError(
                f"Unsupported format '{ext}' for file {filepath}. "
                f"Supported extensions: {list(SUPPORTED_EXTENSIONS.keys())}"
            )
        return fmt

    def scan_data(self, filepath: Path) -> pl.LazyFrame:
        """Create a Polars LazyFrame for zero-copy streaming query planning.

        Args:
            filepath: Path to data file.

        Returns:
            polars.LazyFrame instance.
        """
        fmt = self.identify_format(filepath)
        logger.debug("Scanning %s as %s", filepath, fmt)

        if fmt == "csv":
            return pl.scan_csv(filepath, infer_schema_length=10000, ignore_errors=True)
        elif fmt == "tsv":
            return pl.scan_csv(
                filepath, separator="\t", infer_schema_length=10000, ignore_errors=True
            )
        elif fmt == "parquet":
            return pl.scan_parquet(filepath)
        else:
            raise DataIngestionError(f"Cannot scan unsupported format: {fmt}")

    def read_data(
        self,
        filepath: Path,
        n_rows: int | None = None,
        columns: list[str] | None = None,
    ) -> pl.DataFrame:
        """Eagerly load data into memory using Polars with high-performance C++ readers.

        Args:
            filepath: Path to data file.
            n_rows: Optional row limit for sampling or previewing.
            columns: Optional list of columns to project.

        Returns:
            polars.DataFrame containing loaded records.
        """
        fmt = self.identify_format(filepath)
        logger.info(
            "Reading %s (format: %s, n_rows: %s, columns: %s)",
            filepath.name,
            fmt,
            n_rows,
            len(columns) if columns else "all",
        )

        try:
            if fmt == "csv":
                df = pl.read_csv(
                    filepath,
                    n_rows=n_rows,
                    columns=columns,
                    infer_schema_length=10000,
                    ignore_errors=True,
                )
            elif fmt == "tsv":
                df = pl.read_csv(
                    filepath,
                    separator="\t",
                    n_rows=n_rows,
                    columns=columns,
                    infer_schema_length=10000,
                    ignore_errors=True,
                )
            elif fmt == "parquet":
                df = pl.read_parquet(filepath, n_rows=n_rows, columns=columns)
            else:
                raise DataIngestionError(f"Unsupported format: {fmt}")

            logger.info("Successfully read %d rows and %d columns", df.height, df.width)
            return df
        except Exception as exc:
            logger.error("Failed to read %s: %s", filepath, exc)
            raise DataIngestionError(f"Error reading {filepath}: {exc}") from exc

    def inspect_metadata(self, filepath: Path) -> DatasetMetadata:
        """Inspect file metadata and schema without loading entire dataset into RAM.

        Args:
            filepath: Path to data file.

        Returns:
            DatasetMetadata with dimensions, types, and schema.
        """
        fmt = self.identify_format(filepath)
        file_size = filepath.stat().st_size

        lazy = self.scan_data(filepath)
        schema_dict = {col: str(dtype) for col, dtype in lazy.collect_schema().items()}
        col_names = list(schema_dict.keys())

        # For Parquet, row count is instant from metadata; for CSV, collect length efficiently
        try:
            row_count: int | None = lazy.select(pl.len()).collect().item()
        except Exception as exc:
            logger.warning("Could not quickly determine row count for %s: %s", filepath, exc)
            row_count = None

        return DatasetMetadata(
            filepath=filepath,
            file_format=fmt,
            file_size_bytes=file_size,
            row_count=row_count,
            column_count=len(col_names),
            column_names=col_names,
            schema=schema_dict,
        )

    def detect_nulls(self, df: pl.DataFrame, subset: list[str] | None = None) -> dict[str, int]:
        """Compute the count of null values per column.

        Args:
            df: Target polars DataFrame.
            subset: Optional list of columns to check. Defaults to all.

        Returns:
            Dictionary mapping column name to null count.
        """
        cols = subset or df.columns
        null_counts: dict[str, int] = {}
        for col in cols:
            if col in df.columns:
                null_counts[col] = df[col].null_count()
        return null_counts

    def detect_duplicates(self, df: pl.DataFrame, subset: list[str]) -> int:
        """Calculate the number of duplicate records based on a logical uniqueness key.

        Args:
            df: Target polars DataFrame.
            subset: List of column names forming the primary key / uniqueness constraint.

        Returns:
            Number of duplicate rows.
        """
        missing_keys = [k for k in subset if k not in df.columns]
        if missing_keys:
            raise DataIngestionError(f"Uniqueness key columns not in DataFrame: {missing_keys}")

        is_dup = df.select(subset).is_duplicated()
        return int(is_dup.sum())

    def validate_column_mapping(
        self, df: pl.DataFrame, mapping: DatasetColumnMapping
    ) -> tuple[bool, list[str]]:
        """Validate if required conceptual columns are present in DataFrame.

        Args:
            df: Target polars DataFrame.
            mapping: Configured DatasetColumnMapping.

        Returns:
            Tuple of (is_valid, list_of_missing_columns).
        """
        missing: list[str] = []

        if mapping.meter_id and mapping.meter_id not in df.columns:
            missing.append(f"meter_id: '{mapping.meter_id}'")

        if mapping.label and mapping.label not in df.columns:
            missing.append(f"label: '{mapping.label}'")

        if mapping.timestamp and mapping.timestamp not in df.columns:
            missing.append(f"timestamp: '{mapping.timestamp}'")

        if mapping.consumption and mapping.consumption not in df.columns:
            missing.append(f"consumption: '{mapping.consumption}'")

        is_valid = len(missing) == 0
        if not is_valid:
            logger.warning("Missing required conceptual columns: %s", missing)
        return is_valid, missing
