"""Training-only class weighting and controlled resampling strategies for rare-tampering learning."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import polars as pl
from sklearn.neighbors import NearestNeighbors

logger = logging.getLogger(__name__)


@dataclass
class ClassWeightResult:
    """Summary of class distribution and calculated class weights."""

    total_samples: int
    n_positives: int
    n_negatives: int
    positive_ratio: float
    imbalance_ratio: float  # N_neg / N_pos
    multiplier: float
    scale_pos_weight: float  # (N_neg / N_pos) * multiplier
    class_weights: dict[int, float]  # {0: 1.0, 1: scale_pos_weight}

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return asdict(self)


def compute_training_class_weights(
    y_train: pl.Series | np.ndarray,
    multiplier: float = 1.0,
) -> ClassWeightResult:
    """Calculate class weighting strictly from training data observations.

    Args:
        y_train: Binary training labels (0 or 1).
        multiplier: Optional dampening or amplification factor (default: 1.0).

    Returns:
        ClassWeightResult containing counts, ratio, and scale_pos_weight.

    Raises:
        ValueError: If y_train is empty or does not contain positive instances.
    """
    y_arr = y_train.to_numpy() if isinstance(y_train, pl.Series) else np.asarray(y_train)
    total = len(y_arr)
    if total == 0:
        raise ValueError("y_train is empty. Cannot compute class weights.")

    n_pos = int((y_arr == 1).sum())
    n_neg = int((y_arr == 0).sum())

    if n_pos == 0:
        raise ValueError("Training partition contains 0 positive instances. Cannot balance.")
    if n_neg == 0:
        raise ValueError("Training partition contains 0 negative instances.")

    imb_ratio = float(n_neg / n_pos)
    scale_pos_weight = float(imb_ratio * multiplier)

    res = ClassWeightResult(
        total_samples=total,
        n_positives=n_pos,
        n_negatives=n_neg,
        positive_ratio=round(float(n_pos / total), 6),
        imbalance_ratio=round(imb_ratio, 4),
        multiplier=float(multiplier),
        scale_pos_weight=round(scale_pos_weight, 4),
        class_weights={0: 1.0, 1: round(scale_pos_weight, 4)},
    )
    logger.info(
        f"Training Class Distribution: Total={total:,}, Neg={n_neg:,}, Pos={n_pos:,} "
        f"({res.positive_ratio:.2%}, Ratio={imb_ratio:.2f}:1). "
        f"Computed scale_pos_weight={res.scale_pos_weight:.2f} (multiplier={multiplier})."
    )
    return res


def controlled_training_resample(
    X_train: pl.DataFrame,
    y_train: pl.Series,
    meta_train: pl.DataFrame | None = None,
    strategy: str = "controlled_oversample",
    target_pos_ratio: float = 0.20,
    k_neighbors: int = 5,
    sample_size_cap: int | None = None,
    random_seed: int = 42,
) -> tuple[pl.DataFrame, pl.Series, pl.DataFrame | None, dict[str, Any]]:
    """Apply resampling strictly to training partition data.

    Never apply resampling to validation or test data!

    Args:
        X_train: Training feature DataFrame.
        y_train: Training binary label Series.
        meta_train: Optional metadata DataFrame for tracking.
        strategy: 'controlled_oversample', 'controlled_undersample', or 'smote'.
        target_pos_ratio: Desired ratio of positive instances to negative instances (pos / neg).
        k_neighbors: Number of nearest neighbors for SMOTE.
        sample_size_cap: Optional cap on synthetic instances to prevent memory exhaustion.
        random_seed: Deterministic random seed.

    Returns:
        Tuple of (X_resampled, y_resampled, meta_resampled, audit_dict).
    """
    rng = np.random.default_rng(random_seed)
    y_arr = y_train.to_numpy().astype(np.int32)
    pos_idx = np.where(y_arr == 1)[0]
    neg_idx = np.where(y_arr == 0)[0]

    n_pos_orig = len(pos_idx)
    n_neg_orig = len(neg_idx)
    orig_total = len(y_arr)

    audit: dict[str, Any] = {
        "strategy": strategy,
        "target_pos_ratio": target_pos_ratio,
        "random_seed": random_seed,
        "original_counts": {
            "total": orig_total,
            "positives": n_pos_orig,
            "negatives": n_neg_orig,
            "pos_ratio": round(n_pos_orig / orig_total, 4),
        },
    }

    if strategy == "controlled_oversample":
        # Target: n_pos_target = int(n_neg_orig * target_pos_ratio)
        n_pos_target = max(n_pos_orig, int(n_neg_orig * target_pos_ratio))
        additional_needed = n_pos_target - n_pos_orig

        if additional_needed > 0:
            sampled_pos_idx = rng.choice(pos_idx, size=additional_needed, replace=True)
            new_pos_idx = np.concatenate([pos_idx, sampled_pos_idx])
        else:
            new_pos_idx = pos_idx

        combined_indices = np.concatenate([neg_idx, new_pos_idx])
        rng.shuffle(combined_indices)

        X_res = X_train[combined_indices]
        y_res = y_train[combined_indices]
        meta_res = meta_train[combined_indices] if meta_train is not None else None

    elif strategy == "controlled_undersample":
        # Target: n_neg_target = int(n_pos_orig / target_pos_ratio)
        n_neg_target = min(n_neg_orig, max(n_pos_orig, int(n_pos_orig / target_pos_ratio)))
        sampled_neg_idx = rng.choice(neg_idx, size=n_neg_target, replace=False)

        combined_indices = np.concatenate([sampled_neg_idx, pos_idx])
        rng.shuffle(combined_indices)

        X_res = X_train[combined_indices]
        y_res = y_train[combined_indices]
        meta_res = meta_train[combined_indices] if meta_train is not None else None

    elif strategy == "smote":
        # Verify strictly numeric features only
        for col_name, col_type in zip(X_train.columns, X_train.dtypes, strict=True):
            if col_type not in (
                pl.Float32,
                pl.Float64,
                pl.Int8,
                pl.Int16,
                pl.Int32,
                pl.Int64,
                pl.UInt8,
                pl.UInt16,
                pl.UInt32,
                pl.UInt64,
            ):
                raise TypeError(
                    f"SMOTE feature safety violation: Column '{col_name}' has non-numeric type '{col_type}'. "
                    f"Raw timestamps or identifiers must NEVER enter SMOTE."
                )

        n_pos_target = max(n_pos_orig, int(n_neg_orig * target_pos_ratio))
        n_synthetic = n_pos_target - n_pos_orig
        if sample_size_cap and n_synthetic > sample_size_cap:
            logger.warning(
                f"SMOTE: Requested {n_synthetic:,} synthetic samples exceeds cap of {sample_size_cap:,}. "
                f"Capping to {sample_size_cap:,} to preserve physical calibration and memory limits."
            )
            n_synthetic = sample_size_cap

        if n_synthetic > 0 and n_pos_orig > k_neighbors:
            X_pos = X_train[pos_idx].to_numpy().astype(np.float32)
            # Impute NaN/nulls for k-NN if any
            col_means = np.nanmean(X_pos, axis=0)
            col_means = np.nan_to_num(col_means, nan=0.0)
            inds = np.where(np.isnan(X_pos))
            X_pos[inds] = np.take(col_means, inds[1])

            # Fit k-NN on minority class
            knn = NearestNeighbors(n_neighbors=k_neighbors + 1, metric="euclidean", n_jobs=-1)
            knn.fit(X_pos)
            nn_indices = knn.kneighbors(X_pos, return_distance=False)

            # Generate synthetic samples
            chosen_base = rng.choice(n_pos_orig, size=n_synthetic, replace=True)
            chosen_neighbor_col = rng.integers(1, k_neighbors + 1, size=n_synthetic)
            chosen_neighbors = nn_indices[chosen_base, chosen_neighbor_col]

            base_vectors = X_pos[chosen_base]
            neighbor_vectors = X_pos[chosen_neighbors]
            gaps = rng.uniform(0.0, 1.0, size=(n_synthetic, 1)).astype(np.float32)
            synthetic_vectors = base_vectors + gaps * (neighbor_vectors - base_vectors)

            # Build synthetic DataFrame
            df_synth_X = pl.DataFrame(synthetic_vectors, schema=X_train.schema)
            s_synth_y = pl.Series(
                y_train.name, np.ones(n_synthetic, dtype=np.int32), dtype=y_train.dtype
            )

            # Append synthetic samples to training set
            X_res = pl.concat([X_train, df_synth_X])
            y_res = pl.concat([y_train, s_synth_y])

            if meta_train is not None:
                # Assign distinct synthetic metadata indicator
                df_synth_meta = pl.DataFrame(
                    {
                        "meter_id": ["SYNTHETIC_SMOTE"] * n_synthetic,
                        "timestamp": [None] * n_synthetic,
                        "data_quality_status": ["SYNTHETIC"] * n_synthetic,
                    }
                )
                # Align schema with meta_train
                for col in meta_train.columns:
                    if col not in df_synth_meta.columns:
                        df_synth_meta = df_synth_meta.with_columns(
                            pl.lit(None).cast(meta_train.schema[col]).alias(col)
                        )
                df_synth_meta = df_synth_meta.select(meta_train.columns)
                meta_res = pl.concat([meta_train, df_synth_meta])
            else:
                meta_res = None
        else:
            X_res = X_train
            y_res = y_train
            meta_res = meta_train
    else:
        raise ValueError(
            f"Unsupported resampling strategy: '{strategy}'. "
            f"Expected 'controlled_oversample', 'controlled_undersample', or 'smote'."
        )

    res_total = len(y_res)
    res_pos = int((y_res.to_numpy() == 1).sum())
    res_neg = res_total - res_pos

    audit["resampled_counts"] = {
        "total": res_total,
        "positives": res_pos,
        "negatives": res_neg,
        "pos_ratio": round(res_pos / res_total, 4),
    }

    logger.info(
        f"Applied '{strategy}' to training set: Original={orig_total:,} (Pos={n_pos_orig:,}, "
        f"{n_pos_orig / orig_total:.2%}) -> Resampled={res_total:,} (Pos={res_pos:,}, "
        f"{res_pos / res_total:.2%})."
    )
    return X_res, y_res, meta_res, audit
