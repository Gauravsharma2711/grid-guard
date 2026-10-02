"""Configuration settings for Grid-Guard Phase 8 SHAP Explainability."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class ExplainabilitySettings(BaseSettings):
    """Configuration parameters for SHAP explainability, signatures, and narratives."""

    # Computation & sampling limits
    global_sample_size: int = Field(
        default=500,
        ge=50,
        description="Number of evaluation instances for global SHAP summary analysis",
    )
    top_k_tickets: int = Field(
        default=100,
        ge=1,
        description="Number of top prioritized inspection tickets to enrich with full local explanations",
    )

    # Narrative explanation constraints
    max_positive_features: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum number of top positive risk contributors to highlight in narrative",
    )
    max_negative_features: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Maximum number of counter-evidence features to report in technical explanation",
    )

    # Tampering signature detection thresholds
    step_down_ratio_threshold: float = Field(
        default=0.50,
        gt=0.0,
        lt=1.0,
        description="Consumption-to-baseline ratio below which a sustained drop is flagged (e.g. 0.50 = 50% drop)",
    )
    step_down_min_days: int = Field(
        default=7,
        ge=1,
        description="Minimum consecutive days of depressed consumption required to flag sustained step-down",
    )
    zero_streak_min_days: int = Field(
        default=3,
        ge=1,
        description="Minimum consecutive days of zero or near-zero consumption to flag zero streak",
    )
    zero_consumption_threshold: float = Field(
        default=0.001,
        ge=0.0,
        description="Threshold (kWh) below which consumption is treated as zero",
    )
    flatline_max_cv: float = Field(
        default=0.05,
        gt=0.0,
        description="Rolling coefficient of variation ceiling below which consumption is flagged as flatline",
    )
    flatline_min_days: int = Field(
        default=7,
        ge=2,
        description="Minimum consecutive flatline days required to flag flatline signature",
    )

    # Output directory
    output_dir: Path | None = Field(
        default=None,
        description="Output directory for explainability artifacts (defaults to artifacts/explainability)",
    )

    # Reproducibility
    random_seed: int = Field(
        default=42,
        description="Random seed for deterministic background/sample selection",
    )
