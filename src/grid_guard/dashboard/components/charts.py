"""Visualization and charting components for Grid-Guard Dashboard.

Produces publication-grade, interactive/static charts using Matplotlib.
Follows clean operational analytics aesthetic.
"""

from __future__ import annotations

from typing import Any

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


def _clean_feature_name(name: str) -> str:
    """Format raw technical feature name into clean human-readable title."""
    return (
        name.replace("_", " ")
        .replace("kwh", "kWh")
        .replace("30d", "30-Day")
        .replace("60d", "60-Day")
        .replace("90d", "90-Day")
        .replace("std", "Std Dev")
        .title()
    )


def plot_consumption_timeseries(
    readings: list[dict[str, Any]],
    meter_id: str,
    anomaly_window_days: int = 30,
) -> None:
    """Render smart-meter consumption time-series with historical baseline and anomaly window."""
    if not readings:
        st.info("No time-series readings available for this meter.")
        return

    df = pd.DataFrame(readings)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    # 14-day rolling historical baseline
    df["rolling_mean"] = df["consumption_kwh"].rolling(window=14, min_periods=3).mean()

    fig, ax = plt.subplots(figsize=(10, 4.2), dpi=120)

    # Plot actual readings
    ax.plot(
        df["timestamp"],
        df["consumption_kwh"],
        color="#1f77b4",
        alpha=0.65,
        linewidth=1.3,
        label="Daily Consumption (kWh)",
        marker="o",
        markersize=2.5,
    )

    # Plot rolling baseline
    ax.plot(
        df["timestamp"],
        df["rolling_mean"],
        color="#2ca02c",
        linewidth=2.0,
        linestyle="--",
        label="14-Day Rolling Baseline",
    )

    # Shade the recent anomaly evaluation window
    if len(df) > anomaly_window_days:
        cutoff_date = df["timestamp"].iloc[-anomaly_window_days]
        end_date = df["timestamp"].iloc[-1]
        ax.axvspan(
            cutoff_date,
            end_date,
            color="#d62728",
            alpha=0.12,
            label=f"Latest Evaluation Window ({anomaly_window_days}d)",
        )

    ax.set_title(
        f"AMI Consumption Time-Series — Meter: {meter_id}", fontsize=11, fontweight="bold", pad=10
    )
    ax.set_ylabel("Consumption (kWh/day)", fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate(rotation=30)
    ax.legend(loc="upper right", framealpha=0.9, fontsize=8.5)
    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)


