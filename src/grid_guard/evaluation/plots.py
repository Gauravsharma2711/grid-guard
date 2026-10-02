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


class ImbalanceVisualizer:
    """Generates comparative visualizations between unweighted baseline and imbalance strategies."""

    def __init__(self, output_dir: Path | str = "artifacts/imbalance/figures") -> None:
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

    def plot_pr_curves_comparison(
        self,
        strategy_curves: dict[str, tuple[np.ndarray, np.ndarray, float]],
        output_filename: str = "pr_curves_comparison.png",
    ) -> Path:
        """Plot multiple Precision-Recall curves on a single figure.

        Args:
            strategy_curves: Dict mapping strategy_name to (y_true, y_prob, pr_auc).
            output_filename: Target filename.
        """
        fig, ax = plt.subplots(figsize=(8, 6))
        colors = ["#2B6CB0", "#E53E3E", "#38A169", "#D69E2E", "#805AD5", "#319795"]

        first_yt = None
        for i, (name, (yt, yp, pr_auc)) in enumerate(strategy_curves.items()):
            if first_yt is None:
                first_yt = yt
            prec, rec, _ = precision_recall_curve(yt, yp)
            color = colors[i % len(colors)]
            ax.plot(rec, prec, label=f"{name} (PR-AUC = {pr_auc:.4f})", color=color)

        if first_yt is not None and len(first_yt) > 0:
            prevalence = float(first_yt.sum() / len(first_yt))
            ax.axhline(
                prevalence,
                color="#718096",
                linestyle="--",
                label=f"Random Chance ({prevalence:.1%})",
            )

        ax.set_xlabel("Recall (Theft Capture Rate)")
        ax.set_ylabel("Precision (Positive Predictive Value)")
        ax.set_title("Precision-Recall Trade-off: Baseline vs. Imbalance Mitigation")
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.legend(loc="upper right")
        ax.grid(True, linestyle="--", alpha=0.5)

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_roc_curves_comparison(
        self,
        strategy_curves: dict[str, tuple[np.ndarray, np.ndarray, float]],
        output_filename: str = "roc_curves_comparison.png",
    ) -> Path:
        """Plot multiple ROC curves on a single figure.

        Args:
            strategy_curves: Dict mapping strategy_name to (y_true, y_prob, roc_auc).
            output_filename: Target filename.
        """
        fig, ax = plt.subplots(figsize=(8, 6))
        colors = ["#2B6CB0", "#E53E3E", "#38A169", "#D69E2E", "#805AD5", "#319795"]

        for i, (name, (yt, yp, roc_auc)) in enumerate(strategy_curves.items()):
            fpr, tpr, _ = roc_curve(yt, yp)
            color = colors[i % len(colors)]
            ax.plot(fpr, tpr, label=f"{name} (ROC-AUC = {roc_auc:.4f})", color=color)

        ax.plot([0, 1], [0, 1], color="#718096", linestyle="--", label="Random Classifier (0.5)")
        ax.set_xlabel("False Positive Rate (FPR)")
        ax.set_ylabel("True Positive Rate (Recall / TPR)")
        ax.set_title("ROC Curves: Baseline vs. Imbalance Mitigation Strategies")
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.legend(loc="lower right")
        ax.grid(True, linestyle="--", alpha=0.5)

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_calibration_curves(
        self,
        strategy_probs: dict[str, tuple[np.ndarray, np.ndarray, float]],
        output_filename: str = "calibration_curves.png",
    ) -> Path:
        """Plot reliability curves showing probability calibration across strategies.

        Args:
            strategy_probs: Dict mapping strategy_name to (prob_true, prob_pred, brier_score).
            output_filename: Target filename.
        """
        fig, ax = plt.subplots(figsize=(8, 6))
        colors = ["#2B6CB0", "#E53E3E", "#38A169", "#D69E2E", "#805AD5"]

        ax.plot([0, 1], [0, 1], "k--", label="Perfect Calibration")

        for i, (name, (prob_true, prob_pred, brier)) in enumerate(strategy_probs.items()):
            color = colors[i % len(colors)]
            ax.plot(
                prob_pred,
                prob_true,
                marker="s",
                label=f"{name} (Brier = {brier:.4f})",
                color=color,
            )

        ax.set_xlabel("Mean Predicted Probability")
        ax.set_ylabel("Fraction of True Tampering Positives")
        ax.set_title("Reliability Diagram: Calibration Distortion Assessment")
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.0])
        ax.legend(loc="upper left")
        ax.grid(True, linestyle="--", alpha=0.5)

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_probability_distributions_comparison(
        self,
        baseline_data: tuple[np.ndarray, np.ndarray],
        champion_data: tuple[np.ndarray, np.ndarray],
        champion_name: str = "Imbalance Champion",
        output_filename: str = "probability_distributions_comparison.png",
    ) -> Path:
        """Compare predicted probability distributions of baseline vs champion strategy."""
        fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)

        base_yt, base_yp = baseline_data
        champ_yt, champ_yp = champion_data

        # Subplot 1: Baseline
        axes[0].hist(
            base_yp[base_yt == 0],
            bins=50,
            density=True,
            alpha=0.6,
            color="#3182CE",
            label="Normal (0)",
        )
        axes[0].hist(
            base_yp[base_yt == 1],
            bins=50,
            density=True,
            alpha=0.6,
            color="#E53E3E",
            label="Theft (1)",
        )
        axes[0].axvline(0.5, color="#2D3748", linestyle="--", label="0.5 Threshold")
        axes[0].set_title("Phase 4: Unweighted Baseline")
        axes[0].set_xlabel("Predicted Probability")
        axes[0].set_ylabel("Density")
        axes[0].legend(loc="upper right")
        axes[0].grid(True, linestyle="--", alpha=0.5)

        # Subplot 2: Champion
        axes[1].hist(
            champ_yp[champ_yt == 0],
            bins=50,
            density=True,
            alpha=0.6,
            color="#3182CE",
            label="Normal (0)",
        )
        axes[1].hist(
            champ_yp[champ_yt == 1],
            bins=50,
            density=True,
            alpha=0.6,
            color="#E53E3E",
            label="Theft (1)",
        )
        axes[1].axvline(0.5, color="#2D3748", linestyle="--", label="0.5 Threshold")
        axes[1].set_title(f"Phase 5: {champion_name}")
        axes[1].set_xlabel("Predicted Probability")
        axes[1].legend(loc="upper right")
        axes[1].grid(True, linestyle="--", alpha=0.5)

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_precision_at_k_comparison(
        self,
        strategies_topk: dict[str, dict[str, dict[str, Any]]],
        output_filename: str = "precision_at_k_comparison.png",
    ) -> Path:
        """Plot Precision@K curves comparing multiple strategies."""
        fig, ax = plt.subplots(figsize=(8, 5))
        colors = ["#2B6CB0", "#E53E3E", "#38A169", "#D69E2E", "#805AD5"]

        for i, (name, topk_dict) in enumerate(strategies_topk.items()):
            ks = [int(k) for k in topk_dict.keys()]
            precs = [topk_dict[str(k)]["precision_at_k"] for k in ks]
            color = colors[i % len(colors)]
            ax.plot(ks, precs, marker="o", label=name, color=color, linewidth=2.0)

        ax.set_xlabel("Inspection Capacity (Top-K Ranked Meters)")
        ax.set_ylabel("Precision@K (Capture Accuracy)")
        ax.set_title("Operational Inspection Precision vs. Crew Capacity (Top-K)")
        ax.set_ylim([0.0, 1.05])
        ax.legend(loc="upper right")
        ax.grid(True, linestyle="--", alpha=0.5)

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_financial_loss_comparison(
        self,
        comparison_dict: dict[str, dict[str, float]],
        currency: str = "USD",
        output_filename: str = "financial_loss_comparison.png",
    ) -> Path:
        """Grouped bar chart comparing financial losses across strategies."""
        fig, ax = plt.subplots(figsize=(9, 5))

        strategies = list(comparison_dict.keys())
        x = np.arange(len(strategies))
        width = 0.25

        fp_costs = [comparison_dict[s].get("fp_cost", 0.0) for s in strategies]
        fn_costs = [comparison_dict[s].get("fn_cost", 0.0) for s in strategies]
        total_losses = [comparison_dict[s].get("total_loss", 0.0) for s in strategies]

        ax.bar(x - width, fp_costs, width, label="Wasted FP Dispatch", color="#DD6B20")
        ax.bar(x, fn_costs, width, label="Undetected FN Leakage", color="#E53E3E")
        ax.bar(x + width, total_losses, width, label="Total Operational Loss", color="#742A2A")

        ax.set_ylabel(f"Amount ({currency})")
        ax.set_title("Financial Operational Impact: Phase 4 Baseline vs. Phase 5 Strategies")
        ax.set_xticks(x)
        ax.set_xticklabels(strategies)
        ax.legend(loc="upper right")
        ax.grid(True, linestyle="--", alpha=0.5, axis="y")

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path


