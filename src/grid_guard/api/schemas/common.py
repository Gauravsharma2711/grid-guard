"""Common reusable Pydantic schemas for the Grid-Guard API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized error response payload."""

    error_type: str = Field(
        ...,
        description="High-level error category (e.g. ValidationError, ModelNotReady, InvalidInput)",
    )
    message: str = Field(..., description="Human-readable explanation of the error")
    details: dict[str, Any] | list[Any] | None = Field(
        default=None, description="Detailed validation breakdown or contextual attributes"
    )
    request_id: str | None = Field(
        default=None, description="Correlation identifier for request tracing"
    )


class HealthResponse(BaseModel):
    """Liveness probe response."""

    status: str = Field(default="ok", description="Service process status")
    service: str = Field(default="grid-guard-api", description="Service identifier")
    api_version: str = Field(default="0.1.0", description="Semantic API version")


class ReadyResponse(BaseModel):
    """Readiness probe response indicating model and artifact initialization status."""

    status: str = Field(default="ready", description="'ready' or 'unready'")
    model_loaded: bool = Field(
        ..., description="Whether LightGBM champion booster is loaded in memory"
    )
    explainer_loaded: bool = Field(..., description="Whether Tree-SHAP explainer is initialized")
    features_configured: bool = Field(..., description="Whether feature pipeline is operational")
    model_version: str = Field(..., description="Loaded model checkpoint version")
    feature_count: int = Field(..., description="Number of expected features")
    api_version: str = Field(default="0.1.0", description="API version")


class ModelMetadataResponse(BaseModel):
    """Safe model metadata payload for introspection."""

    model_name: str = Field(default="cost_sensitive_champion_lgb", description="Model identifier")
    model_version: str = Field(
        default="phase6_cost_sensitive_v1", description="Model checkpoint version"
    )
    model_type: str = Field(default="LightGBM Booster", description="Underlying architecture")
    objective_type: str = Field(
        default="financially_weighted_logistic", description="Optimization objective"
    )
    feature_version: str = Field(
        default="phase3_temporal_features_v1", description="Feature schema version"
    )
    feature_count: int = Field(
        default=60, description="Total engineered features consumed by model"
    )
    base_log_odds: float = Field(..., description="Expected value E[z] in margin space")
    base_probability: float = Field(..., description="Prevalence probability sigmoid(E[z])")
    calibration_method: str = Field(
        default="isotonic_or_sigmoid", description="Probability calibration post-processing"
    )
    api_version: str = Field(default="0.1.0", description="API version")


class DataQualitySummary(BaseModel):
    """Summary of data completeness, coverage, and telemetry quality for a meter."""

    coverage_ratio: float = Field(
        ..., ge=0.0, le=1.0, description="Observed days / total calendar span"
    )
    missing_ratio: float = Field(..., ge=0.0, le=1.0, description="Missing reading fraction")
    imputation_ratio: float = Field(
        ..., ge=0.0, le=1.0, description="Synthetically filled fraction"
    )
    total_readings: int = Field(..., ge=1, description="Count of non-null daily readings supplied")
    history_days: int = Field(
        ..., ge=1, description="Calendar days between earliest and latest reading"
    )
    status: str = Field(..., description="'good', 'adequate', or 'insufficient_history'")
    warnings: list[str] = Field(
        default_factory=list, description="Quality or history deficiency warnings"
    )
