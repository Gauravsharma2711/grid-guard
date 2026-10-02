"""Capacity-constrained dispatch policy and quota enforcement."""

from __future__ import annotations

import logging

import numpy as np
import polars as pl

from grid_guard.config.decision import CapacityPolicy

logger = logging.getLogger(__name__)


class CapacityDispatcher:
    """Enforces utility field crew inspection capacity constraints and policies."""

    @staticmethod
    def apply_capacity(
        df_ranked: pl.DataFrame,
        max_inspections: int | None = None,
        policy: CapacityPolicy | str = CapacityPolicy.STRICTLY_POSITIVE_ENV,
        filter_dispatched_only: bool = False,
    ) -> pl.DataFrame:
        """Apply operational capacity constraint and quota policies to a ranked ticket queue.

        Args:
            df_ranked: Polars DataFrame of candidate inspection tickets pre-sorted by ranking strategy.
            max_inspections: Optional hard cap on the number of inspection tickets dispatched.
            policy: Policy rule ('strictly_positive_env' or 'fill_quota').
            filter_dispatched_only: If True, return only dispatched tickets. If False, return all candidate
                                    tickets with 'priority_rank' assigned to dispatched tickets and None otherwise.

        Returns:
            Polars DataFrame with 'priority_rank' column added/updated.
        """
        if df_ranked.is_empty():
            return df_ranked.with_columns(pl.lit(None, dtype=pl.Int32).alias("priority_rank"))

        policy_str = policy.value if isinstance(policy, CapacityPolicy) else str(policy)

        # Step 1: Identify eligible candidates based on policy
        is_rec = df_ranked.get_column("inspection_recommended").to_numpy().astype(bool)
        env_vals = df_ranked.get_column("env").to_numpy().astype(np.float64)

        if policy_str == CapacityPolicy.STRICTLY_POSITIVE_ENV.value:
            # Strictly positive ENV requirement: do NOT dispatch loss-making inspections merely to fill quota
            eligible_mask = is_rec & (env_vals > 0.0)
        elif policy_str == CapacityPolicy.FILL_QUOTA.value:
            eligible_mask = is_rec
        else:
            raise ValueError(
                f"Unknown capacity policy: '{policy}'. Supported: {[p.value for p in CapacityPolicy]}"
            )

        # Step 2: Apply capacity cap to eligible candidates
        eligible_indices = np.where(eligible_mask)[0]
        if max_inspections is not None and max_inspections > 0:
            dispatched_indices = eligible_indices[:max_inspections]
        else:
            dispatched_indices = eligible_indices

        # Step 3: Assign priority ranks (1-indexed for dispatched, None for others)
        ranks: list[int | None] = [None] * len(df_ranked)
        for rank_idx, row_idx in enumerate(dispatched_indices, start=1):
            ranks[row_idx] = rank_idx

        df_out = df_ranked.with_columns(pl.Series("priority_rank", ranks, dtype=pl.Int32))

        logger.info(
            "Capacity constraint evaluated: total=%d, eligible=%d, capacity=%s, dispatched=%d (policy=%s)",
            len(df_ranked),
            len(eligible_indices),
            str(max_inspections),
            len(dispatched_indices),
            policy_str,
        )

        if filter_dispatched_only:
            return df_out.filter(pl.col("priority_rank").is_not_null())

        return df_out
