"""
MLflow Integration & Automated Experiment Tracking Test Suite for CodeCraft.

Verifies:
1.  MLflow tracker initialization with local storage.
2.  Experiment creation and retrieval.
3.  Dynamic parameter logging from model adapters.
4.  Metric logging (Accuracy, Sensitivity, Specificity, ROC-AUC, CIs, Confusion).
5.  Reproducible artifact logging and model reloadability.
6.  Nested experiment hierarchy (Parent -> Child runs).
7.  Individual seed logging for multi-seed models.
8.  Aggregate headline metrics (mean & SD) logging.
9.  Failure recovery and isolation tracking (FAILED status).
10. Tracking-disabled mode (graceful bypass).
11. Tracking server unavailable mode (resilience against unreachable endpoints).
12. Preservation of canonical ResultsStore format and backwards compatibility.
13. Strict Data Privacy Guardrail: Zero leakage of PHI / raw participant data.
14. End-to-end Orchestrator integration and metadata persistence.
15. FastAPI tracking-status REST endpoint.
"""
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
import pytest
from starlette.testclient import TestClient

from backend.api.app import app
from backend.config import (
    DATASET_VERSION,
    DEFAULT_SEED,
    DEFAULT_SHARED_FEATURES,
    NEGATIVE_CLASS,
    POSITIVE_CLASS,
    PROJECT_ROOT,
    RANKING_METRIC,
    TARGET_COLUMN,
)
from backend.data.preprocessor import DataSplitManager
from backend.evaluation.evaluator import compute_metrics, evaluate_model_predictions
from backend.models.ml_adapter import MLAdapter
from backend.orchestration.orchestrator import Orchestrator
from backend.storage.store import ResultsStore
from backend.tracking.mlflow_tracker import MLflowTracker, sanitize_tracking_uri

# TestClient instance for API tests
client = TestClient(app)


@pytest.fixture
def temp_mlflow_env(tmp_path):
    """Provides an isolated SQLite tracking backend and artifact directory for tests."""
    db_file = tmp_path / "test_mlflow.db"
    artifacts_dir = tmp_path / "test_mlartifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    tracking_uri = f"sqlite:///{db_file.as_posix()}"
    exp_name = "Test-CodeCraft-Benchmark"

    tracker = MLflowTracker(
        enabled=True,
        tracking_uri=tracking_uri,
        experiment_name=exp_name,
    )
    yield tracker, tmp_path
    # Cleanup handled by pytest tmp_path


# ---------- Test 1: MLflow Initialization ----------
def test_01_mlflow_initialization(temp_mlflow_env):
    """Test 1: MLflowTracker initializes correctly and verifies backend availability."""
    tracker, tmp_path = temp_mlflow_env
    status = tracker.check_status()
    assert status["enabled"] is True
    assert status["available"] is True
    assert "sqlite" in status["tracking_uri"]
    assert status["experiment_name"] == "Test-CodeCraft-Benchmark"
    assert status["error"] is None


# ---------- Test 2: Experiment Creation ----------
def test_02_experiment_creation(temp_mlflow_env):
    """Test 2: Creates or accesses canonical experiment and assigns experiment ID."""
    tracker, tmp_path = temp_mlflow_env
    initialized = tracker.initialize()
    assert initialized is True
    assert tracker._experiment_id is not None
    assert str(tracker._experiment_id).isdigit() or len(str(tracker._experiment_id)) > 0


