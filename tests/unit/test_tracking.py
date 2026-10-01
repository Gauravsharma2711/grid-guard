"""Unit tests for local MLflow tracking manager."""

from __future__ import annotations

from pathlib import Path

import mlflow

from grid_guard.tracking.experiment import MLflowTracker


def test_tracker_initialization(temp_mlruns_uri: str) -> None:
    """Verify MLflowTracker initializes cleanly with a local tracking URI."""
    tracker = MLflowTracker(
        experiment_name="unit-test-exp-init",
        tracking_uri=temp_mlruns_uri,
    )
    assert tracker.experiment_id is not None
    assert tracker.tracking_uri == temp_mlruns_uri


def test_tracker_run_logging(temp_mlruns_uri: str, tmp_path: Path) -> None:
    """Verify logging parameters, metrics, and artifacts to a local MLflow run."""
    tracker = MLflowTracker(
        experiment_name="unit-test-exp-logging",
        tracking_uri=temp_mlruns_uri,
    )

    with tracker.start_run(run_name="unit_run_1", tags={"env": "test"}) as run:
        run_id = run.info.run_id
        tracker.log_params({"learning_rate": 0.05, "max_depth": 6})
        tracker.log_metrics({"f1_score": 0.91, "expected_net_value": 8500.0})

        # Test local artifact file logging
        artifact_file = tmp_path / "model_spec.txt"
        artifact_file.write_text("LightGBM baseline v0.1", encoding="utf-8")
        tracker.log_artifact(artifact_file)

        # Test dict logging
        tracker.log_dict({"confusion_matrix": [[100, 5], [2, 45]]}, "metrics/cm.json")

    # Verify run recorded in MLflow client
    client = mlflow.tracking.MlflowClient(tracking_uri=temp_mlruns_uri)
    fetched_run = client.get_run(run_id)
    assert fetched_run.data.params["learning_rate"] == "0.05"
    assert fetched_run.data.metrics["f1_score"] == 0.91
    assert fetched_run.data.tags["env"] == "test"
    assert fetched_run.data.tags["project"] == "grid-guard"
