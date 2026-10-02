"""Canonical inspection ticket schema and deterministic ticket identifier generation."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any

import polars as pl


def generate_deterministic_ticket_id(meter_id: str, evaluation_period: str) -> str:
    """Generate a reproducible, deterministic ticket identifier based on meter and period.

    Format:
        TCK-{eval_period}-{hex_hash[:8]}

    Example:
        TCK-2016-10-30-A1B2C3D4
    """
    raw_key = f"{meter_id}::{evaluation_period}"
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:8].upper()
    clean_period = str(evaluation_period).replace("/", "-").replace(" ", "_")
    return f"TCK-{clean_period}-{digest}"


@dataclass(frozen=True)
class InspectionTicket:
    """Canonical schema for a field inspection work order ticket."""

    ticket_id: str
    meter_id: str
    evaluation_period: str
    tamper_probability: float
    calibrated_probability: float
    estimated_leakage_kwh: float
    estimated_recoverable_revenue: float
    dispatch_cost: float
    expected_gross_recovery: float
    env: float
    tau_cost: float
    tau_env: float
    active_threshold: float
    decision_rule: str
    inspection_recommended: bool
    priority_rank: int | None = None
    customer_type: str = "standard"
    feeder_id: str = "unknown"
    data_quality_status: str = "good"
    actual_tamper_label: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert ticket to dictionary."""
        return asdict(self)


def tickets_to_polars(tickets: list[InspectionTicket]) -> pl.DataFrame:
    """Convert a list of InspectionTicket objects to a strongly-typed Polars DataFrame."""
    if not tickets:
        return pl.DataFrame(
            schema={
                "ticket_id": pl.String,
                "meter_id": pl.String,
                "evaluation_period": pl.String,
                "tamper_probability": pl.Float64,
                "calibrated_probability": pl.Float64,
                "estimated_leakage_kwh": pl.Float64,
                "estimated_recoverable_revenue": pl.Float64,
                "dispatch_cost": pl.Float64,
                "expected_gross_recovery": pl.Float64,
                "env": pl.Float64,
                "tau_cost": pl.Float64,
                "tau_env": pl.Float64,
                "active_threshold": pl.Float64,
                "decision_rule": pl.String,
                "inspection_recommended": pl.Boolean,
                "priority_rank": pl.Int32,
                "customer_type": pl.String,
                "feeder_id": pl.String,
                "data_quality_status": pl.String,
                "actual_tamper_label": pl.Int8,
            }
        )

    records = [t.to_dict() for t in tickets]
    return pl.DataFrame(records)
