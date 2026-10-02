"""Publication-grade visualization utilities for SHAP explainability and case studies."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Grid-Guard publication palette
GRID_GUARD_COLORS = {
    "primary": "#1f77b4",
    "secondary": "#ff7f0e",
    "positive_risk": "#d62728",  # Red for risk-increasing
    "negative_risk": "#2ca02c",  # Green for risk-decreasing / counter-evidence
    "baseline": "#7f7f7f",
    "neutral": "#333333",
    "accent": "#9467bd",
    "grid": "#e0e0e0",
}

CATEGORY_COLORS = {
    "Historical Baseline": "#1f77b4",
    "Consumption Collapse & Step-Down": "#d62728",
    "Recent Consumption": "#ff7f0e",
    "Variability & Flatline": "#9467bd",
    "Zero Consumption & Streaks": "#8c564b",
    "Data Quality & Completeness": "#2ca02c",
    "Calendar & Seasonality": "#e377c2",
    "Other Feature": "#7f7f7f",
}


class ExplainabilityVisualizer:
    """Generates professional diagnostic plots for model explainability."""

    def __init__(self, output_dir: Path | str) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Apply standard clean styling
        plt.rcParams.update(
            {
                "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
                "font.size": 10,
                "axes.titlesize": 12,
                "axes.labelsize": 11,
                "xtick.labelsize": 9,
                "ytick.labelsize": 9,
                "figure.titlesize": 14,
                "figure.dpi": 300,
            }
        )

    def plot_global_importance(
        self,
        importance_records: list[dict[str, Any]],
        top_n: int = 15,
        filename: str = "global_shap_importance.png",
    ) -> Path:
        """Plot horizontal bar chart of global feature importance ranked by mean(|SHAP|)."""
        top_records = importance_records[:top_n]
        top_records.reverse()  # For ascending vertical plot

        display_names = [r["display_name"] for r in top_records]
        mean_abs_values = [r["mean_abs_shap"] for r in top_records]
        categories = [r["category"] for r in top_records]
        bar_colors = [CATEGORY_COLORS.get(cat, "#1f77b4") for cat in categories]

        fig, ax = plt.subplots(figsize=(10, 7))
        bars = ax.barh(
            display_names,
            mean_abs_values,
            color=bar_colors,
            alpha=0.85,
            edgecolor="none",
            height=0.65,
        )

        # Annotate values
        for bar in bars:
            width = bar.get_width()
            ax.text(
                width + max(mean_abs_values) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{width:.3f}",
                va="center",
                ha="left",
                fontsize=9,
                color="#333333",
                fontweight="bold",
            )

        ax.set_xlabel("Mean Absolute SHAP Value (Log-Odds Impact: E[|phi_i|])", fontweight="bold")
        ax.set_title(
            "Global Feature Importance (TreeExplainer on Cost-Sensitive LightGBM)",
            fontweight="bold",
            pad=15,
        )
        ax.grid(axis="x", linestyle="--", alpha=0.5, color=GRID_GUARD_COLORS["grid"])
        ax.set_xlim(0, max(mean_abs_values) * 1.15)

        # Category legend
        unique_cats = list(dict.fromkeys(categories))
        legend_elements = [
            plt.Rectangle((0, 0), 1, 1, facecolor=CATEGORY_COLORS.get(c, "#1f77b4"), label=c)
            for c in unique_cats
        ]
        ax.legend(
            handles=legend_elements, title="Feature Category", loc="lower right", framealpha=0.9
        )

        plt.tight_layout()
        out_path = self.output_dir / filename
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Saved global SHAP importance plot to {out_path}")
        return out_path

    def plot_category_attribution(
        self,
        importance_records: list[dict[str, Any]],
        filename: str = "category_attribution_pie_bar.png",
    ) -> Path:
        """Plot aggregate SHAP contribution grouped by high-level feature category."""
        category_sums: dict[str, float] = {}
        for r in importance_records:
            cat = r["category"]
            category_sums[cat] = category_sums.get(cat, 0.0) + r["mean_abs_shap"]

        # Sort categories descending
        sorted_cats = sorted(category_sums.items(), key=lambda x: x[1], reverse=True)
        cat_names = [x[0] for x in sorted_cats]
        cat_values = [x[1] for x in sorted_cats]
        total_val = sum(cat_values)
        cat_pcts = [(v / total_val) * 100.0 for v in cat_values]
        colors = [CATEGORY_COLORS.get(c, "#1f77b4") for c in cat_names]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Donut Chart
        wedges, texts, autotexts = ax1.pie(
            cat_values,
            labels=None,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            pctdistance=0.75,
            wedgeprops={"width": 0.45, "edgecolor": "white", "linewidth": 2},
        )
        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_fontweight("bold")
        ax1.set_title("Relative Category Attribution (%)", fontweight="bold")

        # Bar chart
        y_pos = np.arange(len(cat_names))
        ax2.barh(y_pos, cat_values, color=colors, alpha=0.85, height=0.6)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(cat_names)
        ax2.invert_yaxis()
        ax2.set_xlabel("Total Summed Mean(|SHAP|)", fontweight="bold")
        ax2.set_title("Absolute Cumulative Category Impact", fontweight="bold")
        ax2.grid(axis="x", linestyle="--", alpha=0.5, color=GRID_GUARD_COLORS["grid"])

        for i, v in enumerate(cat_values):
            ax2.text(
                v + max(cat_values) * 0.02,
                i,
                f"{v:.2f} ({cat_pcts[i]:.1f}%)",
                va="center",
                fontsize=9,
            )

        plt.suptitle(
            "Grid-Guard Behavioral Feature Category Attribution",
            fontsize=14,
            fontweight="bold",
            y=1.02,
        )
        plt.tight_layout()
        out_path = self.output_dir / filename
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Saved category attribution plot to {out_path}")
        return out_path

    def plot_local_case_study(
        self,
        case_name: str,
        ticket_id: str,
        meter_id: str,
        probability: float,
        env: float | None,
        base_value: float,
        raw_score: float,
        positive_drivers: list[dict[str, Any]],
        negative_drivers: list[dict[str, Any]],
        filename: str,
    ) -> Path:
        """Plot local waterfall/contribution breakdown for an individual inspection candidate."""
        # Combine drivers
        drivers = []
        for d in positive_drivers[:5]:
            drivers.append((d["display_name"], d["shap_value"], GRID_GUARD_COLORS["positive_risk"]))
        for d in negative_drivers[:3]:
            drivers.append((d["display_name"], d["shap_value"], GRID_GUARD_COLORS["negative_risk"]))

        # Sort by signed SHAP value
        drivers.sort(key=lambda x: x[1])

        names = [d[0] for d in drivers]
        values = [d[1] for d in drivers]
        colors = [d[2] for d in drivers]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(names, values, color=colors, alpha=0.85, height=0.6)

        ax.axvline(0, color="black", linestyle="-", linewidth=1.0)
        ax.set_xlabel("SHAP Contribution to Log-Odds Margin (phi_i)", fontweight="bold")

        env_str = f" | ENV: ${env:,.2f}" if env is not None else ""
        ax.set_title(
            f"Local Attribution: {case_name}\n"
            f"Ticket: {ticket_id} (Meter: {meter_id[:12]}...) | Prob: {probability:.3f} (Log-Odds: {raw_score:+.2f}){env_str}",
            fontweight="bold",
            pad=12,
        )
        ax.grid(axis="x", linestyle="--", alpha=0.5, color=GRID_GUARD_COLORS["grid"])

        for bar in bars:
            width = bar.get_width()
            offset = 0.05 if width >= 0 else -0.05
            ha = "left" if width >= 0 else "right"
            ax.text(
                width + offset,
                bar.get_y() + bar.get_height() / 2,
                f"{width:+.3f}",
                va="center",
                ha=ha,
                fontsize=9,
                fontweight="bold",
                color="#333333",
            )

        # Legend
        pos_rect = plt.Rectangle(
            (0, 0),
            1,
            1,
            facecolor=GRID_GUARD_COLORS["positive_risk"],
            label="Increases Tampering Risk",
        )
        neg_rect = plt.Rectangle(
            (0, 0),
            1,
            1,
            facecolor=GRID_GUARD_COLORS["negative_risk"],
            label="Decreases Risk (Counter-Evidence)",
        )
        ax.legend(handles=[pos_rect, neg_rect], loc="lower right", framealpha=0.9)

        plt.tight_layout()
        out_path = self.output_dir / filename
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Saved local case study plot to {out_path}")
        return out_path

    def plot_time_series_signature(
        self,
        meter_id: str,
        dates: list[str],
        actual_consumption: list[float],
        rolling_baseline_60d: list[float] | None,
        anomaly_start_date: str | None,
        anomaly_end_date: str | None,
        signature_label: str,
        filename: str = "case_study_timeseries.png",
    ) -> Path:
        """Plot daily time-series with historical baseline and highlighted signature window."""
        df = pd.DataFrame({"date": pd.to_datetime(dates), "consumption": actual_consumption})
        if rolling_baseline_60d is not None:
            df["baseline"] = rolling_baseline_60d
        df = df.sort_values("date")

        fig, ax = plt.subplots(figsize=(13, 6))

        # Plot actual consumption
        ax.plot(
            df["date"],
            df["consumption"],
            color="#2b5c8f",
            linewidth=1.2,
            label="Actual Daily Consumption (kWh)",
        )

        # Plot 60-day baseline if available
        if "baseline" in df.columns:
            ax.plot(
                df["date"],
                df["baseline"],
                color="#e6550d",
                linestyle="--",
                linewidth=1.8,
                label="60-Day Historical Baseline",
            )

        # Highlight anomaly signature region
        if anomaly_start_date and anomaly_end_date:
            t_start = pd.to_datetime(anomaly_start_date)
            t_end = pd.to_datetime(anomaly_end_date)
            ax.axvspan(
                t_start,
                t_end,
                color="#d62728",
                alpha=0.18,
                label=f"Signature Window: {signature_label}",
            )
            ax.text(
                t_start + (t_end - t_start) / 2,
                max(actual_consumption) * 0.85,
                signature_label,
                color="#b2182b",
                fontweight="bold",
                ha="center",
                bbox={
                    "boxstyle": "round,pad=0.4",
                    "facecolor": "white",
                    "edgecolor": "#b2182b",
                    "alpha": 0.9,
                },
            )

        ax.set_xlabel("Date", fontweight="bold")
        ax.set_ylabel("Electricity Consumption (kWh/day)", fontweight="bold")
        ax.set_title(
            f"Temporal Signature Case Study: Meter `{meter_id}`\n"
            "Pre-Period Normal Load vs. Post-Tampering Consumption Collapse",
            fontweight="bold",
            pad=15,
        )
        ax.grid(True, linestyle="--", alpha=0.4, color=GRID_GUARD_COLORS["grid"])
        ax.legend(loc="upper right", framealpha=0.9)

        plt.tight_layout()
        out_path = self.output_dir / filename
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Saved time-series signature plot to {out_path}")
        return out_path
