"""Configuration settings for Phase 6 Cost-Sensitive Learning & Custom Objective."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class CostNormalizationType(StrEnum):
    """Supported global reference scale normalization methods for financial weights."""

    DISPATCH_COST = (
        "dispatch_cost"  # Normalized by C_dispatch (w_neg = 1.0, w_pos = C_FN / C_dispatch)
    )
    MEAN = "mean"  # Normalized by mean training cost
    MEDIAN = "median"  # Normalized by median training cost
    NONE = "none"  # Raw financial dollar amounts directly


class ProbabilityCalibrationType(StrEnum):
    """Supported post-hoc probability calibration techniques for shifted cost margins."""

    ISOTONIC = "isotonic"  # Non-parametric piecewise constant calibration
    PLATT = "platt"  # Parametric logistic calibration
    NONE = "none"  # Raw sigmoid output without recalibration


class CostSensitiveSettings(BaseModel):
    """Financial cost-sensitive model configuration parameters."""

    enabled: bool = Field(
        default=True,
        description="Whether to train with cost-sensitive custom objective.",
    )
    objective_name: str = Field(
        default="cost_sensitive_weighted_logistic",
        description="Name of the cost-sensitive custom objective function.",
    )
    dispatch_cost: float = Field(
        default=100.0,
        ge=0.01,
        description="Fixed operational cost C_FP to dispatch a physical field inspection ($).",
    )
    default_tariff: float = Field(
        default=0.15,
        ge=0.001,
        description="Fallback energy tariff ($/kWh) for converting leakage volume to revenue.",
    )
    tariff_source: str = Field(
        default="assumed_fallback",
        description="Provenance source of tariff rate ('observed' vs 'assumed_fallback').",
    )
    undetected_cycles: int = Field(
        default=12,
        ge=1,
        description="Assumed billing months undetected tampering persists before discovery.",
    )
    min_leakage_kwh: float = Field(
        default=5.0,
        ge=0.0,
        description="Minimum monthly deficit threshold to register non-zero financial loss.",
    )
    min_fn_cost: float = Field(
        default=100.0,
        ge=0.01,
        description="Minimum floor for positive class C_FN to ensure strictly positive Hessian.",
    )
    cost_normalization: CostNormalizationType = Field(
        default=CostNormalizationType.DISPATCH_COST,
        description="Method used to normalize financial weights to a well-conditioned scale.",
    )
    reference_scale: float | None = Field(
        default=None,
        description="Explicit user-specified reference scale (overrides cost_normalization if set).",
    )
    cost_capping: bool = Field(
        default=False,
        description="Whether to winsorize extreme C_FN values at a top percentile.",
    )
    cost_cap_percentile: float = Field(
        default=99.5,
        ge=50.0,
        le=100.0,
        description="Percentile at which to cap extreme C_FN outlier values.",
    )
    threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Conventional decision threshold preserved for primary head-to-head comparison.",
    )
    calibration_method: ProbabilityCalibrationType = Field(
        default=ProbabilityCalibrationType.ISOTONIC,
        description="Validation-fitted post-hoc probability calibration technique.",
    )
    selection_metric: str = Field(
        default="total_operational_loss",
        description="Validation metric used to select best cost-sensitive variant.",
    )
    random_seed: int = Field(
        default=42,
        description="Deterministic random seed for reproducibility.",
    )
