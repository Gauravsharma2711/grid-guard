"""Configuration settings for Grid-Guard FastAPI inference service."""

from __future__ import annotations

from pydantic import BaseModel, Field


class APISettings(BaseModel):
    """Settings for the FastAPI REST API server."""

    title: str = "Grid-Guard NTL Detection API"
    version: str = "0.1.0"
    description: str = (
        "Production-grade REST API for smart-meter non-technical loss (NTL) detection, "
        "cost-sensitive economic decisioning, and SHAP explainability."
    )
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    workers: int = 1
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])

    # Model & Feature Artifact Paths
    model_path: str = "artifacts/cost_sensitive/champion_model.txt"

    # Input Limits & Thresholds
    min_readings_per_meter: int = 14
    max_readings_per_meter: int = 730
    recommended_readings_per_meter: int = 90
    max_batch_size: int = 50

    # Default Business / Financial Parameters
    default_tariff: float = 6.0
    default_dispatch_cost: float = 500.0
    currency: str = "INR"

    # Performance & Behavior Flags
    include_explanation_default: bool = True
