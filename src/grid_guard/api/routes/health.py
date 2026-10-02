"""Health and readiness probe endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from grid_guard.api.schemas.common import HealthResponse, ReadyResponse
from grid_guard.config.settings import get_settings

router = APIRouter(tags=["System Health & Readiness"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Process Liveness Probe",
    description="Returns HTTP 200 to confirm that the FastAPI application process is alive and responding.",
)
async def health_check() -> HealthResponse:
    """Liveness probe confirming process vitality."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service="grid-guard-api",
        api_version=settings.api.version,
    )


@router.get(
    "/ready",
    response_model=ReadyResponse,
    summary="Service Readiness Probe",
    description="Verifies that the LightGBM champion booster and Tree-SHAP explainer are loaded in memory and ready to serve inference.",
    responses={
        200: {"description": "Service is fully initialized and operational"},
        503: {"description": "Service is unready (model or explainer missing)"},
    },
)
async def readiness_check(request: Request) -> ReadyResponse | JSONResponse:
    """Readiness probe verifying model checkpoint availability."""
    settings = get_settings()
    service = getattr(request.app.state, "inference_service", None)

    if service is None or not service.is_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unready",
                "model_loaded": False,
                "explainer_loaded": False,
                "features_configured": False,
                "model_version": "unknown",
                "feature_count": 0,
                "api_version": settings.api.version,
            },
        )

    meta = service.get_metadata()
    return ReadyResponse(
        status="ready",
        model_loaded=True,
        explainer_loaded=True,
        features_configured=True,
        model_version=meta.model_version,
        feature_count=meta.feature_count,
        api_version=settings.api.version,
    )
