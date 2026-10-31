"""Orchestrates model training, evaluation, progress tracking, and failure isolation."""
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import psutil

from backend.config import (
    DATASET_VERSION,
    DEFAULT_SEED,
    DEFAULT_SEEDS,
    DEFAULT_SHARED_FEATURES,
    NEGATIVE_CLASS,
    POSITIVE_CLASS,
    PROJECT_ROOT,
    RANKING_METRIC,
    TARGET_COLUMN,
)
from backend.data.preprocessor import DataSplitManager
from backend.evaluation.evaluator import (
    aggregate_seed_metrics,
    compute_metrics,
    evaluate_model_predictions,
    pick_threshold,
)
from backend.models.dl_adapter import DLAdapter
from backend.models.ml_adapter import MLAdapter
from backend.models.qml_adapter import QMLAdapter
from backend.storage.store import ResultsStore
from backend.tracking.mlflow_tracker import MLflowTracker, get_tracker



def get_current_process_memory_mb() -> float:
    """Returns the current process memory consumption in megabytes using psutil."""
    try:
        proc = psutil.Process()
        return round(proc.memory_info().rss / (1024.0 * 1024.0), 2)
    except Exception:
        return 0.0


class Orchestrator:
    """Thread-safe orchestrator managing asynchronous model runs and status."""

    def __init__(
        self,
        store: Optional[ResultsStore] = None,
        tracker: Optional[MLflowTracker] = None,
    ):
        self.store = store or ResultsStore()
        self.tracker = tracker or get_tracker()
        self.split_manager = DataSplitManager()
        self.lock = threading.Lock()

        self.active_run_id: Optional[str] = None
        self.run_status_cache: Dict[str, Dict[str, Any]] = {}
        # Retain fitted adapters for single record prediction
        self.fitted_adapters: Dict[str, Any] = {}
        self.active_thresholds: Dict[str, float] = {}

    def is_running(self) -> bool:
        with self.lock:
            return self.active_run_id is not None

    def get_run_status(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            # Check in-memory status cache first
            if run_id in self.run_status_cache:
                return self.run_status_cache[run_id]

        # Check persisted store
        saved = self.store.get_run(run_id)
        if saved:
            return {
                "run_id": saved["run_id"],
                "status": saved.get("status", "completed"),
                "models": [
                    {
                        "family": fam,
                        "status": m_info.get("status", "completed"),
                        "progress": 100 if m_info.get("status") in ("completed", "imported_reference") else 0,
                        "runtime_sec": m_info.get("runtime_sec", 0.0),
                        "peak_memory_mb": m_info.get("peak_memory_mb", 0.0),
                        "error": m_info.get("error"),
                    }
                    for fam, m_info in saved.get("models", {}).items()
                ],
                "created_at": saved.get("created_at"),
                "dataset_version": saved.get("dataset_version"),
            }
        return None

    def start_run(
        self,
        dataset_id: str = DATASET_VERSION,
        models: Optional[List[str]] = None,
        seed: int = DEFAULT_SEED,
        custom_df: Optional[pd.DataFrame] = None,
        simulate_failure_family: Optional[str] = None,
        memory_limit_mb: Optional[float] = None,
        single_seed_mode: bool = False,
    ) -> Dict[str, Any]:
        """Initiates an asynchronous model training and evaluation run."""
        models_to_run = [m.lower() for m in (models or ["ml", "dl", "qml"])]
        valid_families = {"ml", "dl", "qml"}
        models_to_run = [m for m in models_to_run if m in valid_families]
        if not models_to_run:
            models_to_run = ["ml"]

        with self.lock:
            if self.active_run_id is not None:
                raise RuntimeError("A run is currently in progress.")

            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
            run_id = f"run_{ts}"
            self.active_run_id = run_id

            # Initialize status tracking
            status_entry: Dict[str, Any] = {
                "run_id": run_id,
                "status": "queued",
                "dataset_version": dataset_id,
                "seed": seed,
                "models": [
                    {
                        "family": fam,
                        "status": "queued",
                        "progress": 0,
                        "runtime_sec": 0.0,
                        "peak_memory_mb": 0.0,
                        "error": None,
                    }
                    for fam in models_to_run
                ],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self.run_status_cache[run_id] = status_entry

        # Launch in background thread
        thread = threading.Thread(
            target=self._execute_run,
            args=(
                run_id,
                models_to_run,
                seed,
                custom_df,
                simulate_failure_family,
                memory_limit_mb,
                single_seed_mode,
            ),
            daemon=True,
        )
        thread.start()

        return {"run_id": run_id, "status": "queued"}

    def _execute_run(
        self,
        run_id: str,
        models_to_run: List[str],
        seed: int,
        custom_df: Optional[pd.DataFrame],
        simulate_failure_family: Optional[str],
        memory_limit_mb: Optional[float],
        single_seed_mode: bool,
    ) -> None:
        """Background thread executing the pipeline."""
        with self.lock:
            if run_id in self.run_status_cache:
                self.run_status_cache[run_id]["status"] = "running"

        try:
            # 1. Load data split
            if custom_df is not None:
                train_df, val_df, test_df, split_hash = self.split_manager.split_single_csv(
                    custom_df, seed=seed
                )
                split_protocol = "stratified 70/15/15 single-upload split"
            else:
                train_df, val_df, test_df, split_hash = self.split_manager.load_trio_splits()
                split_protocol = "fixed shared 70/15/15 split (train.csv, validation.csv, test.csv)"

            # 2. Derive or load shared features
            shared_info = self.split_manager.derive_or_load_shared_features(train_df, split_hash, seed)
            selected_features = shared_info["selected_features"]
            numeric_features = shared_info["numeric_features"]
            categorical_features = shared_info["categorical_features"]

            X_train = train_df[selected_features]
            y_train = (train_df[TARGET_COLUMN] == POSITIVE_CLASS).astype(int).to_numpy()
            X_val = val_df[selected_features]
            y_val = (val_df[TARGET_COLUMN] == POSITIVE_CLASS).astype(int).to_numpy()
            X_test = test_df[selected_features]
            y_test = (test_df[TARGET_COLUMN] == POSITIVE_CLASS).astype(int).to_numpy()

            run_record: Dict[str, Any] = {
                "run_id": run_id,
                "source": "local_fresh_run",
                "status": "completed",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "dataset_version": DATASET_VERSION,
                "split_hash": split_hash,
                "split_protocol": split_protocol,
                "seed": seed,
                "test_split": {
                    "n": int(len(y_test)),
                    "prevalence": round(float(np.mean(y_test)), 4),
                    "positive_count": int(np.sum(y_test)),
                    "negative_count": int(len(y_test) - np.sum(y_test)),
                    "weighting": "unweighted",
                },
                "positive_class": POSITIVE_CLASS,
                "negative_class": NEGATIVE_CLASS,
                "ranking_metric": RANKING_METRIC,
                "threshold_rule": "max sensitivity on validation subject to specificity >= 0.70; applied once to test",
                "feature_set": {
                    "id": "shared_reduced_8dim",
                    "raw_features": selected_features,
                    "transformed_dimension": shared_info["transformed_dim"],
                },
                "models": {},
            }

            # Initialize MLflow parent run inside background worker thread
            parent_run_id = None
            mlflow_child_runs: Dict[str, str] = {}
            try:
                parent_run_id = self.tracker.start_parent_run(
                    app_run_id=run_id,
                    dataset_version=DATASET_VERSION,
                    split_hash=split_hash,
                    split_protocol=split_protocol,
                    seed=seed,
                    single_seed_mode=single_seed_mode,
                    models_to_run=models_to_run,
                    selected_features=selected_features,
                    transformed_dim=shared_info["transformed_dim"],
                    n_train=len(train_df),
                    n_val=len(val_df),
                    n_test=len(test_df),
                    ranking_metric=RANKING_METRIC,
                )
            except Exception:
                pass

            # 3. Execute each model family with complete fault isolation
            for fam in models_to_run:
                self._update_model_status(run_id, fam, "running", progress=10)
                t0 = time.time()
                mem_start = get_current_process_memory_mb()

                # Start MLflow child run
                child_run_id = None
                try:
                    child_run_id = self.tracker.start_child_run(
                        parent_run_id=parent_run_id,
                        app_run_id=run_id,
                        family=fam,
                        model_name=fam.upper(),
                        backend="CPU",
                        seed=seed,
                    )
                    if child_run_id:
                        mlflow_child_runs[fam] = child_run_id
                except Exception:
                    pass

                try:
                    # Injected failure simulation test (TC-14)
                    if simulate_failure_family == fam:
                        raise RuntimeError(f"Simulated injected failure for family '{fam}' (TC-14)")

                    # Simulated memory limit check (TC-22)
                    if memory_limit_mb is not None and mem_start > memory_limit_mb:
                        raise MemoryError(
                            f"Enforced memory limit of {memory_limit_mb:.1f} MB exceeded (current: {mem_start:.1f} MB)"
                        )

                    if fam == "ml":
                        self._update_model_status(run_id, fam, "running", progress=30)
                        adapter = MLAdapter(
                            feature_cols=selected_features,
                            numeric_cols=numeric_features,
                            categorical_cols=categorical_features,
                            seed=seed,
                        ).fit(X_train, y_train)

                        self._update_model_status(run_id, fam, "running", progress=70)
                        p_val = adapter.predict_proba(X_val)
                        p_test = adapter.predict_proba(X_test)
                        eval_res = evaluate_model_predictions(y_val, p_val, y_test, p_test)

                        runtime_sec = round(time.time() - t0, 2)
                        peak_mem = max(mem_start, get_current_process_memory_mb())

                        desc = adapter.describe()
                        run_record["models"]["ml"] = {
                            "family": "ml",
                            "model_name": desc["model_name"],
                            "status": "completed",
                            "backend": desc["backend"],
                            "seed": seed,
                            "is_multi_seed": False,
                            "threshold": eval_res["threshold"],
                            "threshold_found": eval_res["threshold_found"],
                            "metrics_at_threshold": eval_res["metrics_at_threshold"],
                            "metrics_at_0.5": eval_res["metrics_at_0.5"],
                            "ci95": eval_res["ci95"],
                            "confusion": eval_res["metrics_at_threshold"]["confusion"],
                            "roc_curve": eval_res["roc_curve"],
                            "runtime_sec": runtime_sec,
                            "peak_memory_mb": peak_mem,
                            "hyperparameters": desc["hyperparameters"],
                            "library_versions": desc["library_versions"],
                            "limitations": desc["limitations"],
                        }
                        # Save in-memory adapter for single prediction
                        self.fitted_adapters[f"{run_id}_ml"] = adapter
                        self.active_thresholds[f"{run_id}_ml"] = eval_res["threshold"]

                        # MLflow tracking
                        try:
                            if child_run_id:
                                self.tracker.log_model_parameters(child_run_id, fam, desc)
                                self.tracker.log_model_metrics(
                                    child_run_id=child_run_id,
                                    eval_res=eval_res,
                                    runtime_sec=runtime_sec,
                                    peak_memory_mb=peak_mem,
                                    test_n=int(len(y_test)),
                                    test_prevalence=round(float(np.mean(y_test)), 4),
                                )
                                self.tracker.log_model_artifacts(
                                    child_run_id=child_run_id,
                                    family=fam,
                                    model_record=run_record["models"]["ml"],
                                    adapter=adapter,
                                )
                                self.tracker.end_child_run(child_run_id, status="FINISHED")
                        except Exception:
                            pass

                    elif fam == "dl":
                        self._update_model_status(run_id, fam, "running", progress=25)
                        seeds_to_run = [seed] if single_seed_mode else DEFAULT_SEEDS

                        seed_evals = []
                        last_adapter = None
                        last_eval = None

                        for s_idx, s in enumerate(seeds_to_run):
                            prog = 25 + int(60 * (s_idx / len(seeds_to_run)))
                            self._update_model_status(run_id, fam, "running", progress=prog)

                            dl_ad = DLAdapter(
                                feature_cols=selected_features,
                                numeric_cols=numeric_features,
                                categorical_cols=categorical_features,
                                seed=s,
                                val_data=(X_val, y_val),
                            ).fit(X_train, y_train)

                            pv = dl_ad.predict_proba(X_val)
                            pt = dl_ad.predict_proba(X_test)
                            ev = evaluate_model_predictions(y_val, pv, y_test, pt, compute_ci=(s == seeds_to_run[0]))
                            seed_evals.append(ev)
                            last_adapter = dl_ad
                            last_eval = ev

                            # Log individual seed metrics to MLflow if multi-seed
                            try:
                                if child_run_id and len(seeds_to_run) > 1:
                                    self.tracker.log_seed_metrics(child_run_id, s, ev)
                            except Exception:
                                pass

                        runtime_sec = round(time.time() - t0, 2)
                        peak_mem = max(mem_start, get_current_process_memory_mb())
                        desc = last_adapter.describe()

                        if len(seeds_to_run) > 1:
                            agg = aggregate_seed_metrics(seed_evals)
                            headline_metrics = agg["metrics_at_threshold"]
                            thr_summary = agg["threshold"]
                        else:
                            headline_metrics = {k: {"mean": v, "sd": 0.0} for k, v in last_eval["metrics_at_threshold"].items()}
                            thr_summary = {"mean": last_eval["threshold"], "sd": 0.0}

                        run_record["models"]["dl"] = {
                            "family": "dl",
                            "model_name": desc["model_name"],
                            "status": "completed",
                            "backend": desc["backend"],
                            "seed": seed,
                            "seeds": seeds_to_run,
                            "is_multi_seed": len(seeds_to_run) > 1,
                            "headline_metrics": headline_metrics,
                            "metrics_at_threshold": last_eval["metrics_at_threshold"],
                            "metrics_at_0.5": last_eval["metrics_at_0.5"],
                            "threshold": thr_summary,
                            "confusion": last_eval["metrics_at_threshold"]["confusion"],
                            "roc_curve": last_eval["roc_curve"],
                            "runtime_sec": runtime_sec,
                            "peak_memory_mb": peak_mem,
                            "hyperparameters": desc["hyperparameters"],
                            "library_versions": desc["library_versions"],
                            "limitations": desc["limitations"],
                        }
                        self.fitted_adapters[f"{run_id}_dl"] = last_adapter
                        self.active_thresholds[f"{run_id}_dl"] = float(thr_summary["mean"])

                        # MLflow tracking
                        try:
                            if child_run_id:
                                self.tracker.log_model_parameters(child_run_id, fam, desc)
                                self.tracker.log_model_metrics(
                                    child_run_id=child_run_id,
                                    eval_res=last_eval,
                                    runtime_sec=runtime_sec,
                                    peak_memory_mb=peak_mem,
                                    test_n=int(len(y_test)),
                                    test_prevalence=round(float(np.mean(y_test)), 4),
                                    headline_metrics=headline_metrics,
                                )
                                self.tracker.log_model_artifacts(
                                    child_run_id=child_run_id,
                                    family=fam,
                                    model_record=run_record["models"]["dl"],
                                    adapter=last_adapter,
                                )
                                self.tracker.end_child_run(child_run_id, status="FINISHED")
                        except Exception:
                            pass

                    elif fam == "qml":
                        self._update_model_status(run_id, fam, "running", progress=25)
                        seeds_to_run = [seed] if single_seed_mode else DEFAULT_SEEDS

                        seed_evals = []
                        last_adapter = None
                        last_eval = None

                        for s_idx, s in enumerate(seeds_to_run):
                            prog = 25 + int(60 * (s_idx / len(seeds_to_run)))
                            self._update_model_status(run_id, fam, "running", progress=prog)

                            qml_ad = QMLAdapter(
                                feature_cols=selected_features,
                                numeric_cols=numeric_features,
                                categorical_cols=categorical_features,
                                seed=s,
                                epochs=15,
                                subsample_n=1500,
                            ).fit(X_train, y_train)

                            pv = qml_ad.predict_proba(X_val)
                            pt = qml_ad.predict_proba(X_test)
                            ev = evaluate_model_predictions(y_val, pv, y_test, pt, compute_ci=(s == seeds_to_run[0]))
                            seed_evals.append(ev)
                            last_adapter = qml_ad
                            last_eval = ev

                            # Log individual seed metrics to MLflow if multi-seed
                            try:
                                if child_run_id and len(seeds_to_run) > 1:
                                    self.tracker.log_seed_metrics(child_run_id, s, ev)
                            except Exception:
                                pass

                        runtime_sec = round(time.time() - t0, 2)
                        peak_mem = max(mem_start, get_current_process_memory_mb())
                        desc = last_adapter.describe()

                        if len(seeds_to_run) > 1:
                            agg = aggregate_seed_metrics(seed_evals)
                            headline_metrics = agg["metrics_at_threshold"]
                            thr_summary = agg["threshold"]
                        else:
                            headline_metrics = {k: {"mean": v, "sd": 0.0} for k, v in last_eval["metrics_at_threshold"].items()}
                            thr_summary = {"mean": last_eval["threshold"], "sd": 0.0}

                        run_record["models"]["qml"] = {
                            "family": "qml",
                            "model_name": desc["model_name"],
                            "status": "completed",
                            "backend": desc["backend"],
                            "seed": seed,
                            "seeds": seeds_to_run,
                            "is_multi_seed": len(seeds_to_run) > 1,
                            "headline_metrics": headline_metrics,
                            "metrics_at_threshold": last_eval["metrics_at_threshold"],
                            "metrics_at_0.5": last_eval["metrics_at_0.5"],
                            "threshold": thr_summary,
                            "confusion": last_eval["metrics_at_threshold"]["confusion"],
                            "roc_curve": last_eval["roc_curve"],
                            "runtime_sec": runtime_sec,
                            "peak_memory_mb": peak_mem,
                            "hyperparameters": desc["hyperparameters"],
                            "circuit_diagram": desc.get("circuit_diagram"),
                            "library_versions": desc["library_versions"],
                            "limitations": desc["limitations"],
                        }
                        self.fitted_adapters[f"{run_id}_qml"] = last_adapter
                        self.active_thresholds[f"{run_id}_qml"] = float(thr_summary["mean"])

                        # MLflow tracking
                        try:
                            if child_run_id:
                                self.tracker.log_model_parameters(child_run_id, fam, desc)
                                self.tracker.log_model_metrics(
                                    child_run_id=child_run_id,
                                    eval_res=last_eval,
                                    runtime_sec=runtime_sec,
                                    peak_memory_mb=peak_mem,
                                    test_n=int(len(y_test)),
                                    test_prevalence=round(float(np.mean(y_test)), 4),
                                    headline_metrics=headline_metrics,
                                )
                                self.tracker.log_model_artifacts(
                                    child_run_id=child_run_id,
                                    family=fam,
                                    model_record=run_record["models"]["qml"],
                                    adapter=last_adapter,
                                )
                                self.tracker.end_child_run(child_run_id, status="FINISHED")
                        except Exception:
                            pass

                    self._update_model_status(
                        run_id,
                        fam,
                        "completed",
                        progress=100,
                        runtime_sec=round(time.time() - t0, 2),
                        peak_memory_mb=max(mem_start, get_current_process_memory_mb()),
                    )

                except Exception as ex:
                    # Failure isolation: log error, mark this model failed, but do not stop others
                    runtime_sec = round(time.time() - t0, 2)
                    err_msg = str(ex)
                    run_record["models"][fam] = {
                        "family": fam,
                        "status": "failed",
                        "error": err_msg,
                        "runtime_sec": runtime_sec,
                        "peak_memory_mb": max(mem_start, get_current_process_memory_mb()),
                    }
                    self._update_model_status(
                        run_id,
                        fam,
                        "failed",
                        progress=100,
                        runtime_sec=runtime_sec,
                        error=err_msg,
                    )
                    # Record failure in MLflow child run
                    try:
                        if child_run_id:
                            self.tracker.record_child_failure(child_run_id, err_msg)
                    except Exception:
                        pass

            # Record MLflow run IDs in run record for traceability
            if parent_run_id or mlflow_child_runs:
                run_record["mlflow"] = {
                    "tracking_enabled": self.tracker.enabled,
                    "parent_run_id": parent_run_id,
                    "child_run_ids": mlflow_child_runs,
                    "experiment_name": self.tracker.experiment_name,
                }

            # Determine overall parent status
            has_completed = any(m.get("status") == "completed" for m in run_record["models"].values())
            has_failed = any(m.get("status") == "failed" for m in run_record["models"].values())

            parent_status = "FINISHED"
            completion_tag = "full_success"
            if has_failed and has_completed:
                parent_status = "FINISHED"
                completion_tag = "partial_completion"
            elif has_failed and not has_completed:
                parent_status = "FAILED"
                completion_tag = "all_failed"

            try:
                if parent_run_id:
                    self.tracker.end_parent_run(
                        parent_run_id=parent_run_id,
                        status=parent_status,
                        tags={"completion_status": completion_tag},
                        run_record=run_record,
                    )
            except Exception:
                pass

            # 4. Save run record atomically
            self.store.save_run(run_record)


            with self.lock:
                if run_id in self.run_status_cache:
                    has_completed = any(m["status"] == "completed" for m in self.run_status_cache[run_id]["models"])
                    self.run_status_cache[run_id]["status"] = "completed" if has_completed else "failed"

        except Exception as e:
            with self.lock:
                if run_id in self.run_status_cache:
                    self.run_status_cache[run_id]["status"] = "failed"
                    self.run_status_cache[run_id]["error"] = str(e)
        finally:
            with self.lock:
                self.active_run_id = None

    def _update_model_status(
        self,
        run_id: str,
        family: str,
        status: str,
        progress: int = 0,
        runtime_sec: float = 0.0,
        peak_memory_mb: float = 0.0,
        error: Optional[str] = None,
    ) -> None:
        with self.lock:
            if run_id in self.run_status_cache:
                for m in self.run_status_cache[run_id]["models"]:
                    if m["family"] == family:
                        m["status"] = status
                        m["progress"] = progress
                        if runtime_sec > 0:
                            m["runtime_sec"] = runtime_sec
                        if peak_memory_mb > 0:
                            m["peak_memory_mb"] = peak_memory_mb
                        if error:
                            m["error"] = error
                        break

    def predict_single_record(
        self,
        run_id: str,
        family: str,
        record: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validates input fields and evaluates prediction using a fitted model adapter.
        Blocks execution and returns field-level errors for invalid records.
        """
        adapter_key = f"{run_id}_{family}"
        adapter = self.fitted_adapters.get(adapter_key)

        # If not in-memory, fall back to checking if reference ML run can be initialized
        if adapter is None and family == "ml":
            # Lazy initialize ML adapter using train data
            train_path = PROJECT_ROOT / "data" / "splits" / "train.csv"
            if not train_path.exists():
                train_path = PROJECT_ROOT / "train.csv"
            if train_path.exists():
                train_df = pd.read_csv(train_path)
                shared_features = DEFAULT_SHARED_FEATURES
                X_tr = train_df[shared_features]
                y_tr = (train_df[TARGET_COLUMN] == POSITIVE_CLASS).astype(int).to_numpy()
                num_cols = ["RIDAGEYR", "DMDHHSZE", "BMXWAIST", "BMXBMI"]
                cat_cols = ["DMDHRAGZ"]
                adapter = MLAdapter(shared_features, num_cols, cat_cols, seed=42).fit(X_tr, y_tr)
                self.fitted_adapters[adapter_key] = adapter
                self.active_thresholds[adapter_key] = 0.5897

        if adapter is None:
            raise RuntimeError(
                f"No fitted model pipeline available for family '{family}' and run '{run_id}'. Please run the model first."
            )

        threshold = self.active_thresholds.get(adapter_key, 0.5)

        # Field validation
        expected_fields = DEFAULT_SHARED_FEATURES
        errors: List[Dict[str, str]] = []
        parsed_record: Dict[str, float] = {}

        for f in expected_fields:
            if f not in record:
                errors.append({"field": f, "error": f"Required field '{f}' is missing"})
                continue
            val = record[f]
            try:
                f_val = float(val)
                if not np.isfinite(f_val):
                    errors.append({"field": f, "error": f"Value must be a finite number, got {val}"})
                elif f == "RIDAGEYR" and (f_val < 0 or f_val > 120):
                    errors.append({"field": f, "error": f"Age must be between 0 and 120, got {f_val}"})
                elif f == "BMXBMI" and (f_val < 10 or f_val > 100):
                    errors.append({"field": f, "error": f"BMI must be between 10 and 100, got {f_val}"})
                elif f == "BMXWAIST" and (f_val < 30 or f_val > 250):
                    errors.append({"field": f, "error": f"Waist circumference must be between 30 and 250 cm, got {f_val}"})
                else:
                    parsed_record[f] = f_val
            except (ValueError, TypeError):
                errors.append({"field": f, "error": f"Field '{f}' must be numeric, got '{val}'"})

        if errors:
            return {
                "valid": False,
                "errors": errors,
            }

        # Predict
        df_single = pd.DataFrame([parsed_record])
        prob = float(adapter.predict_proba(df_single)[0])
        label = POSITIVE_CLASS if prob >= threshold else NEGATIVE_CLASS

        return {
            "valid": True,
            "model": family.upper(),
            "score": round(prob, 4),
            "label": label,
            "threshold": round(threshold, 4),
            "run_id": run_id,
            "warning": "Research/educational use only. Not a diagnosis or medical advice.",
            "interpretation": (
                "Cross-sectional survey classification estimate. Indicates feature pattern similarity "
                "to NHANES participants with HbA1c between 5.7% and 6.4%."
            ),
        }
