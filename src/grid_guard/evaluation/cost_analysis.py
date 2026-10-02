"""Financial cost distribution profiling, weight normalization, and threshold diagnostic analysis."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import polars as pl

from grid_guard.config.cost_sensitive import CostNormalizationType
from grid_guard.evaluation.financial import DataSourceType, FinancialAuditRecord

logger = logging.getLogger(__name__)


@dataclass
class FinancialWeightAuditReport:
    """Detailed statistical and provenance audit of financial training weights."""

    total_samples: int
    positive_samples: int
    negative_samples: int
    positive_prevalence: float
    c_fp_dispatch_cost: float
    c_fn_min: float
    c_fn_median: float
    c_fn_mean: float
    c_fn_p90: float
    c_fn_p99: float
    c_fn_max: float
    weight_min: float
    weight_median: float
    weight_mean: float
    weight_max: float
    weight_ratio_median_pos_to_neg: float
    weight_ratio_mean_pos_to_neg: float
    normalization_strategy: str
    reference_scale: float
    cost_capping_applied: bool
    cost_cap_percentile: float | None
    cost_cap_value: float | None
    samples_capped: int
    provenance_records: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)


class FinancialWeightBuilder:
    """Constructs, normalizes, and audits financial training weights."""

    @staticmethod
    def construct_training_weights(
        y_train: np.ndarray | pl.Series,
        estimated_leakage_costs: np.ndarray | pl.Series,
        dispatch_cost: float = 100.0,
        min_fn_cost: float = 100.0,
        normalization: CostNormalizationType | str = CostNormalizationType.DISPATCH_COST,
        reference_scale: float | None = None,
        cost_capping: bool = False,
        cost_cap_percentile: float = 99.5,
    ) -> tuple[np.ndarray, np.ndarray, FinancialWeightAuditReport]:
        """Construct per-observation financial weights for cost-sensitive learning.

        Assignment Rules:
            - Honest consumers (y_i = 0): w_raw,i = C_FP = dispatch_cost
            - Theft consumers (y_i = 1):  w_raw,i = max(C_FN,i, min_fn_cost)

        Global Normalization:
            w_norm,i = w_raw,i / S_ref
            A global reference scale preserves relative economic ratios without distorting gradient balance.

        Args:
            y_train: Ground-truth binary training labels.
            estimated_leakage_costs: Derived per-sample revenue leakage estimates ($).
            dispatch_cost: Assumed field inspection dispatch cost C_FP ($).
            min_fn_cost: Minimum floor for positive leakage cost to guarantee strictly positive loss weight.
            normalization: Method to scale weights ('dispatch_cost', 'mean', 'median', 'none').
            reference_scale: Optional user-specified reference scale override.
            cost_capping: Whether to winsorize extreme C_FN values at cost_cap_percentile.
            cost_cap_percentile: Top percentile at which to cap positive leakage costs.

        Returns:
            Tuple of (normalized_weights, raw_weights, audit_report).
        """
        y_np = (
            y_train.to_numpy().astype(np.int32)
            if isinstance(y_train, pl.Series)
            else np.asarray(y_train, dtype=np.int32)
        )
        leakage_np = (
            estimated_leakage_costs.to_numpy().astype(np.float64)
            if isinstance(estimated_leakage_costs, pl.Series)
            else np.asarray(estimated_leakage_costs, dtype=np.float64)
        )

        n_total = len(y_np)
        pos_mask = y_np == 1
        n_pos = int(np.sum(pos_mask))
        n_neg = n_total - n_pos

        if n_pos == 0:
            raise ValueError("Training set contains zero positive (theft) examples.")

        # Step 1: Base positive leakage costs with positive floor
        c_fn_raw = np.maximum(leakage_np[pos_mask], min_fn_cost)

        # Step 2: Optional outlier capping on C_FN
        samples_capped = 0
        cap_val = None
        if cost_capping:
            cap_val = float(np.percentile(c_fn_raw, cost_cap_percentile))
            capped_mask = c_fn_raw > cap_val
            samples_capped = int(np.sum(capped_mask))
            c_fn_processed = np.minimum(c_fn_raw, cap_val)
            logger.info(
                f"Cost capping applied at {cost_cap_percentile}th percentile: cap=${cap_val:,.2f} "
                f"({samples_capped:,} observations capped)."
            )
        else:
            c_fn_processed = c_fn_raw

        # Step 3: Populate raw weights array
        w_raw = np.full(n_total, fill_value=float(dispatch_cost), dtype=np.float64)
        w_raw[pos_mask] = c_fn_processed

        # Step 4: Determine global reference scale S_ref
        norm_type = (
            normalization
            if isinstance(normalization, CostNormalizationType)
            else CostNormalizationType(normalization)
        )

        if reference_scale is not None and reference_scale > 0.0:
            s_ref = float(reference_scale)
        elif norm_type == CostNormalizationType.DISPATCH_COST:
            s_ref = float(dispatch_cost)
        elif norm_type == CostNormalizationType.MEAN:
            s_ref = float(np.mean(w_raw))
        elif norm_type == CostNormalizationType.MEDIAN:
            s_ref = float(np.median(w_raw))
        elif norm_type == CostNormalizationType.NONE:
            s_ref = 1.0
        else:
            s_ref = float(dispatch_cost)

        # Step 5: Global normalization: w_norm = w_raw / s_ref
        w_norm = w_raw / s_ref

        # Step 6: Generate Provenance and Statistical Audit Records
        provenance = [
            asdict(
                FinancialAuditRecord(
                    parameter_name="dispatch_cost",
                    value=float(dispatch_cost),
                    unit="USD",
                    source_type=DataSourceType.ASSUMED,
                    description="Assumed fixed operational cost C_FP to dispatch physical inspection crew",
                )
            ),
            asdict(
                FinancialAuditRecord(
                    parameter_name="min_fn_cost",
                    value=float(min_fn_cost),
                    unit="USD",
                    source_type=DataSourceType.ASSUMED,
                    description="Assumed minimum floor on positive class error cost",
                )
            ),
            asdict(
                FinancialAuditRecord(
                    parameter_name="estimated_leakage_cost",
                    value="Rolling Deficit x Tariff x Horizon",
                    unit="USD",
                    source_type=DataSourceType.DERIVED,
                    description="Derived revenue leakage from historical consumption collapse",
                )
            ),
            asdict(
                FinancialAuditRecord(
                    parameter_name="reference_scale",
                    value=float(s_ref),
                    unit="USD",
                    source_type=DataSourceType.DERIVED,
                    description=f"Global normalization scale factor (method: {norm_type.value})",
                )
            ),
        ]

        pos_weights_raw = w_raw[pos_mask]
        audit_report = FinancialWeightAuditReport(
            total_samples=n_total,
            positive_samples=n_pos,
            negative_samples=n_neg,
            positive_prevalence=float(n_pos / n_total),
            c_fp_dispatch_cost=float(dispatch_cost),
            c_fn_min=float(np.min(c_fn_raw)),
            c_fn_median=float(np.median(c_fn_raw)),
            c_fn_mean=float(np.mean(c_fn_raw)),
            c_fn_p90=float(np.percentile(c_fn_raw, 90.0)),
            c_fn_p99=float(np.percentile(c_fn_raw, 99.0)),
            c_fn_max=float(np.max(c_fn_raw)),
            weight_min=float(np.min(w_norm)),
            weight_median=float(np.median(w_norm)),
            weight_mean=float(np.mean(w_norm)),
            weight_max=float(np.max(w_norm)),
            weight_ratio_median_pos_to_neg=float(np.median(pos_weights_raw) / dispatch_cost),
            weight_ratio_mean_pos_to_neg=float(np.mean(pos_weights_raw) / dispatch_cost),
            normalization_strategy=norm_type.value,
            reference_scale=float(s_ref),
            cost_capping_applied=cost_capping,
            cost_cap_percentile=cost_cap_percentile if cost_capping else None,
            cost_cap_value=cap_val,
            samples_capped=samples_capped,
            provenance_records=provenance,
        )

        logger.info(
            f"Financial Weights Constructed: N={n_total:,} (Pos={n_pos:,}, Neg={n_neg:,}). "
            f"C_FP=${dispatch_cost:.2f}, C_FN median=${audit_report.c_fn_median:,.2f} "
            f"(ratio={audit_report.weight_ratio_median_pos_to_neg:.1f}:1). "
            f"Normalized via '{norm_type.value}' (scale={s_ref:,.2f}): w_norm in [{audit_report.weight_min:.3f}, {audit_report.weight_max:.3f}]."
        )

        return w_norm, w_raw, audit_report


class FinancialDiagnosticEvaluator:
    """Evaluates expected cost curves and operational ranking metrics across operating points."""

    @staticmethod
    def evaluate_threshold_grid(
        y_true: np.ndarray,
        y_prob: np.ndarray,
        leakage_costs: np.ndarray,
        dispatch_cost: float = 100.0,
        recovery_rate: float = 0.70,
        steps: int = 19,
    ) -> list[dict[str, Any]]:
        """Evaluate business financial outcomes across a diagnostic decision threshold grid.

        Diagnostic only: computes trade-offs for thresholds [0.05, 0.10, ..., 0.95].
        """
        thresholds = np.linspace(0.05, 0.95, steps).tolist()
        y_arr = np.asarray(y_true, dtype=np.int32)
        p_arr = np.asarray(y_prob, dtype=np.float64)
        c_fn_arr = np.asarray(leakage_costs, dtype=np.float64)

        grid_results = []
        for th in thresholds:
            pred = p_arr >= th
            tp = int(np.sum(pred & (y_arr == 1)))
            fp = int(np.sum(pred & (y_arr == 0)))
            fn = int(np.sum((~pred) & (y_arr == 1)))
            tn = int(np.sum((~pred) & (y_arr == 0)))

            fp_dispatch_cost = fp * dispatch_cost
            fn_leakage_cost = float(np.sum(c_fn_arr[(~pred) & (y_arr == 1)]))
            total_loss = fp_dispatch_cost + fn_leakage_cost

            tp_leakage = float(np.sum(c_fn_arr[pred & (y_arr == 1)]))
            gross_recovery = tp_leakage * recovery_rate
            net_recovery = gross_recovery - ((tp + fp) * dispatch_cost)

            prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
            rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0

            grid_results.append(
                {
                    "threshold": round(float(th), 4),
                    "tp": tp,
                    "fp": fp,
                    "fn": fn,
                    "tn": tn,
                    "precision": round(prec, 4),
                    "recall": round(rec, 4),
                    "fp_dispatch_cost": round(fp_dispatch_cost, 2),
                    "fn_leakage_cost": round(fn_leakage_cost, 2),
                    "total_operational_loss": round(total_loss, 2),
                    "gross_recovery": round(gross_recovery, 2),
                    "net_recovery": round(net_recovery, 2),
                }
            )
        return grid_results

    @staticmethod
    def evaluate_top_k_financial(
        y_true: np.ndarray,
        y_prob: np.ndarray,
        leakage_costs: np.ndarray,
        k_values: list[int],
        dispatch_cost: float = 100.0,
        recovery_rate: float = 0.70,
    ) -> dict[str, dict[str, Any]]:
        """Compute cumulative financial recovery and operational precision at top-K capacity."""
        y_arr = np.asarray(y_true, dtype=np.int32)
        p_arr = np.asarray(y_prob, dtype=np.float64)
        c_fn_arr = np.asarray(leakage_costs, dtype=np.float64)

        order = np.argsort(-p_arr)
        y_sorted = y_arr[order]
        leakage_sorted = c_fn_arr[order]

        n_samples = len(y_sorted)
        total_thefts = int(np.sum(y_arr == 1))
        results = {}

        for k in k_values:
            actual_k = min(k, n_samples)
            if actual_k <= 0:
                continue

            top_y = y_sorted[:actual_k]
            top_leakage = leakage_sorted[:actual_k]

            tp = int(np.sum(top_y == 1))
            fp = actual_k - tp
            prec_k = float(tp / actual_k)
            rec_k = float(tp / total_thefts) if total_thefts > 0 else 0.0

            total_dispatch_spent = actual_k * dispatch_cost
            tp_leakage = float(np.sum(top_leakage[top_y == 1]))
            gross_recovered = tp_leakage * recovery_rate
            net_financial_gain = gross_recovered - total_dispatch_spent

            results[str(k)] = {
                "k": actual_k,
                "true_positives": tp,
                "false_positives": fp,
                "precision_at_k": round(prec_k, 4),
                "recall_at_k": round(rec_k, 4),
                "inspection_cost_spent": round(total_dispatch_spent, 2),
                "gross_revenue_recovered": round(gross_recovered, 2),
                "net_financial_value": round(net_financial_gain, 2),
            }

        return results
