"""Data schemas and transfer objects for Grid-Guard Explainability."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class FeatureContribution:
    """Individual feature contribution derived from SHAP value."""

    feature_name: str
    display_name: str
    category: str
    feature_value: float
    baseline_value: float | None
    shap_value: float
    contribution_direction: str  # "positive" (increases risk) or "negative" (decreases risk)
    rank: int
    description: str

    def to_dict(self) -> dict[str, Any]:
        """Convert contribution to dictionary representation."""
        return asdict(self)


@dataclass(frozen=True)
class TemporalEvidence:
    """Temporal source attribution linking feature behavior to historical calendar window."""

    anchor_date: str
    source_window_start: str
    source_window_end: str
    feature_name: str
    display_name: str
    observed_value: float
    reference_value: float | None
    relative_difference_pct: float | None
    shap_contribution: float
    interpretation: str

    def to_dict(self) -> dict[str, Any]:
        """Convert evidence to dictionary representation."""
        return asdict(self)


@dataclass(frozen=True)
class TamperingSignature:
    """Rule-based consumption pattern signature independent of model weights."""

    signature_type: str  # e.g., "sustained_step_down", "flatline", "zero_streak", "abnormal_peak", "behavior_shift"
    detected: bool
    magnitude: float
    duration_days: int | None
    severity: str  # "low", "moderate", "high"
    description: str

    def to_dict(self) -> dict[str, Any]:
        """Convert signature to dictionary representation."""
        return asdict(self)


@dataclass
class InspectionExplanation:
    """Comprehensive explainability record for a specific meter inspection ticket."""

    ticket_id: str
    meter_id: str
    evaluation_period: str
    model_probability: float
    calibrated_probability: float
    raw_score: float  # Model log-odds margin z
    base_value: float  # Expected log-odds margin E[z]
    expected_net_value: float | None
    inspection_recommended: bool
    priority_rank: int | None
    short_explanation: str
    detailed_explanation: str
    top_positive_features: list[FeatureContribution] = field(default_factory=list)
    top_negative_features: list[FeatureContribution] = field(default_factory=list)
    detected_signatures: list[TamperingSignature] = field(default_factory=list)
    temporal_evidence: list[TemporalEvidence] = field(default_factory=list)
    counter_evidence_summary: str | None = None
    financial_context: dict[str, Any] = field(default_factory=dict)
    model_version: str = "phase6_cost_sensitive_v1"
    feature_version: str = "phase3_features_v1"
    safety_caveat: str = (
        "Model prediction is an anomaly risk assessment and requires physical field "
        "inspection; statistical patterns alone do not prove unauthorized abstraction or physical tampering."
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert full explanation to JSON-serializable dictionary."""
        return {
            "ticket_id": self.ticket_id,
            "meter_id": self.meter_id,
            "evaluation_period": self.evaluation_period,
            "model_probability": self.model_probability,
            "calibrated_probability": self.calibrated_probability,
            "raw_score": self.raw_score,
            "base_value": self.base_value,
            "expected_net_value": self.expected_net_value,
            "inspection_recommended": self.inspection_recommended,
            "priority_rank": self.priority_rank,
            "short_explanation": self.short_explanation,
            "detailed_explanation": self.detailed_explanation,
            "top_positive_features": [f.to_dict() for f in self.top_positive_features],
            "top_negative_features": [f.to_dict() for f in self.top_negative_features],
            "detected_signatures": [s.to_dict() for s in self.detected_signatures],
            "temporal_evidence": [t.to_dict() for t in self.temporal_evidence],
            "counter_evidence_summary": self.counter_evidence_summary,
            "financial_context": self.financial_context,
            "model_version": self.model_version,
            "feature_version": self.feature_version,
            "safety_caveat": self.safety_caveat,
        }
