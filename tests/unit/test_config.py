"""Unit tests for configuration and settings management."""

from __future__ import annotations

from pathlib import Path

from grid_guard.config.settings import Settings, find_project_root, get_settings


def test_find_project_root() -> None:
    """Verify that find_project_root correctly locates the directory with pyproject.toml."""
    root = find_project_root()
    assert (root / "pyproject.toml").is_file()
    assert (root / "src" / "grid_guard").is_dir()


def test_settings_default_initialization() -> None:
    """Verify default Settings instance attributes and path resolution."""
    settings = Settings()
    assert settings.project_name == "grid-guard"
    assert settings.environment == "development"
    assert settings.random_seed == 42
    assert settings.data_dir == settings.project_root / "data"
    assert settings.raw_data_dir == settings.project_root / "data" / "raw"
    assert settings.interim_data_dir == settings.project_root / "data" / "interim"
    assert settings.processed_data_dir == settings.project_root / "data" / "processed"
    assert settings.external_data_dir == settings.project_root / "data" / "external"
    assert settings.mlruns_dir == settings.project_root / "mlruns"
    assert settings.tracking.experiment_name == "grid-guard-ntl-detection"


def test_get_settings_caching() -> None:
    """Verify get_settings returns a valid singleton instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_ensure_directories(tmp_path: Path) -> None:
    """Verify ensure_directories creates missing folders without errors."""
    sub_data = tmp_path / "custom_data"
    settings = Settings(
        project_root=tmp_path,
        data_dir=sub_data,
        raw_data_dir=sub_data / "raw",
        interim_data_dir=sub_data / "interim",
        processed_data_dir=sub_data / "processed",
        external_data_dir=sub_data / "external",
        mlruns_dir=tmp_path / "custom_mlruns",
    )
    settings.ensure_directories()
    assert (sub_data / "raw").is_dir()
    assert (sub_data / "interim").is_dir()
    assert (sub_data / "processed").is_dir()
    assert (sub_data / "external").is_dir()
    assert (tmp_path / "custom_mlruns").is_dir()
