"""Evaluation module computing verified metrics, threshold selection, and bootstrap CIs."""
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from sklearn.metrics import confusion_matrix, roc_auc_score, roc_curve

from backend.config import MIN_SPECIFICITY_TARGET


def compute_metrics(
    y_true: Union[List[int], np.ndarray],
    y_prob: Union[List[float], np.ndarray],
    thr: float,
) -> Dict[str, Any]:
    """
    Computes accuracy, precision, sensitivity, specificity, F1, ROC-AUC, and confusion matrix.
    If a metric is mathematically undefined (e.g. division by zero or single class), returns None (not 0).
    """
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob, dtype=float)

    if len(y_true) == 0:
        return {
            "accuracy": None,
            "precision": None,
            "sensitivity": None,
            "specificity": None,
            "f1": None,
            "roc_auc": None,
            "confusion": [[0, 0], [0, 0]],
        }

    y_pred = (y_prob >= thr).astype(int)

    # Confusion matrix with explicit labels [0, 1] -> [[TN, FP], [FN, TP]]
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    div = lambda a, b: float(a / b) if b > 0 else None

    # Exact definitions
    acc = float((tp + tn) / len(y_true))
    prec = div(tp, tp + fp)
    sens = div(tp, tp + fn)
    spec = div(tn, tn + fp)
    f1 = div(2 * prec * sens, prec + sens) if (prec is not None and sens is not None) else None

    # ROC-AUC requires both classes present in y_true
    auc = None
    if len(np.unique(y_true)) == 2:
        try:
            auc = float(roc_auc_score(y_true, y_prob))
        except Exception:
            auc = None

    return {
        "accuracy": acc,
        "precision": prec,
        "sensitivity": sens,
        "specificity": spec,
        "f1": f1,
        "roc_auc": auc,
        "confusion": [[int(tn), int(fp)], [int(fn), int(tp)]],
    }


def pick_threshold(
    y_val: Union[List[int], np.ndarray],
    p_val: Union[List[float], np.ndarray],
    min_spec: float = MIN_SPECIFICITY_TARGET,
) -> Tuple[float, bool]:
    """
    Selects decision threshold on VALIDATION data only:
    Maximizes sensitivity subject to specificity >= min_spec (default 0.70).
    Returns (threshold, constraint_met). If not achievable, defaults to (0.5, False).
    """
    y_val = np.asarray(y_val).astype(int)
    p_val = np.asarray(p_val, dtype=float)

    if len(np.unique(y_val)) < 2:
        return 0.5, False

    fpr, tpr, thresholds = roc_curve(y_val, p_val)
    # Specificity = 1 - FPR
    valid_idx = np.where(((1.0 - fpr) >= min_spec) & np.isfinite(thresholds))[0]

    if len(valid_idx) == 0:
        return 0.5, False

    best_idx = valid_idx[np.argmax(tpr[valid_idx])]
    return float(thresholds[best_idx]), True


def bootstrap_ci(
    y_true: Union[List[int], np.ndarray],
    y_prob: Union[List[float], np.ndarray],
    thr: float,
    n_boot: int = 1000,
    seed: int = 42,
) -> Dict[str, Optional[List[float]]]:
    """Computes 95% percentile bootstrap confidence intervals on held-out test predictions."""
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob, dtype=float)
    n = len(y_true)

    keys = ["accuracy", "precision", "sensitivity", "specificity", "f1", "roc_auc"]
    samples: Dict[str, List[float]] = {k: [] for k in keys}

    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        m = compute_metrics(y_true[idx], y_prob[idx], thr)
        for k in keys:
            if m[k] is not None:
                samples[k].append(m[k])

    out: Dict[str, Optional[List[float]]] = {}
    for k in keys:
        if len(samples[k]) >= 50:
            low = float(np.percentile(samples[k], 2.5))
            high = float(np.percentile(samples[k], 97.5))
            out[k] = [round(low, 4), round(high, 4)]
        else:
            out[k] = None
    return out


def evaluate_model_predictions(
    y_val: np.ndarray,
    p_val: np.ndarray,
    y_test: np.ndarray,
    p_test: np.ndarray,
    min_spec: float = MIN_SPECIFICITY_TARGET,
    compute_ci: bool = True,
) -> Dict[str, Any]:
    """
    Performs full evaluation pipeline:
    1. Validation threshold selection.
    2. Held-out test evaluation at val-chosen threshold.
    3. Held-out test evaluation at threshold 0.5.
    4. Bootstrap 95% CI (optional).
    """
    thr, found = pick_threshold(y_val, p_val, min_spec=min_spec)
    metrics_at_thr = compute_metrics(y_test, p_test, thr)
    metrics_at_05 = compute_metrics(y_test, p_test, 0.5)

    ci = bootstrap_ci(y_test, p_test, thr) if compute_ci else None

    # Calculate ROC curve coordinates for plotting
    fpr, tpr, _ = roc_curve(y_test, p_test)
    roc_curve_data = {
        "fpr": [round(float(x), 4) for x in fpr.tolist()],
        "tpr": [round(float(y), 4) for y in tpr.tolist()],
    }

    return {
        "threshold": round(float(thr), 4),
        "threshold_found": bool(found),
        "metrics_at_threshold": metrics_at_thr,
        "metrics_at_0.5": metrics_at_05,
        "ci95": ci,
        "roc_curve": roc_curve_data,
        "test_n": int(len(y_test)),
        "test_prevalence": round(float(np.mean(y_test)), 4),
    }


def aggregate_seed_metrics(seed_evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes mean and SD across multiple seed runs (reflecting seed variation on fixed split)."""
    if not seed_evaluations:
        return {}

    metric_keys = ["accuracy", "precision", "sensitivity", "specificity", "f1", "roc_auc"]
    out_thr: Dict[str, Dict[str, Optional[float]]] = {}
    out_05: Dict[str, Dict[str, Optional[float]]] = {}

    for k in metric_keys:
        vals_thr = [ev["metrics_at_threshold"][k] for ev in seed_evaluations if ev.get("metrics_at_threshold", {}).get(k) is not None]
        vals_05 = [ev["metrics_at_0.5"][k] for ev in seed_evaluations if ev.get("metrics_at_0.5", {}).get(k) is not None]

        out_thr[k] = {
            "mean": round(float(np.mean(vals_thr)), 4) if vals_thr else None,
            "sd": round(float(np.std(vals_thr, ddof=1)), 4) if len(vals_thr) > 1 else 0.0 if vals_thr else None,
        }
        out_05[k] = {
            "mean": round(float(np.mean(vals_05)), 4) if vals_05 else None,
            "sd": round(float(np.std(vals_05, ddof=1)), 4) if len(vals_05) > 1 else 0.0 if vals_05 else None,
        }

    thrs = [ev["threshold"] for ev in seed_evaluations if ev.get("threshold") is not None]
    threshold_agg = {
        "mean": round(float(np.mean(thrs)), 4) if thrs else 0.5,
        "sd": round(float(np.std(thrs, ddof=1)), 4) if len(thrs) > 1 else 0.0,
    }

    return {
        "metrics_at_threshold": out_thr,
        "metrics_at_0.5": out_05,
        "threshold": threshold_agg,
        "n_seeds": len(seed_evaluations),
        "note": "Standard deviation reflects seed variation on the fixed test set; not a confidence interval for generalization.",
    }