class CostSensitiveVisualizer:
    """Publication-grade visualizer for Phase 6 cost-sensitive learning diagnostics."""

    def __init__(self, output_dir: Path | str) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_expected_cost_curve(
        self,
        grid_data: list[dict[str, Any]],
        output_filename: str = "expected_cost_curve.png",
    ) -> Path:
        """Diagnostic plot of operational financial loss vs. decision threshold."""
        thresholds = [d["threshold"] for d in grid_data]
        total_loss = [d["total_operational_loss"] for d in grid_data]
        fp_costs = [d["fp_dispatch_cost"] for d in grid_data]
        fn_costs = [d["fn_leakage_cost"] for d in grid_data]

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(
            thresholds, total_loss, color="#742A2A", linewidth=2.5, label="Total Operational Loss"
        )
        ax.plot(
            thresholds, fn_costs, color="#E53E3E", linestyle="--", label="Undetected FN Leakage"
        )
        ax.plot(thresholds, fp_costs, color="#DD6B20", linestyle=":", label="Wasted FP Dispatch")

        # Mark conventional 0.5 threshold
        ax.axvline(
            0.5, color="gray", linestyle="-.", alpha=0.7, label="Conventional Threshold (0.5)"
        )

        ax.set_xlabel("Decision Cutoff Threshold")
        ax.set_ylabel("Financial Cost (USD)")
        ax.set_title("Diagnostic Expected Cost Curve Across Decision Thresholds")
        ax.legend(loc="upper right")
        ax.grid(True, linestyle="--", alpha=0.5)

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_financial_weight_distribution(
        self,
        c_fn_costs: np.ndarray,
        dispatch_cost: float,
        output_filename: str = "financial_weight_distribution.png",
    ) -> Path:
        """Plot the distribution of per-meter positive leakage costs alongside fixed dispatch cost."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

        # Subplot 1: Positive Class C_FN distribution
        c_fn = np.asarray(c_fn_costs, dtype=np.float64)
        ax1.hist(c_fn, bins=40, color="#3182CE", edgecolor="black", alpha=0.7)
        ax1.axvline(
            np.median(c_fn),
            color="#E53E3E",
            linestyle="--",
            linewidth=2,
            label=f"Median C_FN: ${np.median(c_fn):,.0f}",
        )
        ax1.axvline(
            dispatch_cost,
            color="#DD6B20",
            linestyle=":",
            linewidth=2,
            label=f"Fixed C_FP: ${dispatch_cost:,.0f}",
        )
        ax1.set_xlabel("Estimated Revenue Leakage Cost C_FN (USD)")
        ax1.set_ylabel("Meter Frequency")
        ax1.set_title("Positive Class Financial Leakage Distribution (C_FN)")
        ax1.legend(loc="upper right")
        ax1.grid(True, linestyle="--", alpha=0.5)

        # Subplot 2: Relative Weight Ratio (C_FN / C_FP)
        ratios = c_fn / dispatch_cost
        ax2.hist(ratios, bins=40, color="#805AD5", edgecolor="black", alpha=0.7)
        ax2.axvline(
            np.median(ratios),
            color="#E53E3E",
            linestyle="--",
            linewidth=2,
            label=f"Median Ratio: {np.median(ratios):.1f}x",
        )
        ax2.set_xlabel("Relative Error Penalty Ratio (C_FN,i / C_FP)")
        ax2.set_ylabel("Meter Frequency")
        ax2.set_title("Financial Cost Ratio Distribution (w_i / w_neg)")
        ax2.legend(loc="upper right")
        ax2.grid(True, linestyle="--", alpha=0.5)

        fig.tight_layout()
        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_three_phase_pr_curves(
        self,
        curves_dict: dict[str, dict[str, np.ndarray | float]],
        output_filename: str = "pr_curves_three_phase.png",
    ) -> Path:
        """Compare PR Curves across Phase 4, Phase 5, and Phase 6."""
        fig, ax = plt.subplots(figsize=(8, 6))
        colors = ["#4A5568", "#3182CE", "#E53E3E", "#38A169"]

        for idx, (name, d) in enumerate(curves_dict.items()):
            rec = d["recall"]
            prec = d["precision"]
            auc_val = d.get("pr_auc", 0.0)
            color = colors[idx % len(colors)]
            ax.plot(rec, prec, label=f"{name} (PR-AUC = {auc_val:.4f})", color=color, linewidth=2.0)

        ax.set_xlabel("Recall (Theft Capture Rate)")
        ax.set_ylabel("Precision")
        ax.set_title("Precision-Recall Curves: Phase 4 vs. Phase 5 vs. Phase 6")
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.legend(loc="upper right")
        ax.grid(True, linestyle="--", alpha=0.5)

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_three_phase_financial_loss(
        self,
        losses_dict: dict[str, dict[str, float]],
        output_filename: str = "financial_loss_three_phase.png",
    ) -> Path:
        """Grouped bar chart comparing financial outcomes across Phase 4, 5, and 6."""
        fig, ax = plt.subplots(figsize=(9, 5))
        phases = list(losses_dict.keys())
        x = np.arange(len(phases))
        width = 0.25

        fp_costs = [losses_dict[p].get("fp_cost", 0.0) for p in phases]
        fn_costs = [losses_dict[p].get("fn_cost", 0.0) for p in phases]
        total_costs = [losses_dict[p].get("total_loss", 0.0) for p in phases]

        ax.bar(x - width, fp_costs, width, label="Wasted FP Dispatch", color="#DD6B20")
        ax.bar(x, fn_costs, width, label="Undetected FN Leakage", color="#E53E3E")
        ax.bar(x + width, total_costs, width, label="Total Operational Loss", color="#742A2A")

        ax.set_ylabel("Amount (USD)")
        ax.set_title("Operational Financial Impact Evolution (Phase 4 -> 5 -> 6)")
        ax.set_xticks(x)
        ax.set_xticklabels(phases)
        ax.legend(loc="upper right")
        ax.grid(True, linestyle="--", alpha=0.5, axis="y")

        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path

    def plot_feature_importance_comparison(
        self,
        df_p4: pl.DataFrame,
        df_p6: pl.DataFrame,
        top_n: int = 12,
        output_filename: str = "feature_importance_shift.png",
    ) -> Path:
        """Compare top gain feature importances between Phase 4 unweighted and Phase 6 cost-sensitive."""
        fig, ax = plt.subplots(figsize=(10, 6))

        top_p6 = df_p6.head(top_n)
        features = top_p6["feature"].to_list()

        # Join to get matching Phase 4 importances
        p6_gains = top_p6["importance"].to_list()
        p4_dict = dict(zip(df_p4["feature"].to_list(), df_p4["importance"].to_list(), strict=False))
        p4_gains = [p4_dict.get(f, 0.0) for f in features]

        # Normalize to percentage of total gain
        p4_sum = max(sum(df_p4["importance"].to_list()), 1e-6)
        p6_sum = max(sum(df_p6["importance"].to_list()), 1e-6)
        p4_pct = [(v / p4_sum) * 100.0 for v in p4_gains]
        p6_pct = [(v / p6_sum) * 100.0 for v in p6_gains]

        y = np.arange(len(features))
        height = 0.35

        ax.barh(
            y - height / 2, p4_pct, height, label="Phase 4 (Unweighted Baseline)", color="#718096"
        )
        ax.barh(y + height / 2, p6_pct, height, label="Phase 6 (Cost-Sensitive)", color="#3182CE")

        ax.set_yticks(y)
        ax.set_yticklabels(features)
        ax.invert_yaxis()
        ax.set_xlabel("Relative Feature Importance (% Total Gain)")
        ax.set_title(f"Top {top_n} Features: Importance Shift Under Financial Weighting")
        ax.legend(loc="lower right")
        ax.grid(True, linestyle="--", alpha=0.5, axis="x")

        fig.tight_layout()
        out_path = self.output_dir / output_filename
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        return out_path
