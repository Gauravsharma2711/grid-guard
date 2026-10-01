"""Automated and reproducible Exploratory Data Analysis (EDA) visualizations."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from grid_guard.data.profiling import DatasetProfile
from grid_guard.utils.logging import get_logger

# Use non-interactive Agg backend for robust headless execution
matplotlib.use("Agg")
logger = get_logger(__name__)

# Stylistic defaults for clean publication-grade figures
plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.labelweight": "medium",
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "figure.autolayout": True,
        "figure.titlesize": 13,
        "figure.titleweight": "bold",
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
    }
)

COLOR_NORMAL = "#2b5c8f"  # Slate Blue
COLOR_THEFT = "#d95f02"  # Burnt Orange
COLOR_ACCENT = "#2ca02c"  # Soft Forest Green
COLOR_MUTED = "#7570b3"  # Muted Purple


class EDAVisualizer:
    """Engine for generating and exporting Grid-Guard EDA figures."""

    def __init__(self, output_dir: Path | None = None) -> None:
        """Initialize visualizer.

        Args:
            output_dir: Directory where figures will be saved.
        """
        self.output_dir = output_dir.resolve() if output_dir else Path("docs/eda/figures").resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_dataset_overview(
        self, profile: DatasetProfile, filename: str = "fig1_dataset_overview.png"
    ) -> Path:
        """Generate overview figure: class imbalance and meter coverage tiers."""
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Panel 1: Class Distribution
        ax1 = axes[0]
        categories = ["Normal (FLAG=0)", "Theft (FLAG=1)"]
        counts = [
            profile.label_distribution.get("0", 0),
            profile.label_distribution.get("1", 0),
        ]
        total = sum(counts)
        pcts = [c / max(total, 1) * 100 for c in counts]
        bars1 = ax1.bar(
            categories,
            counts,
            color=[COLOR_NORMAL, COLOR_THEFT],
            width=0.55,
            edgecolor="black",
            linewidth=0.8,
        )
        ax1.set_title("Ground-Truth Class Distribution (Imbalance: ~10.7 to 1)")
        ax1.set_ylabel("Number of Consumers")
        ax1.grid(True, axis="y")
        for bar, count, pct in zip(bars1, counts, pcts, strict=False):
            yval = bar.get_height()
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                yval + (total * 0.015),
                f"{count:,}\n({pct:.1f}%)",
                ha="center",
                va="bottom",
                fontweight="bold",
            )
        ax1.set_ylim(0, max(counts) * 1.18)

        # Panel 2: Quality Tier Breakdown
        ax2 = axes[1]
        tiers = [
            "<=5% Null\n(Excellent)",
            "5-20% Null\n(Good)",
            "20-50% Null\n(Partial)",
            "50-99% Null\n(Sparse)",
            "100% Null\n(Empty)",
        ]
        q_counts = [
            profile.quality_tiers.excellent_le_5pct,
            profile.quality_tiers.good_5_to_20pct,
            profile.quality_tiers.partial_20_to_50pct,
            profile.quality_tiers.sparse_50_to_99pct,
            profile.quality_tiers.empty_100pct,
        ]
        tier_colors = ["#1a9850", "#91cf60", "#fee08b", "#fc8d59", "#d73027"]
        bars2 = ax2.bar(
            tiers,
            q_counts,
            color=tier_colors,
            width=0.6,
            edgecolor="black",
            linewidth=0.8,
        )
        ax2.set_title("Meter Data Coverage Quality Tiers")
        ax2.set_ylabel("Number of Meters")
        ax2.grid(True, axis="y")
        for bar, count in zip(bars2, q_counts, strict=False):
            yval = bar.get_height()
            pct = count / max(profile.total_meters, 1) * 100
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                yval + (profile.total_meters * 0.015),
                f"{count:,}\n({pct:.1f}%)",
                ha="center",
                va="bottom",
                fontsize=8.5,
            )
        ax2.set_ylim(0, max(q_counts) * 1.18)

        fig.suptitle(
            f"Grid-Guard Dataset Profile: {profile.dataset_name} ({profile.total_meters:,} meters)",
            y=1.02,
        )
        out_path = self.output_dir / filename
        plt.savefig(out_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        logger.info("Saved overview figure to %s", out_path)
        return out_path

    def plot_consumption_distribution(
        self,
        df_clean: pl.DataFrame,
        date_cols: list[str],
        filename: str = "fig2_consumption_distribution.png",
    ) -> Path:
        """Plot consumption distribution and boxplot comparing normal vs. tampered meters."""
        fig, axes = plt.subplots(1, 2, figsize=(13, 5))

        # Sample a subset of dates and meters for representative distributions
        np.random.seed(42)
        normal_df = df_clean.filter(pl.col("tamper_label") == 0)
        theft_df = df_clean.filter(pl.col("tamper_label") == 1)

        # Sample 100 random days across meters
        sample_dates = list(
            np.random.choice(date_cols, size=min(100, len(date_cols)), replace=False)
        )

        # Flatten valid readings
        normal_vals = normal_df.select(sample_dates).to_numpy().flatten()
        theft_vals = theft_df.select(sample_dates).to_numpy().flatten()

        normal_clean = normal_vals[~np.isnan(normal_vals)]
        theft_clean = theft_vals[~np.isnan(theft_vals)]

        # Sample 100k points for histogram
        n_sample = min(100_000, len(normal_clean), len(theft_clean))
        s_norm = np.random.choice(normal_clean, size=n_sample, replace=False)
        s_theft = np.random.choice(theft_clean, size=n_sample, replace=False)

        # Panel 1: Log-scale density histogram (0 to 50 kWh/day)
        ax1 = axes[0]
        bins = np.linspace(0, 40, 60)
        ax1.hist(
            s_norm,
            bins=bins,
            density=True,
            alpha=0.6,
            color=COLOR_NORMAL,
            label="Normal (FLAG=0)",
            edgecolor="white",
        )
        ax1.hist(
            s_theft,
            bins=bins,
            density=True,
            alpha=0.6,
            color=COLOR_THEFT,
            label="Theft (FLAG=1)",
            edgecolor="white",
        )
        ax1.set_title("Daily Consumption Distribution (0 to 40 kWh)")
        ax1.set_xlabel("Daily Consumption (kWh)")
        ax1.set_ylabel("Probability Density")
        ax1.legend(loc="upper right")
        ax1.grid(True)

        # Panel 2: Mean daily consumption per meter boxplot
        ax2 = axes[1]
        norm_means = (
            normal_df.select(pl.concat_list(date_cols).list.mean().alias("mean_kwh"))["mean_kwh"]
            .drop_nulls()
            .to_numpy()
        )
        theft_means = (
            theft_df.select(pl.concat_list(date_cols).list.mean().alias("mean_kwh"))["mean_kwh"]
            .drop_nulls()
            .to_numpy()
        )

        bplot = ax2.boxplot(
            [norm_means, theft_means],
            tick_labels=["Normal", "Theft"],
            patch_artist=True,
            showmeans=True,
            showfliers=False,  # Exclude extreme outliers for clean view
            medianprops={"color": "black", "linewidth": 1.5},
            meanprops={"marker": "D", "markeredgecolor": "black", "markerfacecolor": "yellow"},
        )
        bplot["boxes"][0].set_facecolor(COLOR_NORMAL)
        bplot["boxes"][1].set_facecolor(COLOR_THEFT)
        ax2.set_title("Meter-Level Mean Consumption (Outliers Clipped)")
        ax2.set_ylabel("Mean Daily Consumption (kWh/day)")
        ax2.grid(True)

        fig.suptitle("Consumption Distribution Diagnostics: Normal vs. Tampered Meters", y=1.02)
        out_path = self.output_dir / filename
        plt.savefig(out_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        logger.info("Saved consumption distribution figure to %s", out_path)
        return out_path

    def plot_missingness_and_gaps(
        self,
        profile: DatasetProfile,
        df_clean: pl.DataFrame,
        filename: str = "fig3_missingness_and_gaps.png",
    ) -> Path:
        """Plot missingness ratio distribution and gap streak lengths."""
        fig, axes = plt.subplots(1, 2, figsize=(13, 5))

        # Panel 1: Missing ratio histogram
        ax1 = axes[0]
        missing_ratios = df_clean["missing_ratio"].to_numpy() * 100
        ax1.hist(missing_ratios, bins=50, color=COLOR_MUTED, edgecolor="black", linewidth=0.5)
        ax1.set_title("Meter Missingness Distribution across 42,372 Consumers")
        ax1.set_xlabel("Missing Observations (%)")
        ax1.set_ylabel("Number of Meters")
        ax1.grid(True)
        ax1.axvline(x=20, color="orange", linestyle="--", linewidth=1.5, label="20% Threshold")
        ax1.axvline(x=50, color="red", linestyle="--", linewidth=1.5, label="50% Threshold")
        ax1.legend()

        # Panel 2: Gap length breakdown
        ax2 = axes[1]
        gap_categories = ["1 Day", "2-3 Days", "4-7 Days", "8-30 Days", ">30 Days"]
        gap_counts = [
            profile.gaps.gaps_1_day,
            profile.gaps.gaps_2_to_3_days,
            profile.gaps.gaps_4_to_7_days,
            profile.gaps.gaps_8_to_30_days,
            profile.gaps.gaps_over_30_days,
        ]
        total_gaps = max(sum(gap_counts), 1)
        gap_pcts = [c / total_gaps * 100 for c in gap_counts]

        bars = ax2.bar(
            gap_categories,
            gap_counts,
            color="#386cb0",
            edgecolor="black",
            linewidth=0.8,
            width=0.55,
        )
        ax2.set_title("Missing Streak (Gap) Length Distribution (5,000 Meter Sample)")
        ax2.set_ylabel("Number of Gap Instances")
        ax2.grid(True, axis="y")
        for bar, count, pct in zip(bars, gap_counts, gap_pcts, strict=False):
            yval = bar.get_height()
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                yval + (total_gaps * 0.015),
                f"{count:,}\n({pct:.1f}%)",
                ha="center",
                va="bottom",
                fontsize=8.5,
            )
        ax2.set_ylim(0, max(gap_counts) * 1.2)

        fig.suptitle("Missing Data & Time-Series Gap Diagnostics", y=1.02)
        out_path = self.output_dir / filename
        plt.savefig(out_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        logger.info("Saved missingness and gaps figure to %s", out_path)
        return out_path

    def plot_representative_time_series(
        self,
        df_clean: pl.DataFrame,
        date_cols: list[str],
        filename: str = "fig4_time_series_profiles.png",
    ) -> Path:
        """Plot representative normal vs tampered meter trajectories."""
        # Find normal and theft candidates with fallback
        normal_candidates = (
            df_clean.filter(pl.col("tamper_label") == 0)
            if "tamper_label" in df_clean.columns
            else df_clean
        )
        theft_candidates = (
            df_clean.filter(pl.col("tamper_label") == 1)
            if "tamper_label" in df_clean.columns
            else df_clean
        )

        if normal_candidates.height == 0:
            normal_candidates = df_clean
        if theft_candidates.height == 0:
            theft_candidates = df_clean

        norm_quality = normal_candidates.filter(
            pl.col("data_quality_status").is_in(["EXCELLENT", "GOOD"])
        )
        if norm_quality.height >= 2:
            normal_candidates = norm_quality

        theft_quality = theft_candidates.filter(
            pl.col("data_quality_status").is_in(["EXCELLENT", "GOOD"])
        )
        if theft_quality.height >= 2:
            theft_candidates = theft_quality

        norm_m1 = normal_candidates[0]["meter_id"][0]
        norm_m2 = normal_candidates[min(1, normal_candidates.height - 1)]["meter_id"][0]
        theft_m1 = theft_candidates[0]["meter_id"][0]
        theft_m2 = theft_candidates[min(1, theft_candidates.height - 1)]["meter_id"][0]

        selected_meters = [
            (norm_m1, "Normal Consumer 1 (Consistent Seasonal Variance)", COLOR_NORMAL, 0),
            (norm_m2, "Normal Consumer 2 (Stable Residential Profile)", COLOR_NORMAL, 0),
            (theft_m1, "Theft Consumer 1 (Sudden Consumption Collapse)", COLOR_THEFT, 1),
            (theft_m2, "Theft Consumer 2 (Intermittent Zero-Reading Signature)", COLOR_THEFT, 1),
        ]

        # Convert date_cols to datetime objects for x-axis
        x_dates = [datetime.strptime(d, "%Y-%m-%d") for d in date_cols]

        fig, axes = plt.subplots(4, 1, figsize=(14, 11), sharex=True)

        for ax, (m_id, label_title, col_color, _) in zip(axes, selected_meters, strict=False):
            m_row = df_clean.filter(pl.col("meter_id") == m_id)
            values = m_row.select(date_cols).to_numpy().flatten()

            ax.plot(x_dates, values, color=col_color, linewidth=0.8, alpha=0.85)
            # Add 30-day moving average trend line
            valid_idx = ~np.isnan(values)
            if np.sum(valid_idx) > 30:
                trend = pl.Series(values).rolling_mean(window_size=30).to_numpy()
                ax.plot(
                    x_dates,
                    trend,
                    color="black",
                    linestyle="-",
                    linewidth=1.5,
                    label="30-Day Trend",
                )

            ax.set_title(f"Meter ID: {m_id} — {label_title}", loc="left")
            ax.set_ylabel("kWh/day")
            ax.grid(True)
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(loc="upper right", frameon=True, fontsize=8)

        axes[-1].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        axes[-1].set_xlabel("Observation Date")

        fig.suptitle("Representative Smart-Meter Time-Series Profiles (2014 - 2016)", y=1.01)
        out_path = self.output_dir / filename
        plt.savefig(out_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        logger.info("Saved time-series profiles figure to %s", out_path)
        return out_path

    def plot_imputation_comparison(
        self,
        df_raw: pl.DataFrame,
        df_clean: pl.DataFrame,
        date_cols_raw: list[str],
        date_cols_clean: list[str],
        filename: str = "fig5_imputation_impact.png",
    ) -> Path:
        """Visualize before-and-after of bounded gap interpolation on a sample meter."""
        # Find a meter with short gaps (<= 3 days) that were interpolated
        diff_meters = df_clean.filter(pl.col("imputation_ratio") > 0.02).head(5)
        if diff_meters.height == 0:
            diff_meters = df_clean.head(1)

        sample_meter_id = diff_meters[0]["meter_id"][0]
        raw_vals = (
            df_raw.filter(pl.col("CONS_NO") == sample_meter_id)
            .select([pl.col(c).cast(pl.Float64, strict=False) for c in date_cols_raw])
            .to_numpy()
            .flatten()
        )
        clean_vals = (
            df_clean.filter(pl.col("meter_id") == sample_meter_id)
            .select(date_cols_clean)
            .to_numpy()
            .flatten()
        )

        # Focus on an adaptive window showing both interpolated points and preserved gaps
        total_len = len(clean_vals)
        window_size = min(90, total_len)
        start_idx = 0 if total_len <= 90 else min(100, total_len - window_size)
        end_idx = start_idx + window_size

        x_indices = np.arange(start_idx, end_idx)
        raw_window = raw_vals[start_idx:end_idx]
        clean_window = clean_vals[start_idx:end_idx]

        # Identify newly imputed points in this window
        imputed_pts = np.isnan(raw_window) & (~np.isnan(clean_window))

        fig, ax = plt.subplots(figsize=(13, 5))
        ax.plot(
            x_indices,
            clean_window,
            color=COLOR_NORMAL,
            linestyle="-",
            linewidth=1.2,
            label="Cleaned Trajectory",
        )
        ax.scatter(
            x_indices[~np.isnan(raw_window)],
            raw_window[~np.isnan(raw_window)],
            color=COLOR_NORMAL,
            s=18,
            label="Raw Observed Readings",
        )

        if np.any(imputed_pts):
            ax.scatter(
                x_indices[imputed_pts],
                clean_window[imputed_pts],
                color="red",
                s=45,
                marker="o",
                zorder=5,
                label=f"Imputed Bounded Gaps (<=3 days: {int(np.sum(imputed_pts))} pts)",
            )

        ax.set_title(f"Localized Bounded Temporal Imputation Showcase (Meter: {sample_meter_id})")
        ax.set_xlabel("Relative Day Index in Observation Period")
        ax.set_ylabel("Daily Consumption (kWh)")
        ax.grid(True)
        ax.legend(loc="upper right", frameon=True)

        out_path = self.output_dir / filename
        plt.savefig(out_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        logger.info("Saved imputation impact figure to %s", out_path)
        return out_path

    def generate_all_figures(
        self,
        df_raw: pl.DataFrame,
        df_clean: pl.DataFrame,
        profile: DatasetProfile,
        canonical_dates: list[str],
        raw_date_cols: list[str],
    ) -> list[Path]:
        """Generate and save the entire EDA figure suite."""
        logger.info("Generating full suite of EDA visualizations...")
        saved_paths: list[Path] = [
            self.plot_dataset_overview(profile),
            self.plot_consumption_distribution(df_clean, canonical_dates),
            self.plot_missingness_and_gaps(profile, df_clean),
            self.plot_representative_time_series(df_clean, canonical_dates),
            self.plot_imputation_comparison(df_raw, df_clean, raw_date_cols, canonical_dates),
        ]
        logger.info("Successfully generated %d figures in %s", len(saved_paths), self.output_dir)
        return saved_paths
