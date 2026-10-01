"""Central Feature Registry for Grid-Guard AMI Temporal Features."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


class FeatureCategory(StrEnum):
    """Categorization of engineered temporal features."""

    CALENDAR = "calendar"
    LAG = "lag"
    ROLLING = "rolling"
    RATIO = "ratio"
    VARIABILITY = "variability"
    PEAK = "peak"
    AUTOCORRELATION = "autocorrelation"
    BEHAVIOR_SHIFT = "behavior_shift"
    ZERO_STREAK = "zero_streak"
    STEP_DOWN = "step_down"
    PEER_CONTEXT = "peer_context"
    DATA_QUALITY = "data_quality"


class LeakageRisk(StrEnum):
    """Audit classification for future-data leakage risk."""

    SAFE = "safe"  # Strictly trailing backward transformation (<= t)
    WARMUP_DEPENDENT = (
        "warmup_dependent"  # Trailing lookback requiring historical window; null during warm-up
    )
    CONTEXT_DEPENDENT = (
        "context_dependent"  # Group/peer aggregate; leave-one-out to prevent self-reference
    )


@dataclass(frozen=True)
class FeatureDefinition:
    """Metadata specification for an individual engineered feature."""

    name: str
    category: FeatureCategory
    source_columns: tuple[str, ...]
    window_days: int | None
    lag_days: int | None
    description: str
    dtype: str = "Float32"
    leakage_risk: LeakageRisk = LeakageRisk.SAFE
    min_history_days: int = 1
    requires_context: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert definition to dictionary representation."""
        data = asdict(self)
        data["category"] = self.category.value
        data["leakage_risk"] = self.leakage_risk.value
        data["source_columns"] = list(self.source_columns)
        return data


class FeatureRegistry:
    """Central registry tracking all engineered features in the pipeline."""

    def __init__(self) -> None:
        self._registry: dict[str, FeatureDefinition] = {}

    def register(self, feature: FeatureDefinition) -> FeatureDefinition:
        """Register a new feature definition.

        Args:
            feature: Feature definition to register.

        Returns:
            The registered feature definition.

        Raises:
            ValueError: If feature name is already registered with differing metadata.
        """
        if feature.name in self._registry and self._registry[feature.name] != feature:
            raise ValueError(
                f"Feature '{feature.name}' already registered with conflicting definition."
            )
        self._registry[feature.name] = feature
        return feature

    def get(self, name: str) -> FeatureDefinition | None:
        """Retrieve definition for a registered feature."""
        return self._registry.get(name)

    def list_features(self) -> list[FeatureDefinition]:
        """Return all registered features in insertion order."""
        return list(self._registry.values())

    def by_category(self, category: FeatureCategory | str) -> list[FeatureDefinition]:
        """Filter registered features by category."""
        target = category.value if isinstance(category, FeatureCategory) else category
        return [f for f in self._registry.values() if f.category.value == target]

    def count(self) -> int:
        """Return total number of registered features."""
        return len(self._registry)

    def to_dict(self) -> dict[str, Any]:
        """Export complete registry as a dictionary."""
        return {
            "total_features": len(self._registry),
            "features_by_category": {
                cat.value: len(self.by_category(cat)) for cat in FeatureCategory
            },
            "features": [f.to_dict() for f in self._registry.values()],
        }

    def export_json(self, output_path: Path | str) -> None:
        """Serialize feature registry metadata to JSON file."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    def export_markdown(self, output_path: Path | str) -> None:
        """Generate human-readable markdown feature dictionary."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# Grid-Guard Feature Dictionary",
            "",
            "This document provides the authoritative registry of all temporal features ",
            "and tampering signatures extracted from smart-meter AMI time series.",
            "",
            f"**Total Features Registered**: {len(self._registry)}",
            "",
            "## Summary by Category",
            "",
            "| Category | Count | Description |",
            "|---|---|---|",
            "| Calendar | "
            + str(len(self.by_category(FeatureCategory.CALENDAR)))
            + " | Day-of-week, month, cyclical harmonic representations |",
            "| Lag | "
            + str(len(self.by_category(FeatureCategory.LAG)))
            + " | Historical backward observation lags (1d, 7d, etc.) |",
            "| Rolling | "
            + str(len(self.by_category(FeatureCategory.ROLLING)))
            + " | Trailing window statistics (mean, std, min, max) |",
            "| Ratio | "
            + str(len(self.by_category(FeatureCategory.RATIO)))
            + " | Multi-scale moving average ratios (e.g. 7d/30d, 14d/60d) |",
            "| Peak | "
            + str(len(self.by_category(FeatureCategory.PEAK)))
            + " | Peak-to-Average Ratios (PAR) over trailing windows |",
            "| Behavior Shift | "
            + str(len(self.by_category(FeatureCategory.BEHAVIOR_SHIFT)))
            + " | Week-over-week consumption and volatility shifts |",
            "| Zero Streak | "
            + str(len(self.by_category(FeatureCategory.ZERO_STREAK)))
            + " | Zero-consumption counts, ratios, and streak tracking |",
            "| Variability | "
            + str(len(self.by_category(FeatureCategory.VARIABILITY)))
            + " | Rolling coefficient of variation and flatline indicators |",
            "| Step Down | "
            + str(len(self.by_category(FeatureCategory.STEP_DOWN)))
            + " | Sustained collapse from historical baseline & duration |",
            "| Autocorrelation | "
            + str(len(self.by_category(FeatureCategory.AUTOCORRELATION)))
            + " | Weekly lag correlation & personal DOW profile deviation |",
            "| Peer Context | "
            + str(len(self.by_category(FeatureCategory.PEER_CONTEXT)))
            + " | Feeder/neighborhood group divergence (where metadata exists) |",
            "| Data Quality | "
            + str(len(self.by_category(FeatureCategory.DATA_QUALITY)))
            + " | Coverage, missingness, and data-quality status indicators |",
            "",
            "---",
            "",
            "## Feature Specifications",
            "",
            "| Feature Name | Category | Window | Lag | Dtype | Leakage Risk | Description |",
            "|---|---|---|---|---|---|---|",
        ]

        for f in self._registry.values():
            w = f"{f.window_days}d" if f.window_days else "-"
            lag = f"{f.lag_days}d" if f.lag_days else "-"
            lines.append(
                f"| `{f.name}` | {f.category.value} | {w} | {lag} | "
                f"`{f.dtype}` | {f.leakage_risk.value} | {f.description} |"
            )

        with open(target, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
