"""FastAPI application package for Grid-Guard."""

from grid_guard.api.main import app, create_app
from grid_guard.api.services.inference import InferenceService

__all__ = ["InferenceService", "app", "create_app"]
