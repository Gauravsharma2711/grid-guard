"""Temporal source attribution mapping engineered features to historical calendar intervals."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from grid_guard.explainability.feature_mapping import FeatureMapper
from grid_guard.explainability.schemas import TemporalEvidence


class TemporalAttributor:
    """Builds explicit, verifiable historical calendar intervals for engineered features."""

    def __init__(self, feature_mapper: FeatureMapper | None = None) -> None:
        self.feature_mapper = feature_mapper or FeatureMapper()

    @staticmethod
    def _parse_date(date_val: str | date) -> date:
        """Parse input date into standard date object."""
        if isinstance(date_val, date):
            return date_val
        return date.fromisoformat(str(date_val).split("T")[0])

    def attribute(
        self,
        feature_name: str,
        anchor_date: str | date,
        observed_value: float,
        shap_contribution: float,
        feature_values_row: dict[str, Any] | None = None,
    ) -> TemporalEvidence:
        """Derive explicit temporal evidence window and comparison for a feature."""
        anchor = self._parse_date(anchor_date)
        meta = self.feature_mapper.resolve(feature_name)
        feat_map = feature_values_row or {}

        # 1. Determine calendar window based on feature structure
        start_date = anchor
        end_date = anchor
        ref_value: float | None = None
        rel_diff_pct: float | None = None
        interpretation = meta.interpretation_hint

        # Case A: Multi-scale ratios (e.g. ratio_14d_60d, sustained_drop_magnitude)
        if (
            "14d_60d" in feature_name
            or "sustained_drop" in feature_name
            or "baseline_deviation" in feature_name
        ):
            start_date = anchor - timedelta(days=59)
            end_date = anchor
            recent_val = feat_map.get("rolling_mean_14d", observed_value)
            base_val = feat_map.get("rolling_mean_60d")
            if base_val is not None and base_val > 1e-4:
                ref_value = float(base_val)
                rel_diff_pct = round(((float(recent_val) - ref_value) / ref_value) * 100.0, 1)
                drop_pct = abs(rel_diff_pct) if rel_diff_pct < 0 else 0.0
                interpretation = (
                    f"Recent 14-day average ({float(recent_val):.2f} kWh/day) is "
                    f"{drop_pct:.1f}% below 60-day baseline ({ref_value:.2f} kWh/day) "
                    f"observed between {anchor - timedelta(days=59)} and {anchor}."
                )

        # Case B: Short-term ratios (e.g. ratio_7d_30d)
        elif "7d_30d" in feature_name:
            start_date = anchor - timedelta(days=29)
            end_date = anchor
            recent_val = feat_map.get("rolling_mean_7d", observed_value)
            base_val = feat_map.get("rolling_mean_30d")
            if base_val is not None and base_val > 1e-4:
                ref_value = float(base_val)
                rel_diff_pct = round(((float(recent_val) - ref_value) / ref_value) * 100.0, 1)
                interpretation = (
                    f"Trailing 7-day average ({float(recent_val):.2f} kWh/day) dropped "
                    f"{abs(rel_diff_pct):.1f}% relative to 30-day baseline ({ref_value:.2f} kWh/day)."
                )

        # Case C: Rolling statistics (e.g. rolling_std_60d, rolling_mean_60d)
        elif "60d" in feature_name:
            start_date = anchor - timedelta(days=59)
            end_date = anchor
            if "std" in feature_name and "rolling_std_30d" in feat_map:
                ref_value = float(feat_map["rolling_std_30d"])
            elif "mean" in feature_name and "rolling_mean_30d" in feat_map:
                ref_value = float(feat_map["rolling_mean_30d"])

        elif "30d" in feature_name:
            start_date = anchor - timedelta(days=29)
            end_date = anchor
            if "lag" in feature_name:
                start_date = anchor - timedelta(days=30)
                end_date = anchor - timedelta(days=30)
                ref_value = float(feat_map.get("consumption_kwh", observed_value))

        elif "14d" in feature_name:
            start_date = anchor - timedelta(days=13)
            end_date = anchor

        elif "7d" in feature_name:
            start_date = anchor - timedelta(days=6)
            end_date = anchor

        # Case D: Active streaks (zero streak, flatline streak)
        elif "streak" in feature_name:
            streak_days = max(1, int(round(observed_value)))
            start_date = anchor - timedelta(days=streak_days - 1)
            end_date = anchor
            interpretation = (
                f"Continuous streak of {streak_days} days detected from "
                f"{start_date.isoformat()} through {end_date.isoformat()}."
            )

        # Case E: Current day consumption
        elif feature_name == "consumption_kwh":
            start_date = anchor
            end_date = anchor
            base_val = feat_map.get("rolling_mean_30d")
            if base_val is not None and base_val > 1e-4:
                ref_value = float(base_val)
                rel_diff_pct = round(((observed_value - ref_value) / ref_value) * 100.0, 1)

        # Calculate relative diff if ref_value exists and not yet set
        if ref_value is not None and rel_diff_pct is None and abs(ref_value) > 1e-4:
            rel_diff_pct = round(((observed_value - ref_value) / abs(ref_value)) * 100.0, 1)

        return TemporalEvidence(
            anchor_date=anchor.isoformat(),
            source_window_start=start_date.isoformat(),
            source_window_end=end_date.isoformat(),
            feature_name=feature_name,
            display_name=meta.display_name,
            observed_value=float(observed_value),
            reference_value=ref_value,
            relative_difference_pct=rel_diff_pct,
            shap_contribution=float(shap_contribution),
            interpretation=interpretation,
        )
