"""Financial cost assumptions and baseline modeling configuration models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FinancialAssumptions(BaseModel):
    """Financial parameters for evaluating inspection costs and revenue leakage."""

    currency: str = "USD"
    dispatch_cost: float = 100.0  # C_dispatch: field inspection crew dispatch cost
    default_tariff: float = 0.15  # Cost per kWh if dataset lacks tariff metadata
    tariff_source: str = "assumed_fallback"  # observed, derived, or assumed_fallback
    undetected_cycles: int = 12  # Number of monthly billing cycles theft continues undetected
    leakage_window_days: int = 30  # Baseline window for estimating monthly leakage volume
    min_leakage_kwh: float = 5.0  # Minimum daily deficit to classify as material leakage


class BaselineModelSettings(BaseModel):
    """Configuration for unweighted LightGBM baseline model training and temporal splitting."""

    model_type: str = "lightgbm"
    target_col: str = "tamper_label"
    objective: str = "binary"
    metric: str = "binary_logloss"
    learning_rate: float = 0.05
    n_estimators: int = 200
    max_depth: int = 6
    num_leaves: int = 31
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    random_state: int = 42
    threshold: float = 0.5  # Conventional unweighted threshold
    sampling_stride_days: int = 30  # Periodic snapshot sampling interval in days

    # Strict temporal split dates
    train_start: str = "2014-04-01"  # After 90-day feature warm-up
    train_end: str = "2015-12-31"
    val_start: str = "2016-01-01"
    val_end: str = "2016-05-31"
    test_start: str = "2016-06-01"
    test_end: str = "2016-10-31"

    top_k_values: list[int] = Field(default_factory=lambda: [10, 50, 100, 500, 1000, 2000])
