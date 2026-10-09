"""Configuration settings for Grid-Guard FastAPI inference service."""

from __future__ import annotations

import json
import os
from typing import Any

from pydantic import BaseModel, Field, field_validator


def _default_port() -> int:
    """Resolve default port from PORT environment variable (Render convention) or fallback to 8000."""
    port_env = os.environ.get("PORT")
    if port_env:
        try:
            return int(port_env)
        except ValueError:
            pass
    return 8000


def _parse_cors_origins(v: Any) -> list[str]:
    """Parse CORS origins from environment variable, string, or list."""
    if v is None:
        raw_env = os.environ.get("CORS_ORIGINS") or os.environ.get("GRID_GUARD_API__CORS_ORIGINS")
        if raw_env:
            v = raw_env
        else:
            return [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:4173",
            ]

    if isinstance(v, str):
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except Exception:
                pass
        return [part.strip() for part in v.split(",") if part.strip()]

    if isinstance(v, (list, tuple, set)):
        return [str(item).strip() for item in v if str(item).strip()]

    return [str(v).strip()]


class APISettings(BaseModel):
    """Settings for the FastAPI REST API server."""

    title: str = "Grid-Guard NTL Detection API"
    version: str = "0.1.0"
    description: str = (
        "Production-grade REST API for smart-meter non-technical loss (NTL) detection, "
        "cost-sensitive economic decisioning, and SHAP explainability."
    )
    host: str = "0.0.0.0"
    port: int = Field(default_factory=_default_port)
    reload: bool = False
    workers: int = 1
    cors_origins: list[str] = Field(default_factory=lambda: _parse_cors_origins(None))
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])

    # Model & Feature Artifact Paths
    model_path: str = Field(
        default_factory=lambda: os.environ.get(
            "GRID_GUARD_API__MODEL_PATH", "artifacts/cost_sensitive/champion_model.txt"
        )
    )

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

    @field_validator("cors_origins", mode="before")
    @classmethod
    def validate_cors_origins(cls, v: Any) -> list[str]:
        return _parse_cors_origins(v)
