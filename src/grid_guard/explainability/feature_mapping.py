"""Feature mapping and semantic registry resolution for explainability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from grid_guard.features.pipeline import FeaturePipeline
from grid_guard.features.registry import FeatureDefinition, FeatureRegistry


@dataclass(frozen=True)
class FeatureMetadataInfo:
    """Enriched metadata for an individual feature used in human-facing explanations."""

    feature_name: str
    display_name: str
    category: str
    description: str
    units: str
    lookback_days: int | None
    reference_feature: str | None
    interpretation_hint: str


# Manual human-friendly enhancements for primary features
_FEATURE_DISPLAY_MAP: dict[str, dict[str, Any]] = {
    "consumption_kwh": {
        "display_name": "Current Day Observed Consumption",
        "category": "Recent Consumption",
        "description": "Raw metered electrical consumption on evaluation date",
        "units": "kWh",
        "lookback_days": 1,
        "reference_feature": "rolling_mean_30d",
        "interpretation_hint": "Low current consumption relative to baseline increases suspicion",
    },
    "rolling_std_60d": {
        "display_name": "60-Day Historical Consumption Volatility",
        "category": "Historical Baseline",
        "description": "Trailing 60-day standard deviation reflecting normal customer load variability",
        "units": "kWh",
        "lookback_days": 60,
        "reference_feature": "rolling_std_30d",
        "interpretation_hint": "High historical volatility combined with recent collapse signals anomaly",
    },
    "rolling_std_30d": {
        "display_name": "30-Day Trailing Consumption Volatility",
        "category": "Historical Baseline",
        "description": "Trailing 30-day standard deviation of daily consumption",
        "units": "kWh",
        "lookback_days": 30,
        "reference_feature": "rolling_std_60d",
        "interpretation_hint": "Sharp drop in volatility indicates artificial flatlining or zero usage",
    },
    "rolling_std_90d": {
        "display_name": "90-Day Seasonal Consumption Volatility",
        "category": "Historical Baseline",
        "description": "Long-term 90-day standard deviation of daily consumption",
        "units": "kWh",
        "lookback_days": 90,
        "reference_feature": None,
        "interpretation_hint": "Long-term historical dispersion benchmark",
    },
    "rolling_mean_60d": {
        "display_name": "60-Day Historical Baseline Average",
        "category": "Historical Baseline",
        "description": "Trailing 60-day average daily electricity usage",
        "units": "kWh/day",
        "lookback_days": 60,
        "reference_feature": None,
        "interpretation_hint": "Long-term usage baseline against which current load is measured",
    },
    "rolling_mean_30d": {
        "display_name": "30-Day Trailing Consumption Average",
        "category": "Historical Baseline",
        "description": "Trailing 30-day average daily electricity usage",
        "units": "kWh/day",
        "lookback_days": 30,
        "reference_feature": "rolling_mean_60d",
        "interpretation_hint": "Medium-term usage level",
    },
    "rolling_mean_14d": {
        "display_name": "14-Day Trailing Consumption Average",
        "category": "Recent Consumption",
        "description": "Trailing 14-day average daily electricity usage",
        "units": "kWh/day",
        "lookback_days": 14,
        "reference_feature": "rolling_mean_60d",
        "interpretation_hint": "Recent two-week usage level",
    },
    "rolling_mean_7d": {
        "display_name": "7-Day Trailing Consumption Average",
        "category": "Recent Consumption",
        "description": "Trailing 7-day average daily electricity usage",
        "units": "kWh/day",
        "lookback_days": 7,
        "reference_feature": "rolling_mean_30d",
        "interpretation_hint": "Short-term one-week usage level",
    },
    "ratio_14d_60d": {
        "display_name": "Recent vs. Historical Consumption Ratio (14d / 60d)",
        "category": "Consumption Collapse & Step-Down",
        "description": "Ratio of recent 14-day average consumption to 60-day historical baseline",
        "units": "ratio",
        "lookback_days": 60,
        "reference_feature": "rolling_mean_60d",
        "interpretation_hint": "Values well below 1.0 (e.g. <0.50) indicate severe consumption collapse",
    },
    "ratio_7d_30d": {
        "display_name": "Short-Term vs. Monthly Ratio (7d / 30d)",
        "category": "Consumption Collapse & Step-Down",
        "description": "Ratio of trailing 7-day usage to trailing 30-day usage",
        "units": "ratio",
        "lookback_days": 30,
        "reference_feature": "rolling_mean_30d",
        "interpretation_hint": "Depressed ratio reveals sudden drop in the past week",
    },
    "ratio_30d_90d": {
        "display_name": "Monthly vs. Seasonal Ratio (30d / 90d)",
        "category": "Consumption Collapse & Step-Down",
        "description": "Ratio of 30-day average usage to 90-day seasonal baseline",
        "units": "ratio",
        "lookback_days": 90,
        "reference_feature": "rolling_mean_90d",
        "interpretation_hint": "Captures extended multi-week consumption shifts",
    },
    "sustained_drop_magnitude": {
        "display_name": "Estimated Consumption Collapse Magnitude",
        "category": "Consumption Collapse & Step-Down",
        "description": "Absolute deficit between 60-day baseline and recent 14-day average",
        "units": "kWh/day",
        "lookback_days": 74,
        "reference_feature": "rolling_mean_60d",
        "interpretation_hint": "Higher unmetered volume deficit directly escalates financial risk",
    },
    "sustained_drop_ratio": {
        "display_name": "Fractional Consumption Deficit",
        "category": "Consumption Collapse & Step-Down",
        "description": "Percentage decline from historical baseline: max(0, 1 - recent/baseline)",
        "units": "fraction",
        "lookback_days": 74,
        "reference_feature": "rolling_mean_60d",
        "interpretation_hint": "Values approaching 1.0 indicate near-total consumption disappearance",
    },
    "sustained_drop_duration": {
        "display_name": "Sustained Low-Usage Streak",
        "category": "Consumption Collapse & Step-Down",
        "description": "Consecutive days where consumption remains <50% of historical baseline",
        "units": "days",
        "lookback_days": 74,
        "reference_feature": None,
        "interpretation_hint": "Longer durations rule out transient temporary dips",
    },
    "baseline_deviation_ratio": {
        "display_name": "Baseline Deviation Ratio",
        "category": "Consumption Collapse & Step-Down",
        "description": "Ratio of recent 14-day consumption to pre-period 60-day historical baseline",
        "units": "ratio",
        "lookback_days": 74,
        "reference_feature": "rolling_mean_60d",
        "interpretation_hint": "Values <1.0 indicate structural reduction below baseline",
    },
    "zero_count_7d": {
        "display_name": "Zero-Consumption Days in Past Week",
        "category": "Zero Consumption & Streaks",
        "description": "Count of days with zero or near-zero consumption over trailing 7 days",
        "units": "days",
        "lookback_days": 7,
        "reference_feature": None,
        "interpretation_hint": "Multiple zero days indicate prolonged circuit disconnections",
    },
    "zero_count_30d": {
        "display_name": "Zero-Consumption Days in Past Month",
        "category": "Zero Consumption & Streaks",
        "description": "Count of days with zero or near-zero consumption over trailing 30 days",
        "units": "days",
        "lookback_days": 30,
        "reference_feature": None,
        "interpretation_hint": "Persistent zero days across a billing cycle",
    },
    "current_zero_streak": {
        "display_name": "Current Consecutive Zero Days",
        "category": "Zero Consumption & Streaks",
        "description": "Consecutive active days recording zero electricity consumption",
        "units": "days",
        "lookback_days": None,
        "reference_feature": None,
        "interpretation_hint": "Extended active zero streaks are primary indicators of complete meter bypass",
    },
    "flatline_streak": {
        "display_name": "Current Near-Constant Consumption Streak",
        "category": "Variability & Flatline",
        "description": "Consecutive days with identical or near-identical consumption",
        "units": "days",
        "lookback_days": None,
        "reference_feature": None,
        "interpretation_hint": "Unnatural absence of natural human load fluctuations",
    },
    "rolling_cv_7d": {
        "display_name": "7-Day Coefficient of Variation",
        "category": "Variability & Flatline",
        "description": "Relative volatility of daily consumption over past 7 days (std / mean)",
        "units": "ratio",
        "lookback_days": 7,
        "reference_feature": "rolling_cv_30d",
        "interpretation_hint": "Near-zero values indicate flatline behavior",
    },
    "daily_diff_abs_7d_mean": {
        "display_name": "7-Day Mean Day-to-Day Absolute Change",
        "category": "Variability & Flatline",
        "description": "Average magnitude of day-to-day consumption changes over trailing week",
        "units": "kWh",
        "lookback_days": 7,
        "reference_feature": "daily_diff_abs_30d_mean",
        "interpretation_hint": "Drop in daily fluctuations indicates loss of natural variance",
    },
    "coverage_ratio": {
        "display_name": "Smart-Meter Data Coverage Ratio",
        "category": "Data Quality & Completeness",
        "description": "Proportion of valid non-null AMI readings received from this meter",
        "units": "ratio",
        "lookback_days": 90,
        "reference_feature": None,
        "interpretation_hint": "High coverage (>0.95) confirms anomalies are genuine rather than telecommunication outages",
    },
    "missing_ratio": {
        "display_name": "Data Missingness Ratio",
        "category": "Data Quality & Completeness",
        "description": "Proportion of missing AMI packets in the historical window",
        "units": "ratio",
        "lookback_days": 90,
        "reference_feature": None,
        "interpretation_hint": "Low missingness verifies signal integrity",
    },
    "imputation_ratio": {
        "display_name": "Imputed Data Ratio",
        "category": "Data Quality & Completeness",
        "description": "Fraction of consumption records restored via bounded-gap imputation",
        "units": "ratio",
        "lookback_days": 90,
        "reference_feature": None,
        "interpretation_hint": "Low ratio confirms model relies on measured telemetry rather than estimates",
    },
    "consumption_kwh_lag_30d": {
        "display_name": "Consumption 30 Days Prior",
        "category": "Historical Baseline",
        "description": "Observed consumption exactly one billing month prior",
        "units": "kWh",
        "lookback_days": 30,
        "reference_feature": "consumption_kwh",
        "interpretation_hint": "Substantial drop from same-time last month signals sudden behavioral change",
    },
}


class FeatureMapper:
    """Resolves technical feature names into human-understandable metadata and descriptions."""

    def __init__(self, registry: FeatureRegistry | None = None) -> None:
        """Initialize with existing registry or build canonical pipeline registry."""
        if registry is None:
            pipeline = FeaturePipeline()
            self.registry = pipeline.registry
        else:
            self.registry = registry

    def resolve(self, feature_name: str) -> FeatureMetadataInfo:
        """Resolve rich metadata for a given feature name."""
        # 1. Check curated high-priority map first
        if feature_name in _FEATURE_DISPLAY_MAP:
            info = _FEATURE_DISPLAY_MAP[feature_name]
            return FeatureMetadataInfo(
                feature_name=feature_name,
                display_name=info["display_name"],
                category=info["category"],
                description=info["description"],
                units=info["units"],
                lookback_days=info["lookback_days"],
                reference_feature=info["reference_feature"],
                interpretation_hint=info["interpretation_hint"],
            )

        # 2. Check Phase 3 FeatureRegistry
        def_obj: FeatureDefinition | None = self.registry.get(feature_name)
        if def_obj is not None:
            category_title = def_obj.category.value.replace("_", " ").title()
            display_title = feature_name.replace("_", " ").title()
            return FeatureMetadataInfo(
                feature_name=feature_name,
                display_name=display_title,
                category=category_title,
                description=def_obj.description,
                units="kWh" if "mean" in feature_name or "std" in feature_name else "unitless",
                lookback_days=def_obj.window_days,
                reference_feature=None,
                interpretation_hint="Engineered temporal feature contributing to model risk",
            )

        # 3. Fallback generic representation
        clean_name = feature_name.replace("_", " ").title()
        return FeatureMetadataInfo(
            feature_name=feature_name,
            display_name=clean_name,
            category="Other Feature",
            description=f"Model input feature '{feature_name}'",
            units="unitless",
            lookback_days=None,
            reference_feature=None,
            interpretation_hint="Feature contribution evaluated by tree booster",
        )