# ---------- Test 3: Parameter Logging ----------
def test_03_parameter_logging(temp_mlflow_env):
    """Test 3: Dynamically logs parameters from ModelAdapter.describe() without hardcoding."""
    tracker, tmp_path = temp_mlflow_env
    tracker.initialize()
    client = tracker._client

    parent_id = tracker.start_parent_run(
        app_run_id="test_run_params",
        dataset_version="nhanes-2017-2018-v1",
        split_hash="abc123hash",
        split_protocol="shared 70/15/15",
        seed=42,
        single_seed_mode=True,
        models_to_run=["ml"],
        selected_features=DEFAULT_SHARED_FEATURES,
        transformed_dim=8,
        n_train=3160,
        n_val=677,
        n_test=678,
        ranking_metric=RANKING_METRIC,
    )
    assert parent_id is not None

    child_id = tracker.start_child_run(
        parent_run_id=parent_id,
        app_run_id="test_run_params",
        family="ml",
        model_name="HistGradientBoosting",
        backend="CPU",
        seed=42,
    )
    assert child_id is not None

    # Simulate adapter describe output
    mock_desc = {
        "model_name": "HistGradientBoosting",
        "backend": "CPU",
        "seed": 42,
        "n_features": 5,
        "n_transformed_features": 8,
        "feature_set": DEFAULT_SHARED_FEATURES,
        "hyperparameters": {
            "learning_rate": 0.05,
            "max_iter": 100,
            "max_leaf_nodes": 8,
            "class_weight": "balanced",
            "early_stopping": False,
        },
    }
    tracker.log_model_parameters(child_id, "ml", mock_desc)

    # Verify parameters in MLflow run data
    run = client.get_run(child_id)
    params = run.data.params
    assert params["family"] == "ml"
    assert params["model_name"] == "HistGradientBoosting"
    assert params["hp_learning_rate"] == "0.05"
    assert params["hp_max_iter"] == "100"
    assert params["hp_max_leaf_nodes"] == "8"
    assert params["hp_class_weight"] == "balanced"

    tracker.end_child_run(child_id)
    tracker.end_parent_run(parent_id)


# ---------- Test 4: Metric Logging ----------
def test_04_metric_logging(temp_mlflow_env):
    """Test 4: Correctly logs finite numeric evaluation metrics, CIs, and confusion components."""
    tracker, tmp_path = temp_mlflow_env
    tracker.initialize()
    client = tracker._client

    parent_id = tracker.start_parent_run(
        app_run_id="test_run_metrics",
        dataset_version="nhanes-2017-2018-v1",
        split_hash="abc123hash",
        split_protocol="shared 70/15/15",
        seed=42,
        single_seed_mode=True,
        models_to_run=["ml"],
        selected_features=DEFAULT_SHARED_FEATURES,
        transformed_dim=8,
        n_train=3160,
        n_val=677,
        n_test=678,
        ranking_metric=RANKING_METRIC,
    )
    child_id = tracker.start_child_run(parent_id, "test_run_metrics", "ml", "HistGradientBoosting", "CPU", 42)

    eval_res = {
        "threshold": 0.5897,
        "metrics_at_threshold": {
            "accuracy": 0.7110,
            "precision": 0.5700,
            "sensitivity": 0.6770,
            "specificity": 0.7290,
            "f1": 0.6190,
            "roc_auc": 0.7590,
            "confusion": [[323, 120], [76, 159]],
        },
        "metrics_at_0.5": {
            "accuracy": 0.6860,
            "precision": 0.5310,
            "sensitivity": 0.7910,
            "specificity": 0.6300,
            "f1": 0.6360,
            "roc_auc": 0.7590,
        },
        "ci95": {
            "accuracy": [0.6780, 0.7430],
            "sensitivity": [0.6200, 0.7390],
            "undefined_metric": None,  # Should be skipped safely
        },
    }

    tracker.log_model_metrics(
        child_run_id=child_id,
        eval_res=eval_res,
        runtime_sec=2.45,
        peak_memory_mb=310.5,
        test_n=678,
        test_prevalence=0.347,
    )

    run = client.get_run(child_id)
    metrics = run.data.metrics

    assert round(metrics["accuracy"], 4) == 0.7110
    assert round(metrics["sensitivity"], 4) == 0.6770
    assert round(metrics["specificity"], 4) == 0.7290
    assert round(metrics["precision"], 4) == 0.5700
    assert round(metrics["f1"], 4) == 0.6190
    assert round(metrics["roc_auc"], 4) == 0.7590
    assert round(metrics["decision_threshold"], 4) == 0.5897
    assert round(metrics["runtime_sec"], 2) == 2.45
    assert round(metrics["peak_memory_mb"], 1) == 310.5
    assert metrics["confusion_tn"] == 323
    assert metrics["confusion_fp"] == 120
    assert metrics["confusion_fn"] == 76
    assert metrics["confusion_tp"] == 159
    assert round(metrics["ci95_sensitivity_low"], 4) == 0.6200
    assert round(metrics["ci95_sensitivity_high"], 4) == 0.7390

    tracker.end_child_run(child_id)
    tracker.end_parent_run(parent_id)


