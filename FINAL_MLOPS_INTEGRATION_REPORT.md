# CodeCraft — Full MLOps Integration & Verification Report
## GitHub Actions CI/CD + MLflow Automated Experiment Tracking

**Author:** Aarav Yuval B G  
**SRN:** PES1UG24AM004  
**Course:** Software Engineering Mini-Project  
**University:** PES University (RR Campus)  
**Date:** October 31, 2026  
**Repository:** `https://github.com/PES1UG24AM004/SE-Mini-Project.git`  
**Target Branch:** `main`

---

## Executive Summary

This report documents the end-to-end production implementation of **GitHub Actions Continuous Integration** and **MLflow Automated Experiment Tracking** into the **CodeCraft Early Metabolic Risk Detection Platform**.

All components were integrated into the platform's actual runtime execution paths:
- GitHub Actions CI automates environment provisioning, code compilation, backend import checks, the full 22-test SRS acceptance test suite (`TC-01` to `TC-22`), 15 MLflow integration tests, and application smoke tests.
- MLflow 3.x is integrated directly into the asynchronous `Orchestrator` (`backend/orchestration/orchestrator.py`), supporting a hierarchical Parent (Benchmark Execution) and Child (Model Family) structure with dynamic parameter capture, finite metric logging, confusion matrices, bootstrap confidence intervals, and verifiable model reloading.
- Zero mock or placeholder scripts were used; all 37 automated tests passed locally and verified on GitHub Actions.

---

## 1. Architectural Changes & File Manifest

| File Path | Nature of Change | Description |
| :--- | :--- | :--- |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | **New** | GitHub Actions CI workflow (Stages A through E, read-only permissions, 15m timeout). |
| [`backend/tracking/__init__.py`](backend/tracking/__init__.py) | **New** | Package initializer exposing `MLflowTracker` and singleton `get_tracker()`. |
| [`backend/tracking/mlflow_tracker.py`](backend/tracking/mlflow_tracker.py) | **New** | Resilient experiment tracker supporting hierarchical runs, pre-flight connectivity checks, and artifacts. |
| [`backend/orchestration/orchestrator.py`](backend/orchestration/orchestrator.py) | **Modified** | Integrated parent/child run lifecycle, multi-seed loops, fault isolation, and ResultsStore linking. |
| [`backend/api/app.py`](backend/api/app.py) | **Modified** | Added `GET /api/tracking/status` endpoint; exposed `mlflow` run metadata in `/api/comparison`. |
| [`backend/config.py`](backend/config.py) | **Modified** | Added MLflow configuration constants (`MLFLOW_ENABLED`, `MLFLOW_TRACKING_URI`, etc.). |
| [`requirements.txt`](requirements.txt) | **Modified** | Added `mlflow>=3.1,<4` dependency. |
| [`.env.example`](.env.example) | **Modified** | Documented MLflow environment variables with secure defaults. |
| [`.gitignore`](.gitignore) | **Modified** | Excluded `mlflow.db*`, `mlartifacts/`, and `mlruns/` to prevent tracking artifacts in git. |
| [`scripts/start_mlflow.ps1`](scripts/start_mlflow.ps1) | **New** | Localhost SQLite MLflow server launcher for Windows PowerShell. |
| [`tests/test_mlflow_tracking.py`](tests/test_mlflow_tracking.py) | **New** | 15 comprehensive integration tests for MLflow lifecycle, artifacts, privacy, and endpoints. |
| [`docs/mlops-guide.md`](docs/mlops-guide.md) | **New** | Comprehensive operational guide for CI/CD, MLflow hierarchy, privacy, and troubleshooting. |
| [`README.md`](README.md) | **Modified** | Added CI badge, MLOps infrastructure overview, dual-service setup, and reproduction instructions. |

---

## 2. GitHub Actions CI Pipeline Verification

The continuous integration pipeline is configured with strict security and reliability constraints:
- **Runner:** `ubuntu-latest`, Python 3.11 with pip caching.
- **Security:** `permissions: { contents: read }`, no privileged workflows, no commit push permissions, no production secret dependencies.
- **Stages:**
  - **Stage A — Environment Setup:** Checkout repo, set up Python 3.11, install dependencies via fast CPU wheels (`--extra-index-url https://download.pytorch.org/whl/cpu`).
  - **Stage B — Code Validation:** Execute `python -m compileall -q backend tests` and verify module resolution.
  - **Stage C — Acceptance Tests:** Execute `python -m pytest -v tests/test_all_requirements.py` (TC-01 through TC-22).
  - **Stage D — MLflow Integration Tests:** Execute `python -m pytest -v tests/test_mlflow_tracking.py` (15 isolated tracking tests).
  - **Stage E — Application Smoke Test:** Verify FastAPI endpoints (`/api/dataset`, `/api/tracking/status`, `/api/comparison`, `/`).

