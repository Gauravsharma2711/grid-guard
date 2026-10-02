"""Prediction request and response schemas for Grid-Guard FastAPI service."""

from __future__ import annotations

import math

from pydantic import BaseModel, Field, field_validator

from grid_guard.api.schemas.common import DataQualitySummary, ModelMetadataResponse


class MeterReading(BaseModel):
    """Individual daily smart meter consumption reading."""

    timestamp: str = Field(..., description="Calendar date or ISO timestamp (e.g. '2016-10-30')")
    consumption_kwh: float = Field(
        ..., description="Measured daily electricity consumption in kilowatt-hours (kWh)"
    )

    @field_validator("consumption_kwh")
    @classmethod
    def validate_consumption(cls, v: float) -> float:
        """Validate consumption is a non-negative, finite number."""
        if math.isnan(v) or math.isinf(v):
            raise ValueError("consumption_kwh must be a finite number, cannot be NaN or Infinite.")
        if v < 0.0:
            raise ValueError(f"consumption_kwh must be non-negative, got {v}.")
        return round(v, 4)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Basic check on timestamp format."""
        s = v.strip()
        if not s:
            raise ValueError("timestamp cannot be empty.")
        return s.split("T")[0]  # Normalize to YYYY-MM-DD


class SingleMeterPredictionRequest(BaseModel):
    """Request payload for evaluating an individual smart meter time series."""

    meter_id: str = Field(
        ..., min_length=1, description="Unique electricity meter or account identifier"
    )
    readings: list[MeterReading] = Field(
        ..., description="Chronological series of daily meter consumption readings"
    )
    evaluation_date: str | None = Field(
        default=None,
        description="Target evaluation date (defaults to latest timestamp in readings)",
    )
    tariff: float | None = Field(
        default=None, gt=0.0, description="Optional tariff rate override (currency/kWh)"
    )
    customer_type: str = Field(
        default="standard",
        description="Customer classification (e.g. residential, commercial, industrial)",
    )
    feeder_id: str = Field(
        default="unknown", description="Distribution substation feeder identifier"
    )
    dispatch_cost: float | None = Field(
        default=None, ge=0.0, description="Field inspection dispatch cost override"
    )
    decision_rule: str = Field(
        default="env", description="Decision policy: 'env', 'cost_threshold', or 'fixed_threshold'"
    )
    fixed_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Probability cutoff if fixed_threshold rule is active",
    )
    include_explanation: bool = Field(
        default=True, description="Whether to compute Tree-SHAP attributions and narratives"
    )

    @field_validator("readings")
    @classmethod
    def validate_readings(cls, readings: list[MeterReading]) -> list[MeterReading]:
        """Ensure readings list is non-empty and has unique timestamps."""
        if not readings:
            raise ValueError("readings list cannot be empty.")
        seen_dates = set()
        for r in readings:
            if r.timestamp in seen_dates:
                raise ValueError(f"Duplicate reading detected for timestamp '{r.timestamp}'.")
            seen_dates.add(r.timestamp)
        return readings

    @field_validator("decision_rule")
    @classmethod
    def validate_decision_rule(cls, rule: str) -> str:
        """Validate rule selection."""
        allowed = {"env", "cost_threshold", "fixed_threshold"}
        r = rule.lower().strip()
        if r not in allowed:
            raise ValueError(f"Invalid decision_rule '{rule}'. Allowed values: {sorted(allowed)}")
        return r


class BatchPredictionRequest(BaseModel):
    """Request payload for bounded multi-meter batch evaluation."""

    meters: list[SingleMeterPredictionRequest] = Field(
        ..., min_length=1, description="List of single meter prediction requests"
    )
    batch_id: str | None = Field(
        default=None, description="Optional client-provided batch correlation identifier"
    )
    include_explanation: bool = Field(
        default=False, description="Default to False for batch to maximize throughput"
    )


class PredictionOutput(BaseModel):
    """Statistical prediction values produced by the model."""

    raw_score: float = Field(..., description="Raw margin score z in log-odds space")
    tamper_probability: float = Field(
        ..., ge=0.0, le=1.0, description="Uncalibrated sigmoid probability sigma(z)"
    )
    calibrated_probability: float = Field(
        ..., ge=0.0, le=1.0, description="Calibrated tampering risk probability"
    )
    prediction_label: int = Field(..., description="Binary classification (1=tampering, 0=normal)")


class FinancialOutput(BaseModel):
    """Financial exposure, expected recovery, and cost estimations."""

    estimated_leakage_kwh: float = Field(
        ..., ge=0.0, description="Estimated unmetered energy loss volume (kWh)"
    )
    estimated_recoverable_revenue: float = Field(
        ..., ge=0.0, description="Projected recoverable revenue R ($)"
    )
    expected_gross_recovery: float = Field(
        ..., ge=0.0, description="Probability-weighted recovery E[R] = p * R ($)"
    )
    dispatch_cost: float = Field(
        ..., ge=0.0, description="Physical crew inspection dispatch cost C_FP ($)"
    )
    expected_net_value: float = Field(
        ..., description="Expected Net Value (ENV) = p * R - C_dispatch ($)"
    )
    tariff: float = Field(..., gt=0.0, description="Effective tariff applied per kWh")
    currency: str = Field(default="INR", description="Operational currency unit")


class DecisionOutput(BaseModel):
    """Economic and operational inspection decision metrics."""

    decision_rule: str = Field(
        ..., description="Active decision policy applied ('env', 'cost_threshold', 'fixed')"
    )
    active_threshold: float = Field(
        ..., description="Operational probability threshold tau applied for recommendation"
    )
    tau_cost: float = Field(
        ..., description="Bayes cost-optimal threshold C_dispatch / (C_dispatch + C_FN)"
    )
    tau_env: float = Field(
        ..., description="Breakeven threshold for positive net return C_dispatch / R"
    )
    inspection_recommended: bool = Field(
        ..., description="Whether physical meter inspection is recommended"
    )
    priority_context: str | None = Field(
        default=None, description="Actionable operational summary context"
    )


class FeatureContributionSchema(BaseModel):
    """Feature attribution record derived from Tree-SHAP."""

    feature_name: str
    display_name: str
    category: str
    feature_value: float
    baseline_value: float | None = None
    shap_value: float
    contribution_direction: str  # 'positive' or 'negative'
    rank: int
    description: str


class TamperingSignatureSchema(BaseModel):
    """Rule-based consumption anomaly signature."""

    signature_type: str
    detected: bool
    magnitude: float
    duration_days: int | None = None
    severity: str
    description: str


class TemporalEvidenceSchema(BaseModel):
    """Temporal source attribution interval."""

    anchor_date: str
    source_window_start: str
    source_window_end: str
    feature_name: str
    display_name: str
    observed_value: float
    reference_value: float | None = None
    relative_difference_pct: float | None = None
    shap_contribution: float
    interpretation: str


class ExplanationOutput(BaseModel):
    """Comprehensive explainability record with SHAP attributions, signatures, and narratives."""

    summary: str = Field(..., description="Concise card-ready summary for field technicians")
    detailed_explanation: str = Field(
        ..., description="In-depth audit narrative detailing feature and financial evidence"
    )
    top_positive_contributors: list[FeatureContributionSchema] = Field(default_factory=list)
    top_negative_contributors: list[FeatureContributionSchema] = Field(default_factory=list)
    detected_signatures: list[TamperingSignatureSchema] = Field(default_factory=list)
    temporal_evidence: list[TemporalEvidenceSchema] = Field(default_factory=list)
    counter_evidence_summary: str | None = None
    safety_caveat: str = Field(
        default="Model evidence indicates an anomalous consumption pattern and requires physical on-site inspection.",
        description="Standard legal/regulatory safety disclaimer",
    )


class SingleMeterPredictionResponse(BaseModel):
    """Full canonical response object for a single meter prediction request."""

    meter_id: str
    evaluation_timestamp: str
    model: ModelMetadataResponse
    data_quality: DataQualitySummary
    prediction: PredictionOutput
    financial: FinancialOutput
    decision: DecisionOutput
    explanation: ExplanationOutput | None = None
    processing_time_ms: float = Field(
        ..., description="Total server processing latency in milliseconds"
    )


class BatchItemError(BaseModel):
    """Error record for an individual item failure in a batch request."""

    meter_id: str
    error: str
    error_type: str


class BatchPredictionResponse(BaseModel):
    """Response payload for multi-meter batch requests supporting partial success."""

    batch_id: str
    total_items: int
    successful_items: int
    failed_items: int
    results: list[SingleMeterPredictionResponse] = Field(default_factory=list)
    errors: list[BatchItemError] = Field(default_factory=list)
    processing_time_ms: float