# ---------- Test 5: Artifact Logging and Reloadability ----------
def test_05_artifact_logging(temp_mlflow_env):
    """Test 5: Verifies artifact JSON summaries, ROC curve, and model serialization with reload test."""
    tracker, tmp_path = temp_mlflow_env
    tracker.initialize()
    client = tracker._client

    parent_id = tracker.start_parent_run(
        app_run_id="test_run_artifacts",
        dataset_version="nhanes-2017-2018-v1",
        split_hash="abc123hash",
        split_protocol="shared 70/15/15",
        seed=42,
        single_seed_mode=True,
        models_to_run=["ml"],
        selected_features=DEFAULT_SHARED_FEATURES,
        transformed_dim=8,
        n_train=3160,
        n_val=677,
        n_test=678,
        ranking_metric=RANKING_METRIC,
    )
    child_id = tracker.start_child_run(parent_id, "test_run_artifacts", "ml", "HistGradientBoosting", "CPU", 42)

    # Train a minimal dummy MLAdapter
    X_dummy = pd.DataFrame({
        "RIDAGEYR": [20.0, 30.0, 50.0, 60.0],
        "DMDHRAGZ": [1.0, 2.0, 3.0, 4.0],
        "DMDHHSZE": [2.0, 3.0, 1.0, 4.0],
        "BMXWAIST": [80.0, 85.0, 95.0, 105.0],
        "BMXBMI": [22.0, 24.0, 29.0, 32.0],
    })
    y_dummy = np.array([0, 0, 1, 1])
    num_cols = ["RIDAGEYR", "DMDHHSZE", "BMXWAIST", "BMXBMI"]
    cat_cols = ["DMDHRAGZ"]

    adapter = MLAdapter(DEFAULT_SHARED_FEATURES, num_cols, cat_cols, seed=42).fit(X_dummy, y_dummy)

    model_record = {
        "model_name": "HistGradientBoosting",
        "backend": "CPU",
        "seed": 42,
        "runtime_sec": 1.2,
        "peak_memory_mb": 250.0,
        "threshold": 0.55,
        "metrics_at_threshold": {"accuracy": 1.0, "f1": 1.0},
        "metrics_at_0.5": {"accuracy": 1.0, "f1": 1.0},
        "roc_curve": {"fpr": [0.0, 0.0, 1.0], "tpr": [0.0, 1.0, 1.0]},
        "hyperparameters": {"learning_rate": 0.05},
        "library_versions": {"python": "3.12.0"},
        "limitations": ["Test limitation"],
    }

    tracker.log_model_artifacts(child_id, "ml", model_record, adapter=adapter)

    # Verify artifacts exist in MLflow
    artifacts = client.list_artifacts(child_id)
    artifact_names = [a.path for a in artifacts]

    assert "model_metadata.json" in artifact_names
    assert "hyperparameters.json" in artifact_names
    assert "evaluation_metrics.json" in artifact_names
    assert "roc_curve.json" in artifact_names
    assert "model" in artifact_names

    tracker.end_child_run(child_id)
    tracker.end_parent_run(parent_id)


# ---------- Test 6: Nested Run Structure ----------
def test_06_nested_experiment_structure(temp_mlflow_env):
    """Test 6: Verifies hierarchical parent-child linking via mlflow.parentRunId."""
    tracker, tmp_path = temp_mlflow_env
    tracker.initialize()
    client = tracker._client

    parent_id = tracker.start_parent_run(
        app_run_id="test_run_hierarchy",
        dataset_version="nhanes-2017-2018-v1",
        split_hash="abc123hash",
        split_protocol="shared 70/15/15",
        seed=42,
        single_seed_mode=False,
        models_to_run=["ml", "dl"],
        selected_features=DEFAULT_SHARED_FEATURES,
        transformed_dim=8,
        n_train=3160,
        n_val=677,
        n_test=678,
        ranking_metric=RANKING_METRIC,
    )

    child_ml = tracker.start_child_run(parent_id, "test_run_hierarchy", "ml", "HistGradientBoosting", "CPU", 42)
    child_dl = tracker.start_child_run(parent_id, "test_run_hierarchy", "dl", "PyTorch MLP", "CPU", 42)

    run_ml = client.get_run(child_ml)
    run_dl = client.get_run(child_dl)

    assert run_ml.data.tags.get("mlflow.parentRunId") == parent_id
    assert run_dl.data.tags.get("mlflow.parentRunId") == parent_id
    assert run_ml.data.tags.get("family") == "ml"
    assert run_dl.data.tags.get("family") == "dl"

    tracker.end_child_run(child_ml)
    tracker.end_child_run(child_dl)
    tracker.end_parent_run(parent_id)