def plot_shap_contributions(top_features: list[dict[str, Any]]) -> None:
    """Render horizontal bar chart of top SHAP feature attributions."""
    if not top_features:
        st.info("No feature attribution records available.")
        return

    # Extract names and contributions
    records = []
    for item in top_features:
        # Compatible with both SingleMeterPredictionResponse and InspectionTicketResponse schemas
        name = item.get("feature_name", "Unknown")
        val = item.get("contribution") or item.get("attribution", 0.0)
        display_val = item.get("feature_value", None)
        records.append(
            {
                "name": _clean_feature_name(name),
                "attribution": float(val),
                "val_str": f"{display_val:.2f}" if isinstance(display_val, (int, float)) else "",
            }
        )

    # Sort by absolute attribution ascending for horizontal display
    records = sorted(records, key=lambda x: abs(x["attribution"]))[-10:]

    names = [r["name"] for r in records]
    values = [r["attribution"] for r in records]
    colors = ["#d62728" if v > 0 else "#2ca02c" for v in values]

    fig, ax = plt.subplots(figsize=(8.5, max(3.5, len(names) * 0.4)), dpi=120)

    y_pos = np.arange(len(names))
    bars = ax.barh(y_pos, values, color=colors, alpha=0.85, height=0.6)

    ax.axvline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=8.5)
    ax.set_xlabel("SHAP Contribution to Tamper Log-Odds (Δ margin)", fontsize=9)
    ax.set_title("Top Local Feature Drivers (Tree-SHAP)", fontsize=10.5, fontweight="bold", pad=8)
    ax.grid(axis="x", linestyle=":", alpha=0.5)

    # Annotate bar values
    for bar, val in zip(bars, values, strict=False):
        offset = 0.02 if val >= 0 else -0.02
        ha = "left" if val >= 0 else "right"
        ax.text(
            val + offset,
            bar.get_y() + bar.get_height() / 2,
            f"{val:+.3f}",
            va="center",
            ha=ha,
            fontsize=8,
            color="#333333",
        )

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def plot_policy_comparison_chart(comparison_data: dict[str, Any]) -> None:
    """Render comparison between Fixed Threshold, Bayes Cost, and Dynamic ENV."""
    policies = comparison_data.get("policy_comparison", {})
    if not policies:
        st.info("Policy benchmark data is not currently available.")
        return

    labels = []
    inspections = []
    expected_env = []
    total_losses = []

    label_map = {
        "fixed_threshold_0.5": "Fixed Threshold (0.50)",
        "bayes_cost_threshold": "Bayes Cost Threshold",
        "env_ranking": "Dynamic ENV Policy (Grid-Guard)",
    }

    # Add policies
    for key, data in policies.items():
        labels.append(label_map.get(key, key))
        inspections.append(data.get("inspections_recommended", 0))
        expected_env.append(
            data.get("expected_financials", {}).get("expected_net_value", 0.0) / 1000.0
        )
        total_losses.append(
            data.get("realized_evaluation", {}).get("realized_total_operational_loss", 0.0) / 1000.0
        )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.0), dpi=120)

    x = np.arange(len(labels))
    width = 0.45

    # Chart 1: Expected Net Value ($k)
    bars1 = ax1.bar(x, expected_env, width, color=["#7f7f7f", "#1f77b4", "#2ca02c"], alpha=0.85)
    ax1.set_ylabel("Expected Net Value ($k)", fontsize=9)
    ax1.set_title("Expected Net Value by Policy", fontsize=10, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=20, ha="right", fontsize=8.5)
    ax1.grid(axis="y", linestyle=":", alpha=0.5)

    for bar, val in zip(bars1, expected_env, strict=False):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 3,
            f"${val:.1f}k",
            ha="center",
            fontsize=8,
        )

    # Chart 2: Total Operational Loss ($k)
    bars2 = ax2.bar(x, total_losses, width, color=["#d62728", "#ff7f0e", "#1f77b4"], alpha=0.85)
    ax2.set_ylabel("Realized Operational Loss ($k)", fontsize=9)
    ax2.set_title("Realized Loss (Dispatch + Lost Leakage)", fontsize=10, fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=20, ha="right", fontsize=8.5)
    ax2.grid(axis="y", linestyle=":", alpha=0.5)

    for bar, val in zip(bars2, total_losses, strict=False):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"${val:.1f}k",
            ha="center",
            fontsize=8,
        )

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def plot_phase_benchmarks_chart(cost_data: dict[str, Any]) -> None:
    """Render 3-Phase Model Comparison (Phase 4 vs Phase 5 vs Phase 6)."""
    exps = cost_data.get("validation_experiments", {})
    if not exps:
        st.info("Validation experiment data is not available.")
        return

    phases = [
        ("Phase 4: Baseline", exps.get("phase4_unweighted_baseline", {})),
        ("Phase 5: Imbalance", exps.get("phase5_smote_tomek", {})),
        ("Phase 6: Cost-Sensitive", exps.get("phase6_cost_sensitive_dispatch_norm", {})),
    ]

    names = [p[0] for p in phases]
    pr_aucs = [p[1].get("statistical", {}).get("pr_auc", 0.0) for p in phases]
    p_at_100 = [p[1].get("ranking", {}).get("100", {}).get("precision_at_k", 0.0) for p in phases]
    losses = [p[1].get("financial", {}).get("total_operational_loss", 0.0) / 1000.0 for p in phases]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.0), dpi=120)
    x = np.arange(len(names))
    width = 0.35

    # Chart 1: Statistical Ranking Metrics
    ax1.bar(x - width / 2, pr_aucs, width, label="PR-AUC", color="#1f77b4", alpha=0.85)
    ax1.bar(x + width / 2, p_at_100, width, label="Precision@100", color="#2ca02c", alpha=0.85)
    ax1.set_ylabel("Metric Score", fontsize=9)
    ax1.set_title("PR-AUC & Precision@100 by Phase", fontsize=10, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=15, ha="right", fontsize=8.5)
    ax1.legend(loc="upper left", fontsize=8)
    ax1.grid(axis="y", linestyle=":", alpha=0.5)

    # Chart 2: Total Operational Loss ($k)
    bars_loss = ax2.bar(x, losses, 0.45, color=["#d62728", "#ff7f0e", "#2ca02c"], alpha=0.85)
    ax2.set_ylabel("Total Operational Loss ($k)", fontsize=9)
    ax2.set_title("Total Operational Loss by Phase ($k)", fontsize=10, fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(names, rotation=15, ha="right", fontsize=8.5)
    ax2.grid(axis="y", linestyle=":", alpha=0.5)

    for bar, val in zip(bars_loss, losses, strict=False):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 10,
            f"${val:.0f}k",
            ha="center",
            fontsize=8,
        )

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
