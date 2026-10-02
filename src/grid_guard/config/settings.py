"""Configuration and settings management for Grid-Guard."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from grid_guard.config.financial import BaselineModelSettings, FinancialAssumptions
from grid_guard.config.imbalance import ImbalanceSettings


def find_project_root() -> Path:
    """Find the root directory of the project by searching for pyproject.toml."""
    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").is_file():
            return parent
    # Fallback to module-relative root: src/grid_guard/config -> root is 3 levels up
    return Path(__file__).resolve().parents[3]


class DatasetColumnMapping(BaseModel):
    """Mapping of conceptual AMI fields to actual dataset column names."""

    meter_id: str = "CONS_NO"
    timestamp: str | None = None  # None if wide-format daily columns
    consumption: str | None = None  # None if wide-format daily columns
    label: str = "FLAG"
    tariff: str | None = None
    customer_category: str | None = None
    feeder_id: str | None = None


class DatasetSettings(BaseModel):
    """Configuration for smart-meter dataset ingestion and validation."""

    name: str = "sgcc_electricity_theft"
    raw_filename: str = "electric-data.csv"
    format: str = "csv"  # csv or parquet
    layout: str = "wide"  # 'wide' (dates as columns) or 'long' (meter, timestamp, value)
    allow_negative_consumption: bool = False
    columns: DatasetColumnMapping = Field(default_factory=DatasetColumnMapping)


class TrackingSettings(BaseModel):
    """MLflow experiment tracking configuration."""

    experiment_name: str = "grid-guard-ntl-detection"
    tracking_uri: str | None = None  # Auto-configured to local sqlite/file if None
    artifact_location: str | None = None


class FeatureSettings(BaseModel):
    """Configuration for temporal feature extraction and tampering signatures."""

    lags: list[int] = Field(default_factory=lambda: [1, 2, 3, 7, 14, 30])
    rolling_windows: list[int] = Field(default_factory=lambda: [7, 14, 30, 60, 90])
    ratio_pairs: list[tuple[int, int]] = Field(
        default_factory=lambda: [(7, 30), (14, 60), (30, 90)]
    )
    step_down_recent_window: int = 14
    step_down_baseline_window: int = 60
    step_down_baseline_lag: int = 14
    zero_threshold: float = 0.001
    flatline_tolerance: float = 0.01
    min_history_days: int = 30
    epsilon: float = 1e-4
    batch_size_meters: int = 10000


class Settings(BaseSettings):
    """Global Grid-Guard application and pipeline settings."""

    model_config = SettingsConfigDict(
        env_prefix="GRID_GUARD_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = "grid-guard"
    environment: str = "development"
    random_seed: int = 42
    log_level: str = "INFO"

    # Directory paths
    project_root: Path = Field(default_factory=find_project_root)
    data_dir: Path | None = None
    raw_data_dir: Path | None = None
    interim_data_dir: Path | None = None
    processed_data_dir: Path | None = None
    external_data_dir: Path | None = None
    mlruns_dir: Path | None = None
    configs_dir: Path | None = None
    artifacts_dir: Path | None = None

    # Sub-configurations
    dataset: DatasetSettings = Field(default_factory=DatasetSettings)
    tracking: TrackingSettings = Field(default_factory=TrackingSettings)
    features: FeatureSettings = Field(default_factory=FeatureSettings)
    financial: FinancialAssumptions = Field(default_factory=FinancialAssumptions)
    baseline: BaselineModelSettings = Field(default_factory=BaselineModelSettings)
    imbalance: ImbalanceSettings = Field(default_factory=ImbalanceSettings)

    def model_post_init(self, __context: Any) -> None:
        """Resolve and initialize default directory paths relative to project root."""
        root = self.project_root.resolve()
        if self.data_dir is None:
            self.data_dir = root / "data"
        else:
            self.data_dir = (
                (root / self.data_dir).resolve()
                if not self.data_dir.is_absolute()
                else self.data_dir
            )

        if self.raw_data_dir is None:
            self.raw_data_dir = self.data_dir / "raw"
        if self.interim_data_dir is None:
            self.interim_data_dir = self.data_dir / "interim"
        if self.processed_data_dir is None:
            self.processed_data_dir = self.data_dir / "processed"
        if self.external_data_dir is None:
            self.external_data_dir = self.data_dir / "external"
        if self.mlruns_dir is None:
            self.mlruns_dir = root / "mlruns"
        if self.configs_dir is None:
            self.configs_dir = root / "configs"
        if self.artifacts_dir is None:
            self.artifacts_dir = root / "artifacts"

        # Resolve tracking URI if not explicitly set
        if self.tracking.tracking_uri is None:
            # Using SQLite database for MLflow local storage
            db_path = (self.mlruns_dir / "mlflow.db").resolve()
            self.tracking.tracking_uri = f"sqlite:///{db_path.as_posix()}"

    def ensure_directories(self) -> None:
        """Create standard data and tracking directories if they do not exist."""
        for path in [
            self.raw_data_dir,
            self.interim_data_dir,
            self.processed_data_dir,
            self.external_data_dir,
            self.mlruns_dir,
        ]:
            if path is not None:
                path.mkdir(parents=True, exist_ok=True)


def load_yaml_config(config_path: Path) -> dict[str, Any]:
    """Load configuration from a YAML file if it exists."""
    if not config_path.is_file():
        return {}
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


@lru_cache(maxsize=1)
def get_settings(config_file: str | None = None) -> Settings:
    """Retrieve cached application settings, optionally overlaying a YAML config.

    Args:
        config_file: Path to a YAML configuration file.

    Returns:
        Configured Settings instance.
    """
    root = find_project_root()
    yaml_data: dict[str, Any] = {}

    target_config = (
        Path(config_file).resolve()
        if config_file
        else Path(os.environ.get("GRID_GUARD_CONFIG_FILE", root / "configs" / "default.yaml"))
    )

    if target_config.is_file():
        yaml_data = load_yaml_config(target_config)

    return Settings(**yaml_data)
