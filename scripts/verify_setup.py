"""End-to-end environment and foundation verification script for Grid-Guard."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import polars as pl

from grid_guard.config.settings import DatasetColumnMapping, get_settings
from grid_guard.data.ingestion import DataIngestionEngine
from grid_guard.data.validation import DataValidator
from grid_guard.tracking.experiment import MLflowTracker
from grid_guard.utils.logging import setup_logger

logger = setup_logger("grid_guard_verify", level="INFO")


def run_verification() -> bool:
    """Run verification checks and return True if all succeed."""
    logger.info("Starting Grid-Guard Phase 1 verification...")
    all_passed = True

    # 1. Verify Configuration & Paths
    try:
        settings = get_settings()
        logger.info("Project Root: %s", settings.project_root)
        logger.info("Environment: %s", settings.environment)
        assert settings.project_root.exists(), "Project root does not exist"
        logger.info("[PASS] Configuration loaded successfully.")
    except Exception as exc:
        logger.error("[FAIL] Configuration verification failed: %s", exc)
        return False

    # 2. Verify Polars Ingestion with Synthetic Data
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        csv_file = tmp_path / "test_readings.csv"
        parquet_file = tmp_path / "test_readings.parquet"

        # Generate synthetic AMI records
        df = pl.DataFrame(
            {
                "meter_id": ["MTR_001", "MTR_002", "MTR_003", "MTR_004"],
                "timestamp": [
                    "2024-01-01 00:00:00",
                    "2024-01-01 01:00:00",
                    "2024-01-01 02:00:00",
                    "2024-01-01 03:00:00",
                ],
                "consumption_kwh": [2.5, 3.1, 0.8, 1.9],
                "is_tampered": [0, 0, 1, 0],
            }
        )

        df.write_csv(csv_file)
        df.write_parquet(parquet_file)

        engine = DataIngestionEngine(raw_data_dir=tmp_path)

        # Test Discovery
        discovered = engine.discover_raw_files(tmp_path)
        if len(discovered) != 2:
            logger.error("[FAIL] File discovery expected 2 files, got %d", len(discovered))
            all_passed = False
        else:
            logger.info("[PASS] File discovery found %d files.", len(discovered))

        # Test CSV Reading
        df_csv = engine.read_data(csv_file)
        if df_csv.height != 4 or df_csv.width != 4:
            logger.error("[FAIL] CSV read dimensions mismatch: %s", df_csv.shape)
            all_passed = False
        else:
            logger.info("[PASS] Polars CSV reading operational.")

        # Test Parquet Reading
        df_parquet = engine.read_data(parquet_file)
        if df_parquet.height != 4:
            logger.error("[FAIL] Parquet read dimensions mismatch")
            all_passed = False
        else:
            logger.info("[PASS] Polars Parquet reading operational.")

        # 3. Verify Data Validation Rules
        mapping = DatasetColumnMapping(
            meter_id="meter_id",
            timestamp="timestamp",
            consumption="consumption_kwh",
            label="is_tampered",
        )
        validator = DataValidator(allow_negative_consumption=False)
        report = validator.validate(df_csv, mapping=mapping, dataset_name="synthetic_test")

        if not report.is_valid:
            logger.error(
                "[FAIL] Data validation failed for clean synthetic dataset:\n%s", report.summary()
            )
            all_passed = False
        else:
            logger.info(
                "[PASS] Data validation engine operational. %d checks passed.", report.passed_checks
            )

        # 4. Verify Local MLflow Tracking
        try:
            tracker = MLflowTracker(
                experiment_name="grid-guard-smoke-test",
                tracking_uri=(tmp_path / "mlruns").as_uri(),
            )
            with tracker.start_run(run_name="smoke_test_run") as run:
                tracker.log_params({"batch_size": 32, "model_type": "baseline"})
                tracker.log_metrics({"val_accuracy": 0.985, "env_score": 12450.0})
                test_artifact = tmp_path / "sample_artifact.txt"
                test_artifact.write_text("Smoke test artifact content", encoding="utf-8")
                tracker.log_artifact(test_artifact)
                logger.info(
                    "[PASS] Local MLflow tracking operational (Run ID: %s).", run.info.run_id
                )
        except Exception as exc:
            logger.error("[FAIL] MLflow tracking failed: %s", exc)
            all_passed = False

    if all_passed:
        logger.info("=========================================")
        logger.info("ALL GRID-GUARD PHASE 1 CHECKS PASSED [OK]")
        logger.info("=========================================")
        return True
    else:
        logger.error("Grid-Guard Phase 1 verification failed.")
        return False


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
