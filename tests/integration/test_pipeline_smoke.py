"""Integration smoke test for end-to-end ingestion, validation, and tracking pipeline."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from grid_guard.config.settings import DatasetColumnMapping
from grid_guard.data.ingestion import DataIngestionEngine
from grid_guard.data.validation import DataValidator
from grid_guard.tracking.experiment import MLflowTracker


def test_end_to_end_pipeline_smoke(tmp_path: Path) -> None:
    """Verify end-to-end integration: discovery -> ingestion -> validation -> MLflow tracking."""
    # 1. Setup mock raw data directory
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True)
    raw_csv = raw_dir / "smart_meter_batch.csv"

    # Create realistic synthetic AMI batch
    meters = [f"MTR_{i:04d}" for i in range(1, 21)]
    timestamps = [f"2024-01-01 {hour:02d}:00:00" for hour in range(24)]
    data = []
    for m in meters:
        for t in timestamps:
            data.append(
                {
                    "meter_id": m,
                    "timestamp": t,
                    "consumption_kwh": 1.25 + (hash(m + t) % 50) / 10.0,
                    "tariff_group": "RESIDENTIAL",
                    "is_tampered": 1 if m in ("MTR_0003", "MTR_0017") else 0,
                }
            )

    df_synth = pl.DataFrame(data)
    df_synth.write_csv(raw_csv)

    # 2. Ingest via DataIngestionEngine
    engine = DataIngestionEngine(raw_data_dir=raw_dir)
    discovered = engine.discover_raw_files()
    assert len(discovered) == 1
    assert discovered[0].name == "smart_meter_batch.csv"

    df_ingested = engine.read_data(discovered[0])
    assert df_ingested.height == 480
    assert df_ingested.width == 5

    # 3. Validate via DataValidator
    mapping = DatasetColumnMapping(
        meter_id="meter_id",
        timestamp="timestamp",
        consumption="consumption_kwh",
        label="is_tampered",
        tariff="tariff_group",
    )
    validator = DataValidator(allow_negative_consumption=False)
    report = validator.validate(df_ingested, mapping=mapping, dataset_name="synthetic_batch")

    assert report.is_valid is True
    assert report.failed_checks == 0

    # 4. Log summary in local MLflow run
    tracking_uri = (tmp_path / "mlruns").as_uri()
    tracker = MLflowTracker(
        experiment_name="grid-guard-integration-tests",
        tracking_uri=tracking_uri,
    )

    with tracker.start_run(run_name="ingestion_validation_pipeline_run") as run:
        tracker.log_params(
            {
                "dataset_name": report.dataset_name,
                "raw_file": discovered[0].name,
                "num_rows": df_ingested.height,
                "num_columns": df_ingested.width,
            }
        )
        tracker.log_metrics(
            {
                "passed_checks": float(report.passed_checks),
                "failed_checks": float(report.failed_checks),
                "warning_checks": float(report.warning_checks),
                "duplicate_count": 0.0,
            }
        )

        summary_file = tmp_path / "validation_summary.txt"
        summary_file.write_text(report.summary(), encoding="utf-8")
        tracker.log_artifact(summary_file)

        assert run.info.run_id is not None
