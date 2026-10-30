"""Thread-safe, atomic results and run record store."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from backend.config import (
    DATASET_VERSION,
    DEFAULT_SEED,
    DEFAULT_SEEDS,
    DEFAULT_SHARED_FEATURES,
    NEGATIVE_CLASS,
    POSITIVE_CLASS,
    PROJECT_ROOT,
    RANKING_METRIC,
    RESULTS_DIR,
)


class ResultsStore:
    """Manages persistence of run records, reference metrics, and split manifests."""

    def __init__(self, storage_dir: Path = RESULTS_DIR):
        self.storage_dir = storage_dir
        self.runs_dir = self.storage_dir / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.reference_file = self.storage_dir / "reference_results.json"
        self._initialize_reference_results()

    def _initialize_reference_results(self) -> None:
        """Initializes baseline reference results from executed Colab notebooks if not already present."""
        if self.reference_file.exists():
            return

        ref_data: Dict[str, Any] = {
            "run_id": "reference_baseline",
            "source": "executed notebook output",
            "status": "imported_reference",
            "created_at": "2026-10-24T00:00:00Z",
            "dataset_version": DATASET_VERSION,
            "split_hash": "d1419b74e6b90c7e93c051e0f497ba7d577c76b798214e33fa87a1b53ba2cdde",
            "split_protocol": "fixed shared 70/15/15 split (train.csv, validation.csv, test.csv)",
            "test_split": {
                "n": 678,
                "prevalence": 0.347,
                "positive_count": 235,
                "negative_count": 443,
                "weighting": "unweighted",
            },
            "positive_class": POSITIVE_CLASS,
            "negative_class": NEGATIVE_CLASS,
            "ranking_metric": RANKING_METRIC,
            "threshold_rule": "max sensitivity on validation subject to specificity >= 0.70; applied once to test",
            "feature_set": {
                "id": "shared_reduced_8dim",
                "raw_features": DEFAULT_SHARED_FEATURES,
                "transformed_dimension": 8,
            },
            "models": {
                "ml": {
                    "family": "ml",
                    "model_name": "HistGradientBoosting",
                    "status": "imported_reference",
                    "backend": "CPU",
                    "seed": 42,
                    "threshold": 0.5897,
                    "threshold_found": True,
                    "runtime_sec": 46.52,
                    "peak_memory_mb": 326.6,
                    "is_multi_seed": False,
                    "metrics_at_threshold": {
                        "accuracy": 0.711,
                        "precision": 0.570,
                        "sensitivity": 0.677,
                        "specificity": 0.729,
                        "f1": 0.619,
                        "roc_auc": 0.759,
                    },
                    "metrics_at_0.5": {
                        "accuracy": 0.686,
                        "precision": 0.531,
                        "sensitivity": 0.791,
                        "specificity": 0.630,
                        "f1": 0.636,
                        "roc_auc": 0.759,
                    },
                    "ci95": {
                        "accuracy": [0.678, 0.743],
                        "precision": [0.511, 0.629],
                        "sensitivity": [0.620, 0.739],
                        "specificity": [0.686, 0.769],
                        "f1": [0.570, 0.668],
                        "roc_auc": [0.725, 0.796],
                    },
                    "confusion": [[323, 120], [76, 159]],
                    "hyperparameters": {
                        "learning_rate": 0.05,
                        "max_iter": 100,
                        "max_leaf_nodes": 8,
                        "class_weight": "balanced",
                    },
                    "library_versions": {
                        "python": "3.13.16",
                        "scikit-learn": "1.6.1",
                        "numpy": "2.1.3",
                    },
                    "limitations": [
                        "Classical tree model evaluated on fixed cross-sectional split.",
                        "Unweighted sample analysis.",
                    ],
                },
                "dl": {
                    "family": "dl",
                    "model_name": "PyTorch Feed-Forward MLP",
                    "status": "imported_reference",
                    "backend": "CPU",
                    "seeds": DEFAULT_SEEDS,
                    "is_multi_seed": True,
                    "headline_metrics": {
                        "sensitivity": {"mean": 0.661, "sd": 0.010},
                        "specificity": {"mean": 0.719, "sd": 0.005},
                        "precision": {"mean": 0.555, "sd": 0.002},
                        "f1": {"mean": 0.604, "sd": 0.004},
                        "accuracy": {"mean": 0.699, "sd": 0.001},
                        "roc_auc": {"mean": 0.768, "sd": 0.002},
                    },
                    "metrics_at_threshold": {
                        "accuracy": 0.699,
                        "precision": 0.555,
                        "sensitivity": 0.661,
                        "specificity": 0.719,
                        "f1": 0.604,
                        "roc_auc": 0.768,
                    },
                    "metrics_at_0.5": {
                        "accuracy": 0.678,
                        "precision": 0.523,
                        "sensitivity": 0.790,
                        "specificity": 0.619,
                        "f1": 0.630,
                        "roc_auc": 0.768,
                    },
                    "threshold": {"mean": 0.583, "sd": 0.004},
                    "confusion": None,
                    "confusion_note": "Confusion matrix unavailable for imported aggregate summary; available after fresh local run with predictions.",
                    "runtime_sec": 4.65,
                    "peak_memory_mb": 340.2,
                    "hyperparameters": {
                        "hidden": [64, 32],
                        "dropout": 0.3,
                        "lr": 0.001,
                        "batch_size": 128,
                        "max_epochs": 100,
                        "patience": 10,
                        "weight_decay": 0.0001,
                    },
                    "library_versions": {
                        "python": "3.13.16",
                        "torch": "2.11.0+cpu",
                        "numpy": "2.1.3",
                    },
                    "limitations": [
                        "Headline metrics show mean +/- SD over 5 seeds (42-46) reflecting seed variation on fixed split.",
                        "SD is not a confidence interval for generalization.",
                    ],
                },
                "qml": {
                    "family": "qml",
                    "model_name": "PennyLane Variational Quantum Classifier (VQC)",
                    "status": "imported_reference",
                    "backend": "PennyLane default.qubit simulator (classical simulation on CPU; no quantum hardware)",
                    "seeds": DEFAULT_SEEDS,
                    "is_multi_seed": True,
                    "headline_metrics": {
                        "sensitivity": {"mean": 0.647, "sd": 0.040},
                        "specificity": {"mean": 0.702, "sd": 0.013},
                        "precision": {"mean": 0.535, "sd": 0.008},
                        "f1": {"mean": 0.585, "sd": 0.020},
                        "accuracy": {"mean": 0.683, "sd": 0.007},
                        "roc_auc": {"mean": 0.732, "sd": 0.014},
                    },
                    "metrics_at_threshold": {
                        "accuracy": 0.683,
                        "precision": 0.535,
                        "sensitivity": 0.647,
                        "specificity": 0.702,
                        "f1": 0.585,
                        "roc_auc": 0.732,
                    },
                    "metrics_at_0.5": {
                        "accuracy": 0.667,
                        "precision": 0.514,
                        "sensitivity": 0.722,
                        "specificity": 0.637,
                        "f1": 0.600,
                        "roc_auc": 0.732,
                    },
                    "threshold": {"mean": 0.557, "sd": 0.030},
                    "confusion": None,
                    "confusion_note": "Confusion matrix unavailable for imported aggregate summary; available after fresh local run with predictions.",
                    "runtime_sec": 32.12,
                    "peak_memory_mb": 355.8,
                    "hyperparameters": {
                        "n_layers": 2,
                        "lr": 0.05,
                        "epochs": 15,
                        "batch_size": 64,
                        "subsample_n": 1500,
                        "n_qubits": 8,
                        "trainable_parameters": 50,
                    },
                    "library_versions": {
                        "python": "3.13.16",
                        "pennylane": "0.45.1",
                        "torch": "2.11.0+cpu",
                    },
                    "limitations": [
                        "Simulated on default.qubit CPU; does not run on quantum hardware.",
                        "No quantum advantage claimed.",
                        "Headline metrics reflect mean +/- SD across 5 seeds.",
                    ],
                },
            },
        }

        self.save_json_atomic(ref_data, self.reference_file)

    def save_json_atomic(self, data: Dict[str, Any], target_path: Path) -> None:
        """Writes JSON to a temporary file before renaming to target path."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = target_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        tmp.replace(target_path)

    def save_run(self, run_record: Dict[str, Any]) -> None:
        """Saves a run record atomically."""
        run_id = run_record["run_id"]
        run_file = self.runs_dir / f"{run_id}.json"
        self.save_json_atomic(run_record, run_file)

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Loads run record by ID, falling back to reference baseline if requested."""
        if run_id in ("reference_baseline", "imported_reference", "reference"):
            if self.reference_file.exists():
                with open(self.reference_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None

        run_file = self.runs_dir / f"{run_id}.json"
        if run_file.exists():
            with open(run_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def list_runs(self) -> List[Dict[str, Any]]:
        """Lists metadata of all available runs."""
        runs: List[Dict[str, Any]] = []

        # Add reference baseline if exists
        if self.reference_file.exists():
            try:
                with open(self.reference_file, "r", encoding="utf-8") as f:
                    ref = json.load(f)
                    runs.append({
                        "run_id": ref.get("run_id"),
                        "source": ref.get("source"),
                        "status": ref.get("status"),
                        "created_at": ref.get("created_at"),
                        "dataset_version": ref.get("dataset_version"),
                        "models": list(ref.get("models", {}).keys()),
                    })
            except Exception:
                pass

        # Add stored runs
        for f in sorted(self.runs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                with open(f, "r", encoding="utf-8") as rf:
                    r = json.load(rf)
                    runs.append({
                        "run_id": r.get("run_id"),
                        "source": r.get("source", "local_run"),
                        "status": r.get("status"),
                        "created_at": r.get("created_at"),
                        "dataset_version": r.get("dataset_version"),
                        "models": list(r.get("models", {}).keys()),
                    })
            except Exception:
                continue

        return runs
