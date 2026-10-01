"""Diagnostic visualization suite for Phase 4 baseline modeling and evaluation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from sklearn.metrics import precision_recall_curve, roc_curve


class BaselineVisualizer:
    """Generates publication-quality diagnostic charts for model evaluation."""

    def __init__(self, output_dir: Path | str = "artifacts/baseline/figures") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        plt.rcParams.update(
            {
                "figure.autolayout": True,
                "axes.titlesize": 12,
                "axes.labelsize": 10,
                "xtick.labelsize": 9,
                "ytick.labelsize": 9,
                "legend.fontsize": 9,
                "lines.linewidth": 1.8,
            }
        )

    def plot_pr_curve(
        self,
        y_true: np.ndarray,
        y_prob: np.ndarray,
        pr_auc: float,
        output_filename: str = "pr_curve.png",
    ) -> Path:
        """Plot Precision-Recall curve with no-skill baseline."""
        precisions, recalls, _ = precision_recall_curve(y_true, y_prob)
        prevalence = float(np.mean(y_true))

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.plot(
            recalls,
            precisions,
            color="#2B6CB0",
            label=f"LightGBM Baseline (PR-AUC = {pr_auc:.4f})",
        )
        ax.axhline(
            prevalence,
            color="#E53E3E",
            linestyle="--",
            label=f"No-Skill Baseline (Prevalence = {prevalence:.2%})",
        )
        ax.set_xlabel("Recall (Theft Capture Rate)")
        ax.set_ylabel("Precision (Accuracy of Flags)")
        ax.set_title("Precision-Recall Curve (Extreme Imbalance Benchmark)")
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.legend(loc="upper right")
        ax.grid(True, linestyle="--", alpha=0.5)

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_roc_curve(
        self,
        y_true: np.ndarray,
        y_prob: np.ndarray,
        roc_auc: float,
        output_filename: str = "roc_curve.png",
    ) -> Path:
        """Plot Receiver Operating Characteristic curve."""
        fpr, tpr, _ = roc_curve(y_true, y_prob)

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.plot(
            fpr,
            tpr,
            color="#319795",
            label=f"LightGBM Baseline (ROC-AUC = {roc_auc:.4f})",
        )
        ax.plot([0, 1], [0, 1], color="#A0AEC0", linestyle="--", label="Random Classifier")
        ax.set_xlabel("False Positive Rate")
        ax.set_ylabel("True Positive Rate")
        ax.set_title("Receiver Operating Characteristic (ROC) Curve")
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.legend(loc="lower right")
        ax.grid(True, linestyle="--", alpha=0.5)

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_confusion_matrix(
        self,
        cm_dict: dict[str, int],
        output_filename: str = "confusion_matrix.png",
    ) -> Path:
        """Plot confusion matrix heatmap."""
        tp = cm_dict["tp"]
        fp = cm_dict["fp"]
        tn = cm_dict["tn"]
        fn = cm_dict["fn"]

        matrix = np.array([[tn, fp], [fn, tp]])

        fig, ax = plt.subplots(figsize=(6, 5))
        cax = ax.matshow(matrix, cmap="Blues", alpha=0.85)
        fig.colorbar(cax)

        for (i, j), val in np.ndenumerate(matrix):
            color = "white" if val > matrix.max() / 2 else "black"
            ax.text(
                j,
                i,
                f"{val:,}",
                ha="center",
                va="center",
                color=color,
                fontsize=12,
                fontweight="bold",
            )

        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["Pred Normal (0)", "Pred Theft (1)"])
        ax.set_yticklabels(["Actual Normal (0)", "Actual Theft (1)"])
        ax.set_title("Baseline Confusion Matrix (Threshold = 0.5)", pad=20)

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_probability_distribution(
        self,
        y_true: np.ndarray,
        y_prob: np.ndarray,
        output_filename: str = "probability_distribution.png",
    ) -> Path:
        """Plot predicted probability density comparing normal vs. tampered meters."""
        fig, ax = plt.subplots(figsize=(8, 5))

        normal_probs = y_prob[y_true == 0]
        theft_probs = y_prob[y_true == 1]

        ax.hist(
            normal_probs,
            bins=50,
            density=True,
            alpha=0.6,
            color="#3182CE",
            label="Normal Consumers (FLAG=0)",
        )
        ax.hist(
            theft_probs,
            bins=50,
            density=True,
            alpha=0.6,
            color="#E53E3E",
            label="Tampered Consumers (FLAG=1)",
        )
        ax.axvline(
            0.5, color="#2D3748", linestyle="--", linewidth=1.5, label="Baseline Threshold (0.5)"
        )

        ax.set_xlabel("Predicted Theft Probability")
        ax.set_ylabel("Density")
        ax.set_title("Predicted Probability Distribution: Separation Assessment")
        ax.legend(loc="upper right")
        ax.grid(True, linestyle="--", alpha=0.5)

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_feature_importance(
        self,
        df_imp: pl.DataFrame,
        top_n: int = 15,
        output_filename: str = "feature_importance.png",
    ) -> Path:
        """Plot top-N feature importances."""
        fig, ax = plt.subplots(figsize=(9, 6))

        top_df = df_imp.head(top_n).sort("importance", descending=False)
        features = top_df.get_column("feature").to_list()
        importances = top_df.get_column("importance").to_list()
        imp_type = top_df.get_column("importance_type")[0].capitalize()

        y_pos = np.arange(len(features))
        ax.barh(y_pos, importances, color="#4FD1C5", edgecolor="#234E52", alpha=0.85)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(features)
        ax.set_xlabel(f"{imp_type} Importance")
        ax.set_title(f"Top {top_n} Features by LightGBM {imp_type}")
        ax.grid(True, linestyle="--", alpha=0.5, axis="x")

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_financial_loss_breakdown(
        self,
        fin_dict: dict[str, Any],
        output_filename: str = "financial_loss_breakdown.png",
    ) -> Path:
        """Plot financial breakdown of operational inspection dispatch costs vs revenue leakage."""
        fig, ax = plt.subplots(figsize=(8, 5))

        fin = fin_dict.get("financial_breakdown", {})
        curr = fin_dict.get("currency", "USD")

        categories = [
            "Wasted FP Dispatch",
            "Undetected FN Leakage",
            "Total Operational Loss",
            "Gross Revenue Recovered",
        ]
        values = [
            fin.get("total_fp_dispatch_cost", 0.0),
            fin.get("total_fn_leakage_cost", 0.0),
            fin.get("total_baseline_operational_loss", 0.0),
            fin.get("estimated_gross_recovery", 0.0),
        ]
        colors = ["#DD6B20", "#E53E3E", "#742A2A", "#38A169"]

        bars = ax.bar(categories, values, color=colors, alpha=0.85, edgecolor="#1A202C")
        ax.set_ylabel(f"Amount ({curr})")
        ax.set_title("Baseline Operational Financial Impact Breakdown")
        ax.grid(True, linestyle="--", alpha=0.5, axis="y")

        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f"{curr} {height:,.0f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
            )

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_precision_at_k(
        self,
        top_k_dict: dict[str, dict[str, Any]],
        output_filename: str = "precision_at_k.png",
    ) -> Path:
        """Plot Precision@K curve across field inspection capacities."""
        fig, ax = plt.subplots(figsize=(7, 5))

        ks = [int(k) for k in top_k_dict.keys()]
        precs = [top_k_dict[str(k)]["precision_at_k"] for k in ks]

        ax.plot(ks, precs, marker="o", color="#805AD5", linewidth=2.0)
        ax.set_xlabel("Inspection Capacity (Top-K Ranked Meters)")
        ax.set_ylabel("Precision@K (Capture Accuracy)")
        ax.set_title("Operational Inspection Precision vs. Crew Capacity (Top-K)")
        ax.set_ylim([0.0, 1.05])
        ax.grid(True, linestyle="--", alpha=0.5)

        for k, p in zip(ks, precs, strict=True):
            ax.annotate(
                f"{p:.1%}",
                (k, p),
                textcoords="offset points",
                xytext=(0, 7),
                ha="center",
                fontsize=8,
            )

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path
