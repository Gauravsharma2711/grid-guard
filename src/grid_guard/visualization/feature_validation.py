"""Visual feature validation and diagnostic plotting for Grid-Guard."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl


class FeatureVisualizer:
    """Generates publication-quality diagnostic plots demonstrating feature dynamics."""

    def __init__(self, output_dir: Path | str = "docs/features/figures") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Apply clean publication-grade styling
        plt.rcParams.update(
            {
                "figure.autolayout": True,
                "axes.titlesize": 12,
                "axes.labelsize": 10,
                "xtick.labelsize": 9,
                "ytick.labelsize": 9,
                "legend.fontsize": 9,
                "lines.linewidth": 1.7,
            }
        )

    def plot_step_down_dynamics(
        self,
        df_feature: pl.DataFrame,
        output_filename: str = "fig1_step_down_tampering.png",
    ) -> Path:
        """Plot raw consumption and sustained step-down tampering detection response."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True)

        days = list(range(len(df_feature)))
        raw_vals = df_feature.get_column("consumption_kwh").to_list()
        recent_14d = df_feature.get_column("rolling_mean_14d").to_list()
        drop_ratio = df_feature.get_column("sustained_drop_ratio").to_list()
        duration = df_feature.get_column("sustained_drop_duration").to_list()

        ax1.plot(days, raw_vals, color="#4A5568", alpha=0.6, label="Raw Daily Reading (kWh)")
        ax1.plot(days, recent_14d, color="#3182CE", label="Recent 14-day Rolling Mean")
        ax1.set_ylabel("Consumption (kWh)")
        ax1.set_title("Sustained Step-Down Tampering: Consumption Baseline vs. Collapse")
        ax1.legend(loc="upper right")
        ax1.grid(True, linestyle="--", alpha=0.5)

        ax2.plot(days, drop_ratio, color="#E53E3E", label="Sustained Drop Ratio [0, 1]")
        ax2_twin = ax2.twinx()
        ax2_twin.plot(days, duration, color="#DD6B20", linestyle=":", label="Drop Duration (Days)")
        ax2.set_ylabel("Sustained Drop Ratio", color="#E53E3E")
        ax2_twin.set_ylabel("Depressed Streak (Days)", color="#DD6B20")
        ax2.set_xlabel("Time (Days)")
        ax2.set_title("Signature Response: Fractional Drop and Continuous Duration Tracking")
        ax2.grid(True, linestyle="--", alpha=0.5)

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_zero_streak_detection(
        self,
        df_feature: pl.DataFrame,
        output_filename: str = "fig2_zero_streak_detection.png",
    ) -> Path:
        """Plot zero-consumption reading response and streak tracking."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True)

        days = list(range(len(df_feature)))
        raw_vals = df_feature.get_column("consumption_kwh").to_list()
        streak = df_feature.get_column("current_zero_streak").to_list()
        ratio_30d = df_feature.get_column("zero_ratio_30d").to_list()

        ax1.step(days, raw_vals, color="#2B6CB0", where="mid", label="Daily Consumption (kWh)")
        ax1.set_ylabel("Consumption (kWh)")
        ax1.set_title("Zero-Consumption Signature: Reading Profile with Disconnections")
        ax1.legend(loc="upper right")
        ax1.grid(True, linestyle="--", alpha=0.5)

        ax2.plot(days, streak, color="#9B2C2C", label="Current Zero Streak (Days)")
        ax2_twin = ax2.twinx()
        ax2_twin.plot(days, ratio_30d, color="#319795", linestyle="--", label="Zero Ratio 30d")
        ax2.set_ylabel("Consecutive Zero Days", color="#9B2C2C")
        ax2_twin.set_ylabel("Trailing 30d Zero Ratio", color="#319795")
        ax2.set_xlabel("Time (Days)")
        ax2.set_title("Dynamic Zero Streak and Trailing 30-Day Zero Density")
        ax2.grid(True, linestyle="--", alpha=0.5)

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_flatline_variance_collapse(
        self,
        df_feature: pl.DataFrame,
        output_filename: str = "fig3_flatline_variance_collapse.png",
    ) -> Path:
        """Plot artificial constant meter reading vs. rolling coefficient of variation."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True)

        days = list(range(len(df_feature)))
        raw_vals = df_feature.get_column("consumption_kwh").to_list()
        flat_streak = df_feature.get_column("flatline_streak").to_list()
        cv_7d = df_feature.get_column("rolling_cv_7d").to_list()

        ax1.plot(days, raw_vals, color="#2D3748", label="Consumption (kWh)")
        ax1.set_ylabel("Consumption (kWh)")
        ax1.set_title("Flatline Signature: Artificially Constant Metering Profile")
        ax1.legend(loc="upper right")
        ax1.grid(True, linestyle="--", alpha=0.5)

        ax2.plot(days, flat_streak, color="#805AD5", label="Flatline Streak (Days)")
        ax2_twin = ax2.twinx()
        ax2_twin.plot(days, cv_7d, color="#D69E2E", linestyle="--", label="Rolling CV 7d")
        ax2.set_ylabel("Flatline Streak (Days)", color="#805AD5")
        ax2_twin.set_ylabel("Coefficient of Variation (7d)", color="#D69E2E")
        ax2.set_xlabel("Time (Days)")
        ax2.set_title("Variance Collapse and Consecutive Identical-Value Tracking")
        ax2.grid(True, linestyle="--", alpha=0.5)

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_ratios_and_par(
        self,
        df_feature: pl.DataFrame,
        output_filename: str = "fig4_multi_scale_ratios_and_par.png",
    ) -> Path:
        """Plot multi-scale moving average ratios and peak-to-average ratio dynamics."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True)

        days = list(range(len(df_feature)))
        raw_vals = df_feature.get_column("consumption_kwh").to_list()
        r7_30 = df_feature.get_column("ratio_7d_30d").to_list()
        par_7d = df_feature.get_column("par_7d").to_list()

        ax1.plot(days, raw_vals, color="#4A5568", alpha=0.5, label="Raw Consumption (kWh)")
        ax1.plot(
            days,
            df_feature.get_column("rolling_mean_7d").to_list(),
            color="#2B6CB0",
            label="Rolling Mean 7d",
        )
        ax1.plot(
            days,
            df_feature.get_column("rolling_mean_30d").to_list(),
            color="#D69E2E",
            label="Rolling Mean 30d",
        )
        ax1.set_ylabel("Consumption (kWh)")
        ax1.set_title("Multi-Scale Trailing Dynamics: 7-day vs. 30-day Baselines")
        ax1.legend(loc="upper right")
        ax1.grid(True, linestyle="--", alpha=0.5)

        ax2.plot(days, r7_30, color="#319795", label="7d / 30d Moving Average Ratio")
        ax2_twin = ax2.twinx()
        ax2_twin.plot(
            days, par_7d, color="#C53030", linestyle=":", label="Peak-to-Average Ratio 7d"
        )
        ax2.axhline(1.0, color="#A0AEC0", linestyle="--", alpha=0.7)
        ax2.set_ylabel("Ratio 7d/30d", color="#319795")
        ax2_twin.set_ylabel("PAR (7d)", color="#C53030")
        ax2.set_xlabel("Time (Days)")
        ax2.set_title("Moving Average Divergence and Spikiness Indicators")
        ax2.grid(True, linestyle="--", alpha=0.5)

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_real_meter_profiles(
        self,
        normal_df: pl.DataFrame,
        theft_df: pl.DataFrame,
        output_filename: str = "fig5_real_meters_comparison.png",
    ) -> Path:
        """Compare real normal meter vs. real tampered meter feature trajectories."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(13, 7), sharex=True)

        norm_days = list(range(len(normal_df)))
        theft_days = list(range(len(theft_df)))

        # Top row: Raw Consumption & 14d rolling mean
        ax1.plot(
            norm_days,
            normal_df.get_column("consumption_kwh").to_list(),
            color="#4A5568",
            alpha=0.4,
            label="Raw Consumption",
        )
        ax1.plot(
            norm_days,
            normal_df.get_column("rolling_mean_14d").to_list(),
            color="#2B6CB0",
            label="14d Rolling Mean",
        )
        ax1.set_title("Normal Consumer (FLAG=0): Consumption Baseline")
        ax1.set_ylabel("kWh")
        ax1.legend(loc="upper right")
        ax1.grid(True, linestyle="--", alpha=0.5)

        ax2.plot(
            theft_days,
            theft_df.get_column("consumption_kwh").to_list(),
            color="#4A5568",
            alpha=0.4,
            label="Raw Consumption",
        )
        ax2.plot(
            theft_days,
            theft_df.get_column("rolling_mean_14d").to_list(),
            color="#C53030",
            label="14d Rolling Mean",
        )
        ax2.set_title("Tampered Consumer (FLAG=1): Step-Down Collapse")
        ax2.set_ylabel("kWh")
        ax2.legend(loc="upper right")
        ax2.grid(True, linestyle="--", alpha=0.5)

        # Bottom row: Sustained Drop Ratio & Zero Streak
        ax3.plot(
            norm_days,
            normal_df.get_column("sustained_drop_ratio").to_list(),
            color="#319795",
            label="Sustained Drop Ratio",
        )
        ax3.set_title("Normal Consumer: Stable Drop Ratio (< 0.2)")
        ax3.set_xlabel("Observation Day")
        ax3.set_ylabel("Drop Ratio [0, 1]")
        ax3.legend(loc="upper right")
        ax3.grid(True, linestyle="--", alpha=0.5)

        ax4.plot(
            theft_days,
            theft_df.get_column("sustained_drop_ratio").to_list(),
            color="#E53E3E",
            label="Sustained Drop Ratio",
        )
        ax4.set_title("Tampered Consumer: Severe Persistent Drop Ratio (> 0.7)")
        ax4.set_xlabel("Observation Day")
        ax4.set_ylabel("Drop Ratio [0, 1]")
        ax4.legend(loc="upper right")
        ax4.grid(True, linestyle="--", alpha=0.5)

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path