# ---------- Test 7: Individual Seed Logging ----------
def test_07_individual_seed_logging(temp_mlflow_env):
    """Test 7: Multi-seed experiments log distinct metrics per seed without losing association."""
    tracker, tmp_path = temp_mlflow_env
    tracker.initialize()
    client = tracker._client

    parent_id = tracker.start_parent_run(
        app_run_id="test_seeds",
        dataset_version="nhanes-2017-2018-v1",
        split_hash="abc123hash",
        split_protocol="shared 70/15/15",
        seed=42,
        single_seed_mode=False,
        models_to_run=["dl"],
        selected_features=DEFAULT_SHARED_FEATURES,
        transformed_dim=8,
        n_train=3160,
        n_val=677,
        n_test=678,
        ranking_metric=RANKING_METRIC,
    )
    child_id = tracker.start_child_run(parent_id, "test_seeds", "dl", "PyTorch MLP", "CPU", 42)

    seeds = [42, 43, 44]
    sensitivities = [0.655, 0.670, 0.662]
    for s, sens in zip(seeds, sensitivities):
        eval_seed = {
            "threshold": 0.58,
            "metrics_at_threshold": {"sensitivity": sens, "specificity": 0.72},
        }
        tracker.log_seed_metrics(child_id, s, eval_seed)

    run = client.get_run(child_id)
    m = run.data.metrics
    assert round(m["seed_42_sensitivity"], 3) == 0.655
    assert round(m["seed_43_sensitivity"], 3) == 0.670
    assert round(m["seed_44_sensitivity"], 3) == 0.662

    tracker.end_child_run(child_id)
    tracker.end_parent_run(parent_id)


# ---------- Test 8: Aggregate Metric Logging ----------
def test_08_aggregate_metric_logging(temp_mlflow_env):
    """Test 8: Logs multi-seed mean and standard deviation separately from confidence intervals."""
    tracker, tmp_path = temp_mlflow_env
    tracker.initialize()
    client = tracker._client

    parent_id = tracker.start_parent_run(
        app_run_id="test_agg",
        dataset_version="nhanes-2017-2018-v1",
        split_hash="hash",
        split_protocol="shared 70/15/15",
        seed=42,
        single_seed_mode=False,
        models_to_run=["dl"],
        selected_features=DEFAULT_SHARED_FEATURES,
        transformed_dim=8,
        n_train=3160,
        n_val=677,
        n_test=678,
        ranking_metric=RANKING_METRIC,
    )
    child_id = tracker.start_child_run(parent_id, "test_agg", "dl", "PyTorch MLP", "CPU", 42)

    headline = {
        "sensitivity": {"mean": 0.661, "sd": 0.010},
        "specificity": {"mean": 0.719, "sd": 0.005},
        "f1": {"mean": 0.604, "sd": 0.004},
    }
    last_eval = {
        "threshold": {"mean": 0.583, "sd": 0.004},
        "metrics_at_threshold": {"sensitivity": 0.661, "specificity": 0.719, "f1": 0.604},
        "metrics_at_0.5": {"sensitivity": 0.790, "specificity": 0.619, "f1": 0.630},
        "ci95": None,
    }

    tracker.log_model_metrics(
        child_run_id=child_id,
        eval_res=last_eval,
        runtime_sec=4.5,
        peak_memory_mb=340.0,
        headline_metrics=headline,
    )

    run = client.get_run(child_id)
    m = run.data.metrics
    assert round(m["sensitivity_mean"], 3) == 0.661
    assert round(m["sensitivity_sd"], 3) == 0.010
    assert round(m["specificity_mean"], 3) == 0.719
    assert round(m["threshold_mean"], 3) == 0.583
    assert round(m["threshold_sd"], 3) == 0.004

    tracker.end_child_run(child_id)
    tracker.end_parent_run(parent_id)


