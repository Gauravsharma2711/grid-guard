"""Inspection ticket and queue schemas for Grid-Guard FastAPI service."""

from __future__ import annotations

from pydantic import BaseModel, Field

from grid_guard.api.schemas.prediction import ExplanationOutput


class InspectionTicketResponse(BaseModel):
    """Enriched field inspection ticket work order."""

    ticket_id: str = Field(
        ..., description="Deterministic ticket identifier (e.g. 'TCK-2016-10-30-EF550F26')"
    )
    meter_id: str = Field(..., description="Target smart meter account identifier")
    evaluation_period: str = Field(..., description="Evaluation snapshot period")
    tamper_probability: float = Field(
        ..., description="Predicted uncalibrated tampering probability"
    )
    calibrated_probability: float = Field(..., description="Calibrated posterior probability p_i")
    estimated_leakage_kwh: float = Field(
        ..., description="Estimated volume of unmetered electricity in kWh"
    )
    estimated_recoverable_revenue: float = Field(
        ..., description="Projected recoverable revenue R ($)"
    )
    dispatch_cost: float = Field(..., description="Field inspection dispatch cost C_FP ($)")
    expected_gross_recovery: float = Field(
        ..., description="Expected gross recovery E[R] = p * R ($)"
    )
    env: float = Field(..., description="Expected Net Value (ENV) = p * R - C_dispatch ($)")
    tau_cost: float = Field(
        ..., description="Bayes cost-optimal threshold C_dispatch / (C_dispatch + C_FN)"
    )
    tau_env: float = Field(..., description="Economic breakeven threshold C_dispatch / R")
    active_threshold: float = Field(..., description="Active probability threshold applied")
    decision_rule: str = Field(
        ..., description="Decision policy applied ('env', 'cost_threshold', 'fixed')"
    )
    inspection_recommended: bool = Field(
        ..., description="Whether inspection is economically justified"
    )
    priority_rank: int | None = Field(
        default=None, description="Queue rank ordered by ENV descending"
    )
    customer_type: str = Field(default="standard", description="Customer classification")
    feeder_id: str = Field(default="unknown", description="Feeder network identifier")
    data_quality_status: str = Field(default="good", description="Quality assessment")
    signatures_summary: str = Field(
        default="Multivariate Feature Anomaly",
        description="Summary of electrical tampering signatures",
    )
    explanation: ExplanationOutput | None = Field(
        default=None, description="Detailed explainability record"
    )
    safety_caveat: str = Field(
        default="Model evidence indicates an anomalous consumption pattern and requires physical on-site inspection.",
        description="Standard legal/regulatory disclaimer",
    )


class InspectionQueueRequest(BaseModel):
    """Request parameters for querying or ranking inspection candidates into a prioritized queue."""

    max_inspections: int = Field(
        default=50, ge=1, le=500, description="Maximum number of prioritized tickets to return"
    )
    decision_rule: str = Field(
        default="env", description="Decision policy: 'env', 'cost_threshold', or 'fixed_threshold'"
    )
    min_env: float = Field(default=0.0, description="Minimum Expected Net Value cutoff")
    min_probability: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Minimum probability cutoff"
    )
    include_explanations: bool = Field(
        default=True, description="Whether to include full SHAP narratives for queued tickets"
    )


class InspectionQueueResponse(BaseModel):
    """Response payload containing a ranked inspection queue."""

    queue_size: int = Field(..., description="Number of tickets in the returned inspection queue")
    total_expected_recovery: float = Field(
        ..., description="Sum of expected gross recovery across all tickets ($)"
    )
    total_dispatch_cost: float = Field(
        ..., description="Total crew dispatch cost for the queue ($)"
    )
    total_net_value: float = Field(
        ..., description="Cumulative Expected Net Value (total recovery - total cost) ($)"
    )
    decision_rule: str = Field(..., description="Decision policy applied")
    tickets: list[InspectionTicketResponse] = Field(
        default_factory=list, description="Ranked inspection work orders"
    )
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
