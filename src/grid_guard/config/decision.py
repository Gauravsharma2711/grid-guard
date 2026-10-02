"""Configuration parameters for dynamic thresholding, Expected Net Value (ENV), and inspection prioritization."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class DecisionRule(StrEnum):
    """Operational criterion for recommending a physical meter inspection."""

    ENV = "env"  # Inspect if ENV_i > 0 (p_i > tau_env_i)
    COST_THRESHOLD = "cost_threshold"  # Inspect if p_i >= tau_cost_i (Bayes cost threshold)
    FIXED_THRESHOLD = "fixed_threshold"  # Inspect if p_i >= fixed_threshold (e.g. 0.5)


class CapacityPolicy(StrEnum):
    """Policy for dispatching inspection tickets under hard operational crew capacity constraints."""

    STRICTLY_POSITIVE_ENV = (
        "strictly_positive_env"  # Never dispatch negative-ENV meters even if spare capacity exists
    )
    FILL_QUOTA = "fill_quota"  # Fill quota up to max_inspections using highest-ranked meters regardless of ENV sign


class RankingStrategy(StrEnum):
    """Primary sorting key for prioritizing the inspection queue."""

    ENV_DESCENDING = "env_descending"  # Sort by Expected Net Value descending
    PROBABILITY_DESCENDING = (
        "probability_descending"  # Sort by predicted tampering probability descending
    )
    RECOVERY_DESCENDING = "recovery_descending"  # Sort by estimated recoverable revenue descending


class AggregationPeriod(StrEnum):
    """Temporal granularity for collapsing multi-snapshot predictions into a single inspection unit."""

    LATEST_SNAPSHOT = "latest_snapshot"  # Most recent snapshot timestamp per meter
    MAX_SCORE = "max_score"  # Snapshot corresponding to maximum tampering probability
    MAX_ENV = "max_env"  # Snapshot corresponding to maximum ENV
    NONE = "none"  # Keep all evaluation snapshot rows without aggregation


class ProbabilitySource(StrEnum):
    """Source probability representation consumed by the decision engine."""

    CALIBRATED = "calibrated"  # Post-hoc calibrated probability (e.g. Isotonic/Platt)
    UNCALIBRATED = "uncalibrated"  # Raw sigmoid output from boosting model


class DecisionSettings(BaseModel):
    """Centralized operational and financial parameters for the Grid-Guard decision engine."""

    decision_rule: DecisionRule = DecisionRule.ENV
    dispatch_cost: float = Field(
        default=100.0, ge=0.0, description="Cost (USD) to dispatch an inspection crew (C_dispatch)"
    )
    default_tariff: float = Field(
        default=0.15, gt=0.0, description="Electricity tariff rate (USD/kWh)"
    )
    recovery_factor: float = Field(
        default=1.0,
        gt=0.0,
        le=1.0,
        description="Expected fraction of unmetered leakage recoverable upon inspection (0 < eta <= 1)",
    )
    undetected_cycles: int = Field(
        default=12,
        ge=1,
        description="Number of monthly billing cycles undetected leakage continues before discovery",
    )
    min_leakage_kwh: float = Field(
        default=5.0,
        ge=0.0,
        description="Minimum daily deficit (kWh) to classify as material revenue leakage",
    )
    min_probability: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Operational guardrail: minimum probability required for dispatch",
    )
    min_recoverable_revenue: float = Field(
        default=0.0,
        ge=0.0,
        description="Operational guardrail: minimum recoverable revenue (USD) required for dispatch",
    )
    min_env: float = Field(
        default=0.0,
        description="Operational guardrail: minimum Expected Net Value (USD) required for dispatch",
    )
    fixed_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Conventional fixed decision threshold for baseline comparison",
    )
    max_inspections_per_period: int | None = Field(
        default=None,
        ge=1,
        description="Hard capacity limit on total inspection tickets per evaluation period",
    )
    capacity_policy: CapacityPolicy = CapacityPolicy.STRICTLY_POSITIVE_ENV
    ranking_strategy: RankingStrategy = RankingStrategy.ENV_DESCENDING
    probability_source: ProbabilitySource = ProbabilitySource.CALIBRATED
    aggregation_period: AggregationPeriod = AggregationPeriod.LATEST_SNAPSHOT
    top_k_values: list[int] = Field(default_factory=lambda: [10, 25, 50, 100, 250, 500, 1000, 2000])
    random_seed: int = 42