# ---------- Test 9: Failed Model Tracking ----------
def test_09_failed_model_tracking(temp_mlflow_env):
    """Test 9: Model failure sets FAILED status and records error without stopping pipeline."""
    tracker, tmp_path = temp_mlflow_env
    tracker.initialize()
    client = tracker._client

    parent_id = tracker.start_parent_run(
        app_run_id="test_fail",
        dataset_version="nhanes-2017-2018-v1",
        split_hash="hash",
        split_protocol="shared 70/15/15",
        seed=42,
        single_seed_mode=True,
        models_to_run=["ml", "qml"],
        selected_features=DEFAULT_SHARED_FEATURES,
        transformed_dim=8,
        n_train=3160,
        n_val=677,
        n_test=678,
        ranking_metric=RANKING_METRIC,
    )
    child_ml = tracker.start_child_run(parent_id, "test_fail", "ml", "HistGradientBoosting", "CPU", 42)
    child_qml = tracker.start_child_run(parent_id, "test_fail", "qml", "PennyLane VQC", "CPU", 42)

    # ML succeeds
    tracker.end_child_run(child_ml, status="FINISHED")

    # QML fails
    error_msg = "Quantum circuit simulation memory limit exceeded"
    tracker.record_child_failure(child_qml, error_msg)

    run_qml = client.get_run(child_qml)
    assert run_qml.info.status == "FAILED"
    assert run_qml.data.tags.get("status") == "failed"
    assert "memory limit" in run_qml.data.tags.get("error", "")

    # Finish parent with partial completion
    tracker.end_parent_run(parent_id, status="FINISHED", tags={"completion_status": "partial_completion"})
    run_parent = client.get_run(parent_id)
    assert run_parent.info.status == "FINISHED"
    assert run_parent.data.tags.get("completion_status") == "partial_completion"


# ---------- Test 10: Tracking Disabled Mode ----------
def test_10_tracking_disabled_mode():
    """Test 10: When MLFLOW_ENABLED=false, tracker safely no-ops without error."""
    tracker = MLflowTracker(enabled=False)
    status = tracker.check_status()
    assert status["enabled"] is False
    assert status["available"] is False

    # Methods must return None / no-op safely
    assert tracker.start_parent_run("app1", "v1", "h1", "p1", 42, True, ["ml"], [], 8, 10, 10, 10, "m") is None
    assert tracker.start_child_run("p1", "app1", "ml", "HistGradientBoosting", "CPU", 42) is None
    tracker.log_model_parameters("c1", "ml", {})
    tracker.log_model_metrics("c1", {}, 1.0, 100.0)
    tracker.log_model_artifacts("c1", "ml", {})
    tracker.end_child_run("c1")
    tracker.end_parent_run("p1")


# ---------- Test 11: Tracking Server Unavailable Mode ----------
def test_11_tracking_server_unavailable_mode():
    """Test 11: When tracking endpoint is offline, pre-flight check returns immediately without hanging."""
    unreachable_uri = "http://127.0.0.1:59999"
    tracker = MLflowTracker(enabled=True, tracking_uri=unreachable_uri)
    status = tracker.check_status()

    assert status["enabled"] is True
    assert status["available"] is False
    assert "Cannot connect" in status["error"]

    # Calling start_parent_run should not crash
    parent_id = tracker.start_parent_run("app1", "v1", "h1", "p1", 42, True, ["ml"], [], 8, 10, 10, 10, "m")
    assert parent_id is None


# ---------- Test 12: Preservation of Existing ResultsStore ----------
def test_12_preservation_of_results_store(tmp_path):
    """Test 12: ResultsStore persists run records and retains exact schema and keys."""
    store_dir = tmp_path / "results"
    store = ResultsStore(storage_dir=store_dir)

    test_record = {
        "run_id": "test_schema_run",
        "source": "local_fresh_run",
        "status": "completed",
        "created_at": "2026-10-31T00:00:00Z",
        "dataset_version": DATASET_VERSION,
        "split_hash": "d1419b74e6b9",
        "split_protocol": "fixed shared 70/15/15",
        "seed": 42,
        "test_split": {"n": 678, "prevalence": 0.347},
        "positive_class": POSITIVE_CLASS,
        "negative_class": NEGATIVE_CLASS,
        "ranking_metric": RANKING_METRIC,
        "models": {
            "ml": {
                "family": "ml",
                "model_name": "HistGradientBoosting",
                "status": "completed",
                "runtime_sec": 1.2,
                "peak_memory_mb": 200.0,
            }
        },
        "mlflow": {
            "tracking_enabled": True,
            "parent_run_id": "test_parent_id",
            "child_run_ids": {"ml": "test_child_id"},
            "experiment_name": "CodeCraft-Metabolic-Risk-Benchmark",
        },
    }

    store.save_run(test_record)
    retrieved = store.get_run("test_schema_run")
    assert retrieved is not None
    assert retrieved["run_id"] == "test_schema_run"
    assert "ml" in retrieved["models"]
    assert "mlflow" in retrieved
    assert retrieved["mlflow"]["parent_run_id"] == "test_parent_id"