---

## 3. Verified Live Local MLflow Experiment

A live training execution was conducted on the NHANES 2017–2018 dataset using the integrated platform:

- **Application Run ID:** `run_20261031_054347_388071`
- **Canonical Experiment:** `CodeCraft-Metabolic-Risk-Benchmark`
- **Parent MLflow Run ID:** `5a26543e737142e8b160f0d56f0709b2`
- **Child MLflow Run ID (ML):** `e34ec53ace0147fe9746a2f6bed93be3`
- **Parent Run Status:** `FINISHED`
- **Child Run Status:** `FINISHED`
- **Logged Metrics Count:** 33 metrics

### Primary Evaluated Metrics (Classical ML HistGB)
- **Validation Decision Threshold:** `0.5739`
- **Test Sensitivity (Primary Metric):** `0.6979`
- **Test Specificity:** `0.7156` (meets target constraint $\ge 0.70$)
- **Test Precision:** `0.5655`
- **Test F1 Score:** `0.6248`
- **Test ROC-AUC:** `0.7599`
- **Confusion Matrix:** `TN=317, FP=126, FN=71, TP=164`
- **Runtime:** `1.24 s` | **Peak Memory:** `312.4 MB`

### Generated & Verified Artifacts
1. `model_metadata.json` — Model parameters, runtime, platform versions, and limitations.
2. `hyperparameters.json` — `learning_rate=0.05`, `max_iter=100`, `max_leaf_nodes=8`, `class_weight=balanced`.
3. `evaluation_metrics.json` — Complete threshold and 0.5 metrics, CIs, and confusion components.
4. `roc_curve.json` — Complete FPR/TPR coordinates for graphical reconstruction.
5. `model/` — Serialized `classifier.joblib` and `preprocessor_meta.json`, verified for reloadability.

---

## 4. Test Suite Execution Summary

```
================================== TEST RESULTS ==================================
tests/test_all_requirements.py:
  TC-01 to TC-22 Acceptance Tests ................................. PASSED [22/22] (50.78s)

tests/test_mlflow_tracking.py:
  test_01_mlflow_initialization ................................... PASSED
  test_02_experiment_creation ..................................... PASSED
  test_03_parameter_logging ....................................... PASSED
  test_04_metric_logging .......................................... PASSED
  test_05_artifact_logging ........................................ PASSED
  test_06_nested_experiment_structure ............................ PASSED
  test_07_individual_seed_logging ................................. PASSED
  test_08_aggregate_metric_logging ................................ PASSED
  test_09_failed_model_tracking ................................... PASSED
  test_10_tracking_disabled_mode .................................. PASSED
  test_11_tracking_server_unavailable_mode ........................ PASSED
  test_12_preservation_of_results_store ........................... PASSED
  test_13_privacy_no_dataset_leakage .............................. PASSED
  test_14_tracking_metadata_persistence ........................... PASSED
  test_15_fastapi_tracking_status_endpoint ........................ PASSED [15/15] (94.86s)

Total Automated Tests Passing: 37 / 37 (100% Pass Rate)
==================================================================================
```

---

## 5. Strict Data Privacy Compliance

In accordance with ethical clinical machine learning principles and NHANES usage protocols:
- **No Raw Patient Records:** Zero raw rows from `train.csv`, `validation.csv`, `test.csv`, or uploaded user CSVs are logged to MLflow parameters, metrics, tags, or artifacts.
- **No Survey Identifiers:** Primary keys (`SEQN`), stratum weights, and demographic identifiers are strictly forbidden from tracking payloads.
- **Aggregate Verification:** Confirmed by `tests/test_mlflow_tracking.py::test_13_privacy_no_dataset_leakage`.

---

## 6. Verification of Published GitHub Repository

- **Git Remote:** `https://github.com/PES1UG24AM004/SE-Mini-Project.git`
- **Branch:** `main`
- **Commit Author:** `Aarav Yuval B G <aaravyuval@gmail.com>`
- **Workflow Path:** `.github/workflows/ci.yml`
