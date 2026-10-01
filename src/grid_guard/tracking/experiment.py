"""Local experiment tracking utilities wrapping MLflow."""

from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import mlflow
from mlflow.entities import Run

from grid_guard.config.settings import get_settings
from grid_guard.utils.logging import get_logger

logger = get_logger(__name__)

# Suppress agent telemetry hints in local runs and permit local file store backends
os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"


class MLflowTracker:
    """Manager for local, reproducible MLflow experiment tracking without cloud dependencies."""

    def __init__(
        self,
        experiment_name: str | None = None,
        tracking_uri: str | None = None,
        artifact_location: str | None = None,
    ) -> None:
        """Initialize MLflow tracking.

        Args:
            experiment_name: Name of the experiment. Defaults to config settings.
            tracking_uri: Local URI (file:// or sqlite:///). Defaults to config settings.
            artifact_location: Optional custom directory for artifacts.
        """
        settings = get_settings()
        self.experiment_name = experiment_name or settings.tracking.experiment_name

        # Ensure local mlruns directory exists
        mlruns_dir = (settings.mlruns_dir or settings.project_root / "mlruns").resolve()
        mlruns_dir.mkdir(parents=True, exist_ok=True)

        # Standardize local file URI
        if tracking_uri is not None:
            self.tracking_uri = tracking_uri
        elif settings.tracking.tracking_uri:
            self.tracking_uri = settings.tracking.tracking_uri
        else:
            self.tracking_uri = mlruns_dir.as_uri()

        self.artifact_location = artifact_location
        self._initialize_tracking()

    def _initialize_tracking(self) -> None:
        """Configure MLflow client and experiment."""
        logger.info("Initializing MLflow local tracking at: %s", self.tracking_uri)
        mlflow.set_tracking_uri(self.tracking_uri)

        try:
            exp = mlflow.get_experiment_by_name(self.experiment_name)
            if exp is None:
                self.experiment_id = mlflow.create_experiment(
                    name=self.experiment_name,
                    artifact_location=self.artifact_location,
                )
                logger.info(
                    "Created experiment '%s' (ID: %s)", self.experiment_name, self.experiment_id
                )
            else:
                self.experiment_id = exp.experiment_id
                logger.info(
                    "Using existing experiment '%s' (ID: %s)",
                    self.experiment_name,
                    self.experiment_id,
                )
            mlflow.set_experiment(experiment_id=self.experiment_id)
        except Exception as exc:
            logger.warning(
                "Could not set up MLflow experiment by ID: %s. Falling back to name.", exc
            )
            mlflow.set_experiment(self.experiment_name)
            exp = mlflow.get_experiment_by_name(self.experiment_name)
            self.experiment_id = exp.experiment_id if exp else "0"

    @contextmanager
    def start_run(
        self,
        run_name: str | None = None,
        tags: dict[str, Any] | None = None,
        nested: bool = False,
    ) -> Generator[Run, None, None]:
        """Context manager to execute a tracked MLflow run.

        Args:
            run_name: Optional descriptive label for this run.
            tags: Key-value tags to attach.
            nested: Whether run is nested within another active run.

        Yields:
            mlflow.entities.Run object.
        """
        active_tags = tags or {}
        active_tags.setdefault("project", "grid-guard")
        active_tags.setdefault("phase", "phase_1")

        with mlflow.start_run(
            run_name=run_name,
            experiment_id=self.experiment_id,
            tags=active_tags,
            nested=nested,
        ) as run:
            logger.info(
                "Started MLflow run '%s' (ID: %s)", run_name or run.info.run_id, run.info.run_id
            )
            try:
                yield run
            finally:
                logger.info("Ended MLflow run (ID: %s)", run.info.run_id)

    def log_params(self, params: dict[str, Any]) -> None:
        """Log parameters to the currently active MLflow run."""
        mlflow.log_params(params)

    def log_metrics(self, metrics: dict[str, float], step: int | None = None) -> None:
        """Log scalar metrics to the active MLflow run."""
        mlflow.log_metrics(metrics, step=step)

    def log_artifact(self, local_path: Path | str, artifact_path: str | None = None) -> None:
        """Log a local file or directory as an artifact."""
        mlflow.log_artifact(str(local_path), artifact_path=artifact_path)

    def log_dict(self, dictionary: dict[str, Any], artifact_file: str) -> None:
        """Log a Python dictionary directly as a JSON artifact."""
        mlflow.log_dict(dictionary, artifact_file)


# Alias for backward/forward compatibility
ExperimentTracker = MLflowTracker
