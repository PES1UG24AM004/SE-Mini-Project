"""
MLflow Experiment Tracking Module for CodeCraft Early Metabolic Risk Platform.

Provides safe, modular, and fail-safe experiment tracking integrating:
- Hierarchical Parent (Training Run) and Child (Model Family) runs
- Dynamic hyperparameter logging from ModelAdapter.describe()
- Evaluator metric logging (Accuracy, Sensitivity, Specificity, ROC-AUC, CIs, Confusion)
- Reproducible artifact tracking (Metadata, Metrics, ROC Curves, Circuit Diagrams, Models)
- Local SQLite and Remote Tracking Server support
- Strict data privacy guardrails preventing any PHI / participant data leakage
"""
import json
import logging
import math
import os
import sys
import tempfile
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# Configure module logger
os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
logger = logging.getLogger("codecraft.mlflow_tracker")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [MLFLOW] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def sanitize_tracking_uri(uri: str) -> str:
    """Removes user credentials from tracking URI for safe display."""
    if not uri:
        return ""
    try:
        parsed = urllib.parse.urlsplit(uri)
        if parsed.username or parsed.password:
            netloc = parsed.hostname or ""
            if parsed.port:
                netloc += f":{parsed.port}"
            return urllib.parse.urlunsplit(
                (parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment)
            )
        return uri
    except Exception:
        return "invalid-uri"


def get_git_commit_sha() -> str:
    """Safely retrieves current git commit SHA."""
    try:
        import subprocess
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2.0,
        ).strip()
        return out if out else "unknown"
    except Exception:
        return "unknown"


def is_finite_numeric(val: Any) -> bool:
    """Returns True if val is a valid finite float or int."""
    if val is None or isinstance(val, bool):
        return False
    if isinstance(val, (int, float, np.integer, np.floating)):
        return not (math.isnan(val) or math.isinf(val))
    return False


def check_server_connectivity(tracking_uri: str, timeout: float = 0.3) -> Tuple[bool, Optional[str]]:
    """
    Performs an immediate pre-flight connectivity check to avoid long client retry delays
    when a remote or local HTTP tracking server is down.
    """
    if not tracking_uri:
        return False, "Tracking URI is empty."
    try:
        parsed = urllib.parse.urlsplit(tracking_uri)
        if parsed.scheme in ("http", "https"):
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            import socket
            with socket.create_connection((host, port), timeout=timeout):
                return True, None
        elif parsed.scheme in ("sqlite", "file", ""):
            return True, None
        return True, None
    except Exception as e:
        safe_uri = sanitize_tracking_uri(tracking_uri)
        return False, f"Cannot connect to tracking endpoint '{safe_uri}': {e}"