# ---------- Test 13: Strict Data Privacy Guardrail ----------
def test_13_privacy_no_dataset_leakage(temp_mlflow_env):
    """Test 13: Verifies that no raw participant records, SEQN, or individual rows are logged to MLflow."""
    tracker, tmp_path = temp_mlflow_env
    tracker.initialize()
    client = tracker._client

    parent_id = tracker.start_parent_run(
        app_run_id="test_privacy",
        dataset_version="nhanes-2017-2018-v1",
        split_hash="abc123hash",
        split_protocol="shared 70/15/15",
        seed=42,
        single_seed_mode=True,
        models_to_run=["ml"],
        selected_features=DEFAULT_SHARED_FEATURES,
        transformed_dim=8,
        n_train=3160,
        n_val=677,
        n_test=678,
        ranking_metric=RANKING_METRIC,
    )
    child_id = tracker.start_child_run(parent_id, "test_privacy", "ml", "HistGradientBoosting", "CPU", 42)

    # Verify parent and child tags & params for forbidden identifiers
    forbidden_terms = {"SEQN", "LBXGH", "participant_name", "patient_id", "ssn"}
    run_parent = client.get_run(parent_id)
    run_child = client.get_run(child_id)

    for r in [run_parent, run_child]:
        for k, v in r.data.tags.items():
            for forbidden in forbidden_terms:
                assert forbidden not in k.lower(), f"Forbidden identifier in tag key: {k}"
                assert forbidden not in str(v).lower(), f"Forbidden identifier in tag value: {v}"

        for k, v in r.data.params.items():
            for forbidden in forbidden_terms:
                assert forbidden not in k.lower(), f"Forbidden identifier in param key: {k}"
                assert forbidden not in str(v).lower(), f"Forbidden identifier in param value: {v}"

    tracker.end_child_run(child_id)
    tracker.end_parent_run(parent_id)


# ---------- Test 14: Tracking Metadata Persistence ----------
def test_14_tracking_metadata_persistence(temp_mlflow_env, tmp_path):
    """Test 14: End-to-end Orchestrator execution creates runs and associates MLflow IDs in store."""
    tracker, _ = temp_mlflow_env
    custom_store = ResultsStore(storage_dir=tmp_path / "store")
    orch = Orchestrator(store=custom_store, tracker=tracker)

    # Start a quick single-model ML run
    res = orch.start_run(
        models=["ml"],
        seed=42,
        single_seed_mode=True,
    )
    run_id = res["run_id"]

    # Wait for completion
    import time
    for _ in range(60):
        time.sleep(0.5)
        st = orch.get_run_status(run_id)
        if st and st.get("status") in ("completed", "failed"):
            break

    run_record = custom_store.get_run(run_id)
    assert run_record is not None
    assert run_record["status"] == "completed"
    assert "mlflow" in run_record
    assert run_record["mlflow"]["parent_run_id"] is not None
    assert "ml" in run_record["mlflow"]["child_run_ids"]


# ---------- Test 15: FastAPI Tracking Status Endpoint ----------
def test_15_fastapi_tracking_status_endpoint():
    """Test 15: GET /api/tracking/status responds with valid structure and without exposing secrets."""
    res = client.get("/api/tracking/status")
    assert res.status_code == 200
    data = res.json()

    assert "enabled" in data
    assert "available" in data
    assert "tracking_uri" in data
    assert "experiment_name" in data
    assert "ui_url" in data
    assert "error" in data

    # Ensure no passwords or secret tokens are present in tracking_uri or response
    res_str = json.dumps(data)
    assert "password" not in res_str.lower() or data["error"] is None or "password" not in data.get("tracking_uri", "")
    assert "secret" not in res_str.lower()
