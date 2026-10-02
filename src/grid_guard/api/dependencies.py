"""FastAPI dependency injection providers."""

from __future__ import annotations

from fastapi import HTTPException, Request, status

from grid_guard.api.services.inference import InferenceService
from grid_guard.config.settings import Settings, get_settings


def get_settings_dep() -> Settings:
    """Retrieve application configuration settings."""
    return get_settings()


def get_inference_service(request: Request) -> InferenceService:
    """Dependency provider returning initialized InferenceService from app state.

    Raises:
        HTTPException(503): If the inference service or model has not been initialized.
    """
    service: InferenceService | None = getattr(request.app.state, "inference_service", None)
    if service is None or not service.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inference service is not initialized or model checkpoint is unavailable.",
        )
    return service
