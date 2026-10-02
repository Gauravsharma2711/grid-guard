"""Inspection prioritization engine, period aggregation, and queue generation."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import polars as pl

from grid_guard.config.decision import (
    AggregationPeriod,
    DecisionRule,
    DecisionSettings,
    ProbabilitySource,
    RankingStrategy,
)
from grid_guard.decision.capacity import CapacityDispatcher
from grid_guard.decision.env import compute_expected_net_value
from grid_guard.decision.thresholds import (
    compute_active_threshold,
    compute_bayes_cost_threshold,
    compute_env_threshold,
)
from grid_guard.decision.tickets import generate_deterministic_ticket_id

logger = logging.getLogger(__name__)


class InspectionPrioritizer:
    """End-to-end decision engine prioritizing field inspections based on Expected Net Value (ENV)."""

    def __init__(self, settings: DecisionSettings | None = None) -> None:
        self.settings = settings or DecisionSettings()

    def prioritize(
        self,
        predictions_df: pl.DataFrame,
        evaluation_period: str | None = None,
        filter_dispatched_only: bool = False,
    ) -> pl.DataFrame:
        """Transform raw/calibrated model predictions into a prioritized inspection queue.

        Args:
            predictions_df: Polars DataFrame containing model predictions and metadata.
            evaluation_period: Optional label for the evaluation cycle (e.g. '2016-10-30').
            filter_dispatched_only: If True, returns only tickets approved for physical dispatch.
                                    If False, returns all evaluated candidates with priority_rank assigned.

        Returns:
            Ranked Polars DataFrame conforming to the InspectionTicket schema.
        """
        if predictions_df.is_empty():
            logger.warning("Empty predictions DataFrame supplied to InspectionPrioritizer.")
            return pl.DataFrame()

        df = predictions_df

        # Step 1: Period-Level Aggregation (Enforce one ticket per inspection unit)
        df_agg = self._aggregate_inspection_units(df)

        # Step 2: Extract & Validate Core Inputs
        p_col = (
            "predicted_prob"
            if self.settings.probability_source == ProbabilitySource.CALIBRATED
            and "predicted_prob" in df_agg.columns
            else "uncalibrated_prob"
            if "uncalibrated_prob" in df_agg.columns
            else "predicted_prob"
        )
        uncal_col = "uncalibrated_prob" if "uncalibrated_prob" in df_agg.columns else p_col

        p_cal = df_agg.get_column(p_col).to_numpy().astype(np.float64)
        p_uncal = df_agg.get_column(uncal_col).to_numpy().astype(np.float64)

        # Leakage cost & recoverable revenue
        leakage_col = (
            "estimated_leakage_cost"
            if "estimated_leakage_cost" in df_agg.columns
            else "leakage_cost"
            if "leakage_cost" in df_agg.columns
            else None
        )
        if leakage_col is not None:
            c_fn_raw = df_agg.get_column(leakage_col).fill_null(0.0).to_numpy().astype(np.float64)
        else:
            c_fn_raw = np.zeros(len(df_agg), dtype=np.float64)

        # Apply recovery factor
        recoverable_rev = c_fn_raw * self.settings.recovery_factor

        # Estimated leakage kWh if present
        leak_kwh_col = (
            "leakage_monthly_kwh"
            if "leakage_monthly_kwh" in df_agg.columns
            else "leakage_daily_kwh"
        )
        if leak_kwh_col in df_agg.columns:
            leak_kwh = df_agg.get_column(leak_kwh_col).fill_null(0.0).to_numpy().astype(np.float64)
        else:
            # Fallback estimation: R / (Tariff * Cycles)
            leak_kwh = np.where(
                self.settings.default_tariff > 0,
                recoverable_rev
                / (self.settings.default_tariff * max(1, self.settings.undetected_cycles)),
                0.0,
            )

        # Step 3: Compute ENV and Expected Gross Recovery
        exp_recovery, env = compute_expected_net_value(
            probabilities=p_cal,
            recoverable_revenue=recoverable_rev,
            dispatch_cost=self.settings.dispatch_cost,
        )

        # Step 4: Compute Dynamic Thresholds
        tau_cost = compute_bayes_cost_threshold(
            dispatch_cost=self.settings.dispatch_cost,
            fn_cost=c_fn_raw,
        )
        tau_env = compute_env_threshold(
            dispatch_cost=self.settings.dispatch_cost,
            recoverable_revenue=recoverable_rev,
        )
        active_tau = compute_active_threshold(
            tau_cost=tau_cost,
            tau_env=tau_env,
            decision_rule=self.settings.decision_rule,
            fixed_threshold=self.settings.fixed_threshold,
        )

        # Step 5: Determine Inspection Recommendation
        rule = self.settings.decision_rule
        min_p = self.settings.min_probability
        min_r = self.settings.min_recoverable_revenue
        min_e = self.settings.min_env

        if rule == DecisionRule.ENV:
            # Primary rule: Positive ENV and passes operational guardrails
            recommended = (env > min_e) & (p_cal >= min_p) & (recoverable_rev >= min_r)
        elif rule == DecisionRule.COST_THRESHOLD:
            # Bayes threshold rule: p >= tau_cost
            recommended = (p_cal >= tau_cost) & (p_cal >= min_p)
        elif rule == DecisionRule.FIXED_THRESHOLD:
            # Conventional fixed threshold
            recommended = p_cal >= self.settings.fixed_threshold
        else:
            raise ValueError(f"Unsupported decision rule: {rule}")

        # Step 6: Construct Period & Deterministic Ticket IDs
        meter_ids = df_agg.get_column("meter_id").to_list()
        if evaluation_period is not None:
            periods = [str(evaluation_period)] * len(df_agg)
        elif "timestamp" in df_agg.columns:
            periods = [str(ts) for ts in df_agg.get_column("timestamp").to_list()]
        else:
            periods = ["period_1"] * len(df_agg)

        ticket_ids = [
            generate_deterministic_ticket_id(m_id, p_str)
            for m_id, p_str in zip(meter_ids, periods, strict=False)
        ]

        # Extract optional context fields if available
        customer_types = (
            df_agg.get_column("customer_type").to_list()
            if "customer_type" in df_agg.columns
            else ["standard"] * len(df_agg)
        )
        feeder_ids = (
            df_agg.get_column("feeder_id").to_list()
            if "feeder_id" in df_agg.columns
            else ["unknown"] * len(df_agg)
        )
        quality_statuses = (
            df_agg.get_column("data_quality_status").to_list()
            if "data_quality_status" in df_agg.columns
            else ["good"] * len(df_agg)
        )
        actual_labels = (
            df_agg.get_column("tamper_label").to_list()
            if "tamper_label" in df_agg.columns
            else None
        )

        # Assemble Output DataFrame
        ticket_dict: dict[str, Any] = {
            "ticket_id": ticket_ids,
            "meter_id": meter_ids,
            "evaluation_period": periods,
            "tamper_probability": p_uncal,
            "calibrated_probability": p_cal,
            "estimated_leakage_kwh": leak_kwh,
            "estimated_recoverable_revenue": recoverable_rev,
            "dispatch_cost": np.full(len(df_agg), self.settings.dispatch_cost, dtype=np.float64),
            "expected_gross_recovery": exp_recovery,
            "env": env,
            "tau_cost": tau_cost,
            "tau_env": tau_env,
            "active_threshold": active_tau,
            "decision_rule": [rule.value] * len(df_agg),
            "inspection_recommended": recommended,
            "customer_type": customer_types,
            "feeder_id": feeder_ids,
            "data_quality_status": quality_statuses,
        }
        if actual_labels is not None:
            ticket_dict["actual_tamper_label"] = actual_labels

        df_out = pl.DataFrame(ticket_dict)

        # Step 7: Multi-Key Sorting & Ranking
        df_ranked = self._rank_tickets(df_out)

        # Step 8: Apply Capacity Constraints
        df_final = CapacityDispatcher.apply_capacity(
            df_ranked=df_ranked,
            max_inspections=self.settings.max_inspections_per_period,
            policy=self.settings.capacity_policy,
            filter_dispatched_only=filter_dispatched_only,
        )

        return df_final

    def _aggregate_inspection_units(self, df: pl.DataFrame) -> pl.DataFrame:
        """Aggregate multi-snapshot predictions to strictly ONE ticket per meter per inspection unit."""
        period_mode = self.settings.aggregation_period
        if period_mode == AggregationPeriod.NONE or "meter_id" not in df.columns:
            return df

        if period_mode == AggregationPeriod.LATEST_SNAPSHOT and "timestamp" in df.columns:
            # Sort by timestamp ascending and take last row per meter
            df_agg = (
                df.sort(["meter_id", "timestamp"]).group_by("meter_id", maintain_order=True).last()
            )
            logger.info(
                "Aggregated multi-snapshot predictions to latest snapshot: %d rows -> %d unique meters",
                len(df),
                len(df_agg),
            )
            return df_agg

        elif period_mode == AggregationPeriod.MAX_SCORE:
            score_col = "predicted_prob" if "predicted_prob" in df.columns else "uncalibrated_prob"
            df_agg = (
                df.sort(["meter_id", score_col]).group_by("meter_id", maintain_order=True).last()
            )
            return df_agg

        return df

    def _rank_tickets(self, df: pl.DataFrame) -> pl.DataFrame:
        """Rank candidate tickets according to the configured ranking strategy."""
        strategy = self.settings.ranking_strategy

        if strategy == RankingStrategy.ENV_DESCENDING:
            # Primary: ENV descending. Secondary tie-breakers: calibrated prob desc, recoverable rev desc, meter_id asc
            df_sorted = df.sort(
                by=["env", "calibrated_probability", "estimated_recoverable_revenue", "meter_id"],
                descending=[True, True, True, False],
            )
        elif strategy == RankingStrategy.PROBABILITY_DESCENDING:
            df_sorted = df.sort(
                by=["calibrated_probability", "env", "estimated_recoverable_revenue", "meter_id"],
                descending=[True, True, True, False],
            )
        elif strategy == RankingStrategy.RECOVERY_DESCENDING:
            df_sorted = df.sort(
                by=["estimated_recoverable_revenue", "env", "calibrated_probability", "meter_id"],
                descending=[True, True, True, False],
            )
        else:
            df_sorted = df.sort(by="env", descending=True)

        return df_sorted
