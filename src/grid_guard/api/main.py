"""FastAPI application entrypoint for Grid-Guard NTL detection service."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from grid_guard.api.middleware import (
    register_exception_handlers,
    request_id_and_logging_middleware,
)
from grid_guard.api.routes import (
    health_router,
    inspection_router,
    metadata_router,
    prediction_router,
)
from grid_guard.api.services.inference import InferenceService
from grid_guard.config.settings import Settings, get_settings

logger = logging.getLogger("grid_guard.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager loading expensive models once at startup."""
    logger.info("Initializing Grid-Guard InferenceService during application startup...")
    try:
        service = InferenceService()
        app.state.inference_service = service
        logger.info(
            f"InferenceService initialized successfully: model={service.get_metadata().model_version}, "
            f"features={len(service.feature_names)}."
        )
    except Exception as exc:
        logger.error(
            f"Fatal error initializing InferenceService at startup: {exc}. "
            "Service will remain in unready state.",
            exc_info=True,
        )
        app.state.inference_service = None

    yield

    logger.info("Grid-Guard API server shutting down...")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app_settings = settings or get_settings()

    app = FastAPI(
        title=app_settings.api.title,
        version=app_settings.api.version,
        description=app_settings.api.description,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. Register CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.api.cors_origins,
        allow_credentials=app_settings.api.cors_allow_credentials,
        allow_methods=app_settings.api.cors_allow_methods,
        allow_headers=app_settings.api.cors_allow_headers,
    )

    # 2. Register Request ID and Logging Middleware
    app.add_middleware(BaseHTTPMiddleware, dispatch=request_id_and_logging_middleware)

    # 3. Register Centralized Exception Handlers
    register_exception_handlers(app)

    # 4. Mount Endpoint Routers
    app.include_router(health_router)
    app.include_router(metadata_router)
    app.include_router(prediction_router)
    app.include_router(inspection_router)

    return app


# Default application instance for ASGI servers (e.g. uvicorn)
app = create_app()
