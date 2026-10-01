"""CLI script to safely inspect raw smart-meter datasets without modification."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from grid_guard.config.settings import get_settings
from grid_guard.data.ingestion import DataIngestionEngine
from grid_guard.data.validation import DataValidator
from grid_guard.utils.logging import setup_logger

logger = setup_logger("inspect_raw_data", level="INFO")


def main() -> None:
    """Inspect raw datasets located in data/raw/."""
    parser = argparse.ArgumentParser(description="Inspect raw smart-meter datasets.")
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to specific raw file. If omitted, discovers files in data/raw.",
    )
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=10,
        help="Number of rows to preview (default: 10).",
    )
    args = parser.parse_args()

    settings = get_settings()
    engine = DataIngestionEngine()

    if args.file:
        target_files = [Path(args.file).resolve()]
    else:
        target_files = engine.discover_raw_files()

    if not target_files:
        logger.warning(
            "No supported data files (.csv, .parquet) found in %s",
            settings.raw_data_dir,
        )
        sys.exit(0)

    for target in target_files:
        logger.info("=" * 60)
        logger.info("INSPECTING DATASET: %s", target.name)
        logger.info("=" * 60)

        metadata = engine.inspect_metadata(target)
        logger.info("File Size: %.2f MB", metadata.file_size_bytes / (1024 * 1024))
        logger.info("File Format: %s", metadata.file_format)
        logger.info("Columns: %d", metadata.column_count)
        if metadata.row_count is not None:
            logger.info("Estimated Row Count: %d", metadata.row_count)

        # Read sample rows
        df_sample = engine.read_data(target, n_rows=args.sample_rows)
        logger.info("Sample Schema (First 5 columns):")
        for col in df_sample.columns[:5]:
            logger.info("  - %s: %s", col, df_sample[col].dtype)

        if len(df_sample.columns) > 5:
            logger.info("  ... and %d more columns", len(df_sample.columns) - 5)
            logger.info("Sample Schema (Last 3 columns):")
            for col in df_sample.columns[-3:]:
                logger.info("  - %s: %s", col, df_sample[col].dtype)

        # Basic validation check on sample
        validator = DataValidator()
        report = validator.validate(df_sample, dataset_name=target.stem)
        logger.info("\n%s", report.summary())


if __name__ == "__main__":
    main()
