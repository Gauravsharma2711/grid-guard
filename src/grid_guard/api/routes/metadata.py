"""Model and public configuration metadata introspection endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from grid_guard.api.dependencies import get_inference_service, get_settings_dep
from grid_guard.api.schemas.common import ModelMetadataResponse
from grid_guard.api.services.inference import InferenceService
from grid_guard.config.settings import Settings

router = APIRouter(prefix="/api/v1/metadata", tags=["Metadata & Introspection"])


@router.get(
    "/model",
    response_model=ModelMetadataResponse,
    summary="Model Checkpoint Introspection",
    description="Returns verified metadata for the currently loaded LightGBM model, feature schema, base expected values, and objective type.",
)
async def get_model_metadata(
    service: InferenceService = Depends(get_inference_service),
) -> ModelMetadataResponse:
    """Introspect loaded model characteristics."""
    return service.get_metadata()


@router.get(
    "/config",
    summary="Public Configuration Introspection",
    description="Returns safe, non-sensitive operational configuration limits, supported decision policies, and input constraints.",
)
async def get_public_config(
    settings: Settings = Depends(get_settings_dep),
) -> dict[str, Any]:
    """Expose safe public operational limits and capabilities."""
    return {
        "api_version": settings.api.version,
        "input_cadence": "daily",
        "limits": {
            "min_readings_per_meter": settings.api.min_readings_per_meter,
            "max_readings_per_meter": settings.api.max_readings_per_meter,
            "recommended_readings_per_meter": settings.api.recommended_readings_per_meter,
            "max_batch_size": settings.api.max_batch_size,
        },
        "financial_defaults": {
            "default_tariff": settings.api.default_tariff,
            "default_dispatch_cost": settings.api.default_dispatch_cost,
            "currency": settings.api.currency,
            "recovery_factor": settings.decision.recovery_factor,
            "undetected_cycles": settings.financial.undetected_cycles,
        },
        "supported_decision_rules": ["env", "cost_threshold", "fixed_threshold"],
        "default_decision_rule": settings.decision.decision_rule.value,
        "feature_categories": [
            "recent_consumption",
            "historical_baseline",
            "temporal_behavior",
            "variability",
            "peak_behavior",
            "zero_flatline_behavior",
            "sustained_step_down",
            "data_quality",
        ],
    }
