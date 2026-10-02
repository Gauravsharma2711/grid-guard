"""Routes package for Grid-Guard FastAPI service."""

from grid_guard.api.routes.health import router as health_router
from grid_guard.api.routes.inspection import router as inspection_router
from grid_guard.api.routes.metadata import router as metadata_router
from grid_guard.api.routes.prediction import router as prediction_router

__all__ = [
    "health_router",
    "inspection_router",
    "metadata_router",
    "prediction_router",
]