class MLflowTracker:
    """
    Fail-safe MLflow experiment tracker.
    
    Guarantees that no MLflow error or tracking server outage can disrupt
    model training, inference, or ResultsStore persistence.
    """

    def __init__(
        self,
        enabled: Optional[bool] = None,
        tracking_uri: Optional[str] = None,
        experiment_name: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.enabled = (
            enabled
            if enabled is not None
            else (
                os.environ.get("MLFLOW_ENABLED", "true").lower()
                in ("true", "1", "yes")
            )
        )
        self.tracking_uri = (
            tracking_uri
            or os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
        )
        self.experiment_name = (
            experiment_name
            or os.environ.get(
                "MLFLOW_EXPERIMENT_NAME",
                "CodeCraft-Metabolic-Risk-Benchmark",
            )
        )
        self.username = username or os.environ.get("MLFLOW_TRACKING_USERNAME", "")
        self.password = password or os.environ.get("MLFLOW_TRACKING_PASSWORD", "")

        self._mlflow_lib: Optional[Any] = None
        self._client: Optional[Any] = None
        self._experiment_id: Optional[str] = None
        self._initialized: bool = False
        self._last_error: Optional[str] = None

    def _setup_credentials(self) -> None:
        """Sets tracking credentials in environment if provided."""
        if self.username:
            os.environ["MLFLOW_TRACKING_USERNAME"] = self.username
        if self.password:
            os.environ["MLFLOW_TRACKING_PASSWORD"] = self.password

    def _get_mlflow(self) -> Optional[Any]:
        """Lazy loads MLflow library safely."""
        if self._mlflow_lib is None:
            try:
                import mlflow
                self._mlflow_lib = mlflow
            except ImportError as e:
                self._last_error = f"MLflow library is not installed: {e}"
                logger.warning(self._last_error)
                return None
        return self._mlflow_lib

    def check_status(self) -> Dict[str, Any]:
        """
        Tests tracking configuration and server connectivity.
        Returns safe status dictionary without credentials or db secrets.
        """
        safe_uri = sanitize_tracking_uri(self.tracking_uri)
        if not self.enabled:
            return {
                "enabled": False,
                "available": False,
                "tracking_uri": safe_uri,
                "experiment_name": self.experiment_name,
                "active_experiment_id": None,
                "ui_url": self._get_ui_url(),
                "error": "MLflow tracking is disabled via configuration (MLFLOW_ENABLED=false).",
            }

        mlflow_lib = self._get_mlflow()
        if mlflow_lib is None:
            return {
                "enabled": True,
                "available": False,
                "tracking_uri": safe_uri,
                "experiment_name": self.experiment_name,
                "active_experiment_id": None,
                "ui_url": self._get_ui_url(),
                "error": self._last_error or "MLflow package not installed.",
            }

        # Pre-flight check
        conn_ok, conn_err = check_server_connectivity(self.tracking_uri, timeout=0.5)
        if not conn_ok:
            self._last_error = conn_err
            return {
                "enabled": True,
                "available": False,
                "tracking_uri": safe_uri,
                "experiment_name": self.experiment_name,
                "active_experiment_id": None,
                "ui_url": self._get_ui_url(),
                "error": conn_err,
            }

        try:
            self._setup_credentials()

            mlflow_lib.set_tracking_uri(self.tracking_uri)
            from mlflow.tracking import MlflowClient

            client = MlflowClient(tracking_uri=self.tracking_uri)

            # Test connection with search_experiments
            exp = client.get_experiment_by_name(self.experiment_name)
            exp_id = exp.experiment_id if exp else None

            self._client = client
            self._experiment_id = exp_id
            self._last_error = None

            return {
                "enabled": True,
                "available": True,
                "tracking_uri": safe_uri,
                "experiment_name": self.experiment_name,
                "active_experiment_id": exp_id,
                "ui_url": self._get_ui_url(),
                "error": None,
            }
        except Exception as e:
            err_msg = f"Unable to connect to MLflow tracking server at '{safe_uri}': {str(e)}"
            self._last_error = err_msg
            logger.warning(err_msg)
            return {
                "enabled": True,
                "available": False,
                "tracking_uri": safe_uri,
                "experiment_name": self.experiment_name,
                "active_experiment_id": None,
                "ui_url": self._get_ui_url(),
                "error": err_msg,
            }

    def _get_ui_url(self) -> Optional[str]:
        """Derives the user-facing UI URL from tracking URI."""
        if not self.tracking_uri:
            return None
        safe_uri = sanitize_tracking_uri(self.tracking_uri)
        if safe_uri.startswith(("http://", "https://")):
            return safe_uri
        return None

    def initialize(self) -> bool:
        """Initializes connection to tracking server and ensures experiment exists."""
        if not self.enabled:
            return False

        status = self.check_status()
        if not status["available"]:
            return False

        try:
            client = self._client
            exp = client.get_experiment_by_name(self.experiment_name)
            if exp is None:
                exp_id = client.create_experiment(self.experiment_name)
                logger.info("Created MLflow experiment '%s' (ID: %s)", self.experiment_name, exp_id)
            else:
                exp_id = exp.experiment_id
            self._experiment_id = exp_id
            self._initialized = True
            return True
        except Exception as e:
            self._last_error = f"Failed to initialize experiment: {str(e)}"
            logger.warning(self._last_error)
            return False

    # ---------- PARENT RUN MANAGEMENT ----------

    def start_parent_run(
        self,
        app_run_id: str,
        dataset_version: str,
        split_hash: str,
        split_protocol: str,
        seed: int,
        single_seed_mode: bool,
        models_to_run: List[str],
        selected_features: List[str],
        transformed_dim: int,
        n_train: int,
        n_val: int,
        n_test: int,
        ranking_metric: str,
    ) -> Optional[str]:
        """
        Creates and starts a parent MLflow run for the application training execution.
        Returns parent MLflow run_id, or None on failure.
        """
        if not self.enabled or not self.initialize():
            return None

        try:
            client = self._client
            tags = {
                "app_run_id": app_run_id,
                "run_type": "parent",
                "application": "CodeCraft",
                "app_version": "1.0.0",
                "python_version": sys.version.split()[0],
                "git_commit": get_git_commit_sha(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "dataset_version": dataset_version,
                "split_hash": split_hash,
                "single_seed_mode": str(single_seed_mode).lower(),
                "ranking_metric": ranking_metric,
            }

            run = client.create_run(
                experiment_id=self._experiment_id,
                run_name=f"CodeCraft-{app_run_id}",
                tags=tags,
            )
            parent_run_id = run.info.run_id

            # Log parent parameters
            params = {
                "dataset_version": dataset_version,
                "split_hash": split_hash,
                "split_protocol": split_protocol[:250],
                "initial_seed": str(seed),
                "single_seed_mode": str(single_seed_mode),
                "models_to_run": ",".join(models_to_run),
                "n_selected_features": str(len(selected_features)),
                "raw_features": ",".join(selected_features)[:500],
                "transformed_dimension": str(transformed_dim),
                "n_train": str(n_train),
                "n_val": str(n_val),
                "n_test": str(n_test),
                "ranking_metric": ranking_metric,
            }
            for k, v in params.items():
                try:
                    client.log_param(parent_run_id, k, v)
                except Exception:
                    pass

            logger.info("Started parent MLflow run %s for app_run %s", parent_run_id, app_run_id)
            return parent_run_id

        except Exception as e:
            logger.warning("Failed to start parent MLflow run: %s", e)
            return None

    def end_parent_run(
        self,
        parent_run_id: Optional[str],
        status: str = "FINISHED",
        tags: Optional[Dict[str, str]] = None,
        run_record: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Finishes the parent run and logs experiment summary artifact."""
        if not parent_run_id or not self._client:
            return

        try:
            client = self._client
            if tags:
                for k, v in tags.items():
                    client.set_tag(parent_run_id, k, str(v))

            # Log safe experiment summary artifact if run_record provided
            if run_record:
                summary_data = {
                    "app_run_id": run_record.get("run_id"),
                    "status": run_record.get("status"),
                    "created_at": run_record.get("created_at"),
                    "dataset_version": run_record.get("dataset_version"),
                    "split_hash": run_record.get("split_hash"),
                    "seed": run_record.get("seed"),
                    "ranking_metric": run_record.get("ranking_metric"),
                    "models_evaluated": list(run_record.get("models", {}).keys()),
                    "models_summary": {
                        fam: {
                            "status": m.get("status"),
                            "runtime_sec": m.get("runtime_sec"),
                            "peak_memory_mb": m.get("peak_memory_mb"),
                            "error": m.get("error"),
                        }
                        for fam, m in run_record.get("models", {}).items()
                    },
                }
                with tempfile.TemporaryDirectory() as tmp_dir:
                    sum_file = Path(tmp_dir) / "experiment_summary.json"
                    sum_file.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")
                    client.log_artifact(parent_run_id, str(sum_file))

            client.set_terminated(parent_run_id, status=status)
            logger.info("Terminated parent MLflow run %s with status %s", parent_run_id, status)
        except Exception as e:
            logger.warning("Failed to terminate parent MLflow run %s: %s", parent_run_id, e)

    # ---------- CHILD RUN MANAGEMENT ----------

    def start_child_run(
        self,
        parent_run_id: Optional[str],
        app_run_id: str,
        family: str,
        model_name: str,
        backend: str,
        seed: int,
    ) -> Optional[str]:
        """
        Creates a nested child MLflow run linked to parent_run_id.
        Returns child run_id or None.
        """
        if not self.enabled or not self._client:
            return None

        try:
            client = self._client
            tags = {
                "app_run_id": app_run_id,
                "run_type": "child",
                "family": family,
                "model_name": model_name,
                "backend": backend,
                "seed": str(seed),
            }
            if parent_run_id:
                tags["mlflow.parentRunId"] = parent_run_id

            child_run = client.create_run(
                experiment_id=self._experiment_id,
                run_name=f"{family.upper()}-{app_run_id}",
                tags=tags,
            )
            child_run_id = child_run.info.run_id
            logger.info("Started child MLflow run %s for family %s", child_run_id, family)
            return child_run_id
        except Exception as e:
            logger.warning("Failed to create child MLflow run for family %s: %s", family, e)
            return None

    def log_model_parameters(
        self,
        child_run_id: Optional[str],
        family: str,
        adapter_desc: Dict[str, Any],
    ) -> None:
        """
        Dynamically extracts and logs hyperparameters and backend configuration
        from the adapter's describe() output.
        """
        if not child_run_id or not self._client:
            return

        try:
            client = self._client
            # Base parameters common to all adapters
            params = {
                "family": family,
                "model_name": str(adapter_desc.get("model_name", "")),
                "backend": str(adapter_desc.get("backend", "")),
                "seed": str(adapter_desc.get("seed", "")),
                "n_features": str(adapter_desc.get("n_features", "")),
                "n_transformed_features": str(adapter_desc.get("n_transformed_features", "")),
            }

            # Hyperparameters from adapter describe()
            raw_hparams = adapter_desc.get("hyperparameters", {})
            for k, v in raw_hparams.items():
                if isinstance(v, (list, tuple)):
                    params[f"hp_{k}"] = json.dumps(v)[:500]
                elif isinstance(v, dict):
                    params[f"hp_{k}"] = json.dumps(v)[:500]
                else:
                    params[f"hp_{k}"] = str(v)[:500]

            # Specialized parameters per family
            if family == "ml":
                params["model_type"] = "HistGradientBoostingClassifier"
                if "feature_set" in adapter_desc:
                    params["feature_set"] = ",".join(adapter_desc["feature_set"])[:500]

            elif family == "dl":
                params["model_type"] = "PyTorch_MLP"
                if "device" in adapter_desc:
                    params["device"] = str(adapter_desc["device"])

            elif family == "qml":
                params["model_type"] = "PennyLane_VQC"
                params["n_qubits"] = str(adapter_desc.get("n_qubits", 8))
                params["n_trainable_params"] = str(adapter_desc.get("n_trainable_parameters", 50))

            for k, v in params.items():
                if v != "":
                    try:
                        client.log_param(child_run_id, k, v)
                    except Exception:
                        pass

        except Exception as e:
            logger.warning("Failed to log parameters for run %s: %s", child_run_id, e)

    def log_model_metrics(
        self,
        child_run_id: Optional[str],
        eval_res: Dict[str, Any],
        runtime_sec: float,
        peak_memory_mb: float,
        test_n: Optional[int] = None,
        test_prevalence: Optional[float] = None,
        headline_metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Logs evaluation metrics to child run:
        - Accuracy, precision, sensitivity, specificity, f1, roc_auc
        - Decision threshold, runtime_sec, peak_memory_mb
        - Metrics at threshold 0.5
        - Confusion matrix components
        - Bootstrap confidence intervals (ci95)
        - Multi-seed aggregate metrics (mean & sd)
        """
        if not child_run_id or not self._client:
            return

        try:
            client = self._client
            metrics_to_log: Dict[str, float] = {}

            # Runtime and memory
            if is_finite_numeric(runtime_sec):
                metrics_to_log["runtime_sec"] = float(runtime_sec)
            if is_finite_numeric(peak_memory_mb):
                metrics_to_log["peak_memory_mb"] = float(peak_memory_mb)

            # Sample statistics
            if is_finite_numeric(test_n):
                metrics_to_log["test_n"] = float(test_n)
            if is_finite_numeric(test_prevalence):
                metrics_to_log["test_prevalence"] = float(test_prevalence)

            # Decision threshold
            thr = eval_res.get("threshold")
            if isinstance(thr, dict):
                # Multi-seed threshold summary {"mean": ..., "sd": ...}
                if is_finite_numeric(thr.get("mean")):
                    metrics_to_log["threshold_mean"] = float(thr["mean"])
                if is_finite_numeric(thr.get("sd")):
                    metrics_to_log["threshold_sd"] = float(thr["sd"])
            elif is_finite_numeric(thr):
                metrics_to_log["decision_threshold"] = float(thr)

            # Metrics at selected threshold
            m_thr = eval_res.get("metrics_at_threshold", {})
            for k in ["accuracy", "precision", "sensitivity", "specificity", "f1", "roc_auc"]:
                val = m_thr.get(k)
                if is_finite_numeric(val):
                    metrics_to_log[k] = float(val)

            # Metrics at threshold 0.5
            m_05 = eval_res.get("metrics_at_0.5", {})
            for k in ["accuracy", "precision", "sensitivity", "specificity", "f1", "roc_auc"]:
                val = m_05.get(k)
                if is_finite_numeric(val):
                    metrics_to_log[f"threshold_0.5_{k}"] = float(val)

            # Confusion matrix
            cm = m_thr.get("confusion")
            if cm and len(cm) == 2 and len(cm[0]) == 2 and len(cm[1]) == 2:
                tn, fp = cm[0]
                fn, tp = cm[1]
                if is_finite_numeric(tn):
                    metrics_to_log["confusion_tn"] = float(tn)
                if is_finite_numeric(fp):
                    metrics_to_log["confusion_fp"] = float(fp)
                if is_finite_numeric(fn):
                    metrics_to_log["confusion_fn"] = float(fn)
                if is_finite_numeric(tp):
                    metrics_to_log["confusion_tp"] = float(tp)

            # Bootstrap Confidence Intervals (ci95)
            ci95 = eval_res.get("ci95", {})
            if isinstance(ci95, dict):
                for metric_key, bounds in ci95.items():
                    if bounds and len(bounds) == 2:
                        low, high = bounds
                        if is_finite_numeric(low):
                            metrics_to_log[f"ci95_{metric_key}_low"] = float(low)
                        if is_finite_numeric(high):
                            metrics_to_log[f"ci95_{metric_key}_high"] = float(high)

            # Headline aggregate metrics (for multi-seed DL / QML)
            if headline_metrics and isinstance(headline_metrics, dict):
                for k, stats in headline_metrics.items():
                    if isinstance(stats, dict):
                        if is_finite_numeric(stats.get("mean")):
                            metrics_to_log[f"{k}_mean"] = float(stats["mean"])
                        if is_finite_numeric(stats.get("sd")):
                            metrics_to_log[f"{k}_sd"] = float(stats["sd"])
                    elif is_finite_numeric(stats):
                        metrics_to_log[f"{k}_mean"] = float(stats)

            # Execute logging of all finite numeric metrics
            for k, v in metrics_to_log.items():
                try:
                    client.log_metric(child_run_id, k, v)
                except Exception:
                    pass

            logger.info("Logged %d metrics for child run %s", len(metrics_to_log), child_run_id)

        except Exception as e:
            logger.warning("Failed to log metrics for child run %s: %s", child_run_id, e)

    def log_seed_metrics(
        self,
        child_run_id: Optional[str],
        seed: int,
        seed_eval: Dict[str, Any],
    ) -> None:
        """Logs metrics for an individual seed within a multi-seed experiment."""
        if not child_run_id or not self._client:
            return

        try:
            client = self._client
            m_thr = seed_eval.get("metrics_at_threshold", {})
            for k in ["sensitivity", "specificity", "precision", "f1", "accuracy", "roc_auc"]:
                val = m_thr.get(k)
                if is_finite_numeric(val):
                    metric_name = f"seed_{seed}_{k}"
                    try:
                        client.log_metric(child_run_id, metric_name, float(val))
                    except Exception:
                        pass
            if is_finite_numeric(seed_eval.get("threshold")):
                try:
                    client.log_metric(child_run_id, f"seed_{seed}_threshold", float(seed_eval["threshold"]))
                except Exception:
                    pass
        except Exception as e:
            logger.warning("Failed to log seed %s metrics for child run %s: %s", seed, child_run_id, e)

    def log_model_artifacts(
        self,
        child_run_id: Optional[str],
        family: str,
        model_record: Dict[str, Any],
        adapter: Optional[Any] = None,
    ) -> None:
        """
        Logs safe, reproducible experiment artifacts:
        - model_metadata.json
        - hyperparameters.json
        - evaluation_metrics.json
        - roc_curve.json
        - circuit_diagram.txt (for QML)
        - model artifact serialization with reloading test
        
        Strict Privacy Guardrail:
        Never logs raw participant records, user CSVs, or individual patient data.
        """
        if not child_run_id or not self._client:
            return

        try:
            client = self._client
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)

                # 1. model_metadata.json
                meta = {
                    "family": family,
                    "model_name": model_record.get("model_name"),
                    "backend": model_record.get("backend"),
                    "seed": model_record.get("seed"),
                    "seeds": model_record.get("seeds"),
                    "is_multi_seed": model_record.get("is_multi_seed", False),
                    "runtime_sec": model_record.get("runtime_sec"),
                    "peak_memory_mb": model_record.get("peak_memory_mb"),
                    "library_versions": model_record.get("library_versions"),
                    "limitations": model_record.get("limitations", []),
                }
                (tmp_path / "model_metadata.json").write_text(
                    json.dumps(meta, indent=2), encoding="utf-8"
                )
                client.log_artifact(child_run_id, str(tmp_path / "model_metadata.json"))

                # 2. hyperparameters.json
                if "hyperparameters" in model_record:
                    (tmp_path / "hyperparameters.json").write_text(
                        json.dumps(model_record["hyperparameters"], indent=2),
                        encoding="utf-8",
                    )
                    client.log_artifact(child_run_id, str(tmp_path / "hyperparameters.json"))

                # 3. evaluation_metrics.json
                metrics_summary = {
                    "threshold": model_record.get("threshold"),
                    "metrics_at_threshold": model_record.get("metrics_at_threshold"),
                    "metrics_at_0.5": model_record.get("metrics_at_0.5"),
                    "headline_metrics": model_record.get("headline_metrics"),
                    "ci95": model_record.get("ci95"),
                    "confusion": model_record.get("confusion"),
                }
                (tmp_path / "evaluation_metrics.json").write_text(
                    json.dumps(metrics_summary, indent=2), encoding="utf-8"
                )
                client.log_artifact(child_run_id, str(tmp_path / "evaluation_metrics.json"))

                # 4. roc_curve.json
                if "roc_curve" in model_record and model_record["roc_curve"]:
                    (tmp_path / "roc_curve.json").write_text(
                        json.dumps(model_record["roc_curve"], indent=2), encoding="utf-8"
                    )
                    client.log_artifact(child_run_id, str(tmp_path / "roc_curve.json"))

                # 5. QML circuit diagram (if QML)
                if family == "qml" and model_record.get("circuit_diagram"):
                    (tmp_path / "circuit_diagram.txt").write_text(
                        model_record["circuit_diagram"], encoding="utf-8"
                    )
                    client.log_artifact(child_run_id, str(tmp_path / "circuit_diagram.txt"))

                # 6. Model Artifact Serialization & Reload Verification
                if adapter is not None:
                    try:
                        self._log_and_verify_model_artifact(
                            child_run_id=child_run_id,
                            family=family,
                            adapter=adapter,
                            tmp_path=tmp_path,
                        )
                    except Exception as model_err:
                        logger.warning(
                            "Model artifact serialization skipped for %s: %s",
                            family,
                            model_err,
                        )

            logger.info("Successfully logged artifacts for child run %s", child_run_id)

        except Exception as e:
            logger.warning("Failed to log artifacts for child run %s: %s", child_run_id, e)

    def _log_and_verify_model_artifact(
        self,
        child_run_id: str,
        family: str,
        adapter: Any,
        tmp_path: Path,
    ) -> None:
        """Serializes model weights and architecture, and verifies reloadability."""
        client = self._client
        mlflow_lib = self._mlflow_lib

        if family == "ml":
            # For classical ML: Save classifier and preprocessor metadata
            if hasattr(adapter, "classifier_") and adapter.classifier_ is not None:
                model_dir = tmp_path / "ml_model"
                model_dir.mkdir(parents=True, exist_ok=True)
                import joblib

                joblib.dump(adapter.classifier_, model_dir / "classifier.joblib")
                prep_meta = {
                    "feature_cols": adapter.feature_cols,
                    "numeric_cols": adapter.numeric_cols,
                    "categorical_cols": adapter.categorical_cols,
                    "seed": adapter.seed,
                    "model_class": "HistGradientBoostingClassifier",
                }
                (model_dir / "preprocessor_meta.json").write_text(
                    json.dumps(prep_meta, indent=2), encoding="utf-8"
                )

                # Verify reload
                loaded_clf = joblib.load(model_dir / "classifier.joblib")
                assert hasattr(loaded_clf, "predict_proba"), "Reloaded ML model missing predict_proba"

                client.log_artifacts(child_run_id, str(model_dir), artifact_path="model")

        elif family == "dl":
            # For DL: Save PyTorch state_dict and architecture configuration
            if hasattr(adapter, "model_") and adapter.model_ is not None:
                import torch

                model_dir = tmp_path / "dl_model"
                model_dir.mkdir(parents=True, exist_ok=True)
                torch.save(adapter.model_.state_dict(), model_dir / "weights.pt")

                arch_meta = {
                    "hidden": adapter.hidden,
                    "dropout": adapter.dropout,
                    "feature_cols": adapter.feature_cols,
                    "numeric_cols": adapter.numeric_cols,
                    "categorical_cols": adapter.categorical_cols,
                    "seed": adapter.seed,
                }
                (model_dir / "architecture.json").write_text(
                    json.dumps(arch_meta, indent=2), encoding="utf-8"
                )

                # Verify reload
                weights = torch.load(model_dir / "weights.pt", weights_only=True)
                assert weights is not None, "Reloaded DL weights empty"

                client.log_artifacts(child_run_id, str(model_dir), artifact_path="model")

        elif family == "qml":
            # For QML: Save variational weights, scale, bias, and circuit metadata
            if hasattr(adapter, "weights_") and adapter.weights_ is not None:
                import torch

                model_dir = tmp_path / "qml_model"
                model_dir.mkdir(parents=True, exist_ok=True)
                qml_state = {
                    "weights": adapter.weights_.detach().cpu(),
                    "scale_a": adapter.scale_a_.detach().cpu() if adapter.scale_a_ is not None else None,
                    "bias_b": adapter.bias_b_.detach().cpu() if adapter.bias_b_ is not None else None,
                }
                torch.save(qml_state, model_dir / "variational_weights.pt")

                qml_meta = {
                    "n_layers": adapter.n_layers,
                    "ansatz": "StronglyEntanglingLayers",
                    "embedding": "AngleEmbedding",
                    "feature_cols": adapter.feature_cols,
                    "seed": adapter.seed,
                }
                (model_dir / "qml_config.json").write_text(
                    json.dumps(qml_meta, indent=2), encoding="utf-8"
                )

                # Verify reload
                reloaded = torch.load(model_dir / "variational_weights.pt", weights_only=False)
                assert "weights" in reloaded, "Reloaded QML weights missing"

                client.log_artifacts(child_run_id, str(model_dir), artifact_path="model")

    def end_child_run(
        self,
        child_run_id: Optional[str],
        status: str = "FINISHED",
    ) -> None:
        """Finishes the child run with the given status."""
        if not child_run_id or not self._client:
            return

        try:
            self._client.set_terminated(child_run_id, status=status)
            logger.info("Terminated child MLflow run %s with status %s", child_run_id, status)
        except Exception as e:
            logger.warning("Failed to terminate child MLflow run %s: %s", child_run_id, e)

    def record_child_failure(
        self,
        child_run_id: Optional[str],
        error_message: str,
    ) -> None:
        """Marks a child run as FAILED and tags the error message."""
        if not child_run_id or not self._client:
            return

        try:
            safe_error = str(error_message)[:500]
            self._client.set_tag(child_run_id, "status", "failed")
            self._client.set_tag(child_run_id, "error", safe_error)
            self._client.set_terminated(child_run_id, status="FAILED")
            logger.info("Recorded failure for child MLflow run %s: %s", child_run_id, safe_error)
        except Exception as e:
            logger.warning("Failed to record failure for child run %s: %s", child_run_id, e)


# Global singleton instance for convenient import
_tracker_instance: Optional[MLflowTracker] = None


def get_tracker() -> MLflowTracker:
    """Returns singleton MLflowTracker configured from environment."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = MLflowTracker()
    return _tracker_instance
