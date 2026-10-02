"""Configuration models for class imbalance experimentation and rare-theft learning."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ImbalanceStrategyType(StrEnum):
    """Supported class imbalance mitigation strategies."""

    UNWEIGHTED = "unweighted"
    CLASS_WEIGHT = "class_weight"
    CONTROLLED_OVERSAMPLE = "controlled_oversample"
    CONTROLLED_UNDERSAMPLE = "controlled_undersample"
    SMOTE = "smote"


class ImbalanceSettings(BaseModel):
    """Configuration parameters for rare-theft learning and class imbalance mitigation."""

    strategy: ImbalanceStrategyType = ImbalanceStrategyType.CLASS_WEIGHT
    class_weight_multiplier: float = (
        1.0  # Multiplier on inverse-frequency weight (or explicit ratio)
    )
    target_pos_ratio: float = 0.20  # Target positive-to-negative ratio for sampling
    selection_metric: str = "pr_auc"  # Metric used to select champion strategy on validation set
    threshold: float = 0.5  # Conventional decision threshold
    random_seed: int = 42

    # Sensitivity grid parameters for validation exploration
    weight_multipliers: list[float] = Field(default_factory=lambda: [1.0, 2.0, 3.0, 5.0, 10.72])
    oversample_ratios: list[float] = Field(default_factory=lambda: [0.15, 0.25, 0.50])
    undersample_ratios: list[float] = Field(default_factory=lambda: [0.20, 0.33, 0.50])

    # SMOTE parameters
    smote_k_neighbors: int = 5
    smote_sample_size_cap: int = 50000  # Safe cap to avoid combinatorial explosion on dense memory
