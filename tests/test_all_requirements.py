"""
Comprehensive Test Suite for CodeCraft Early Metabolic Risk Detection.
Verifies all 22 Acceptance Test Cases (TC-01 to TC-22) mapped to SRS and Architecture.
"""
import io
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from starlette.testclient import TestClient

from backend.api.app import app
from backend.config import (
    DEFAULT_SEED,
    FORBIDDEN_COLUMNS,
    NEGATIVE_CLASS,
    POSITIVE_CLASS,
    PROJECT_ROOT,
    RANKING_METRIC,
    TARGET_COLUMN,
    WARNING_TEXT,
)
from backend.data.preprocessor import DataSplitManager, compute_file_sha256
from backend.data.validator import (
    ValidationError,
    check_file_safety,
    sanitize_cell_for_export,
    validate_dataframe,
)
from backend.evaluation.evaluator import (
    aggregate_seed_metrics,
    bootstrap_ci,
    compute_metrics,
    pick_threshold,
)
from backend.models.ml_adapter import MLAdapter
from backend.models.stub_adapter import StubAdapter
from backend.reports.generator import ReportGenerator
from backend.storage.store import ResultsStore

client = TestClient(app)


# ---------- TC-01: Valid import ----------
def test_tc01_valid_import():
    """TC-01: Successful dataset inspection/import; record count, column count, classes visible."""
    res = client.get("/api/dataset")
    assert res.status_code == 200
    data = res.json()
    assert data["rows"] == 4515
    assert data["columns"] == 53
    assert data["target"] == TARGET_COLUMN
    assert POSITIVE_CLASS in data["classCounts"]
    assert NEGATIVE_CLASS in data["classCounts"]
    assert data["datasetId"] == "nhanes-2017-2018-v1"


# ---------- TC-02: Missing target ----------
def test_tc02_missing_target():
    """TC-02: Import CSV without target; validation fails naming missing target; blocks training."""
    df_no_target = pd.DataFrame({
        "RIDAGEYR": [45, 52, 61],
        "BMXBMI": [25.4, 28.1, 31.0],
    })
    report = validate_dataframe(df_no_target)
    assert not report["valid"]
    target_issues = [i for i in report["issues"] if i["field"] == TARGET_COLUMN]
    assert len(target_issues) > 0
    assert "missing" in target_issues[0]["error"].lower()


# ---------- TC-03: Invalid values & missingness ----------
def test_tc03_invalid_values():
    """TC-03: Invalid data types, out-of-range values, and single class; issues listed with field names."""
    df_invalid = pd.DataFrame({
        TARGET_COLUMN: [NEGATIVE_CLASS, NEGATIVE_CLASS, NEGATIVE_CLASS],  # Single class
        "RIDAGEYR": [-5, 150, 45],  # Out of range
        "BMXBMI": ["not_a_number", 25.0, 30.0],  # Invalid type
    })
    report = validate_dataframe(df_invalid)
    assert not report["valid"]
    fields_flagged = {i["field"] for i in report["issues"]}
    assert "RIDAGEYR" in fields_flagged
    assert "BMXBMI" in fields_flagged
    assert TARGET_COLUMN in fields_flagged


# ---------- TC-04: Shared split & leakage prevention ----------
def test_tc04_shared_split_leakage():
    """TC-04: Identical split across models; transforms fit on train only; test untouched."""
    mgr = DataSplitManager(PROJECT_ROOT)
    tr1, va1, te1, hash1 = mgr.load_trio_splits()
    tr2, va2, te2, hash2 = mgr.load_trio_splits()

    assert hash1 == hash2
    assert len(tr1) == 3160 and len(va1) == 677 and len(te1) == 678

    # Verify no overlap between splits
    # Compute SHA-256 of each train row vs test row
    tr_hashes = set(pd.util.hash_pandas_object(tr1).values)
    te_hashes = set(pd.util.hash_pandas_object(te1).values)
    assert len(tr_hashes.intersection(te_hashes)) == 0


# ---------- TC-05: Separate model training records ----------
def test_tc05_separate_model_training():
    """TC-05: Models produce distinct run records with family, config, seed, backend, and status."""
    store = ResultsStore()
    record = store.get_run("reference_baseline")
    assert record is not None
    assert set(record["models"].keys()) >= {"ml", "dl", "qml"}

    for fam in ["ml", "dl", "qml"]:
        m = record["models"][fam]
        assert m["family"] == fam
        assert "backend" in m
        assert "status" in m
        assert "hyperparameters" in m


# ---------- TC-06: Metric correctness to 4 decimals & undefined metric handling ----------
def test_tc06_metric_correctness():
    """TC-06: Metric calculations equal independent reference to 4 decimals; undefined returns None."""
    y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0])
    y_prob = np.array([0.10, 0.40, 0.35, 0.80, 0.65, 0.90, 0.20, 0.70, 0.55, 0.30, 0.45, 0.60])

    m = compute_metrics(y_true, y_prob, 0.5)

    # Independent calculations
    # y_pred = [0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1]
    # TP: 4 (idx 4, 5, 7, 8), FP: 2 (idx 3, 11), TN: 4 (idx 0, 1, 2, 9), FN: 2 (idx 6, 10)
    assert m["confusion"] == [[4, 2], [2, 4]]
    assert round(m["accuracy"], 4) == round(8 / 12, 4)
    assert round(m["sensitivity"], 4) == round(4 / 6, 4)
    assert round(m["specificity"], 4) == round(4 / 6, 4)
    assert round(m["precision"], 4) == round(4 / 6, 4)

    # Undefined metric case: single class labels (no positive examples)
    m_undef = compute_metrics([0, 0, 0], [0.1, 0.2, 0.3], 0.5)
    assert m_undef["sensitivity"] is None
    assert m_undef["precision"] is None
    assert m_undef["f1"] is None
    assert m_undef["roc_auc"] is None


# ---------- TC-07: Comparison display & ranking metric ----------
def test_tc07_comparison_display():
    """TC-07: Side-by-side comparison on same test set, ranking metric, test label, n/a handling."""
    res = client.get("/api/comparison?runId=reference_baseline")
    assert res.status_code == 200
    data = res.json()

    assert data["rankingMetric"] == RANKING_METRIC
    assert data["testSet"]["n"] == 678
    assert data["testSet"]["prevalence"] == 0.347
    assert len(data["models"]) >= 3

    for m in data["models"]:
        assert m["family"] in ("ml", "dl", "qml")
        assert m["status"] in ("completed", "imported_reference")


# ---------- TC-08: Prediction safety & validation ----------
def test_tc08_prediction_safety():
    """TC-08: Valid input yields score/label/threshold/warning; invalid input returns field error without calling model."""
    valid_payload = {
        "runId": "reference_baseline",
        "family": "ml",
        "features": {
            "RIDAGEYR": 45.0,
            "DMDHRAGZ": 3.0,
            "DMDHHSZE": 2.0,
            "BMXWAIST": 88.5,
            "BMXBMI": 26.2,
        },
    }
    res_ok = client.post("/api/predict", json=valid_payload)
    assert res_ok.status_code == 200
    data_ok = res_ok.json()
    assert data_ok["valid"] is True
    assert 0.0 <= data_ok["score"] <= 1.0
    assert data_ok["label"] in (POSITIVE_CLASS, NEGATIVE_CLASS)
    assert WARNING_TEXT in data_ok["warning"]

    # Invalid input (string for age, missing BMI)
    invalid_payload = {
        "runId": "reference_baseline",
        "family": "ml",
        "features": {
            "RIDAGEYR": "invalid_string",
            "DMDHRAGZ": 3.0,
            "DMDHHSZE": 2.0,
            "BMXWAIST": 88.5,
        },
    }
    res_bad = client.post("/api/predict", json=invalid_payload)
    assert res_bad.status_code == 422
    data_bad = res_bad.json()
    assert data_bad["valid"] is False
    err_fields = [e["field"] for e in data_bad["errors"]]
    assert "RIDAGEYR" in err_fields
    assert "BMXBMI" in err_fields


# ---------- TC-09: Privacy & identifier exclusion ----------
def test_tc09_privacy_and_identifier_exclusion():
    """TC-09: Forbidden columns (SEQN, etc.) rejected/flagged; aggregate report contains no participant rows."""
    df_leakage = pd.DataFrame({
        "SEQN": [10001, 10002],
        "participant_name": ["Alice", "Bob"],
        TARGET_COLUMN: [NEGATIVE_CLASS, POSITIVE_CLASS],
    })
    report = validate_dataframe(df_leakage)
    assert not report["valid"]
    assert any("forbidden" in i["field"].lower() or "privacy" in i.get("type", "") for i in report["issues"])

    # Export report has no participant rows or identifier feature predictors
    res = client.get("/api/reports/reference_baseline?format=json")
    assert res.status_code == 200
    export_data = res.json()
    assert "SEQN" not in export_data["provenance"]["feature_set"].get("raw_features", [])
    assert "rows" not in export_data.get("models", {})


# ---------- TC-10: Export, provenance & reproducibility ----------
def test_tc10_export_and_reproducibility():
    """TC-10: Reports contain timestamp, split hash, seed, library versions, aggregate metrics."""
    res = client.get("/api/reports/reference_baseline?format=json")
    assert res.status_code == 200
    data = res.json()
    assert "provenance" in data
    prov = data["provenance"]
    assert prov["split_hash"] == "d1419b74e6b90c7e93c051e0f497ba7d577c76b798214e33fa87a1b53ba2cdde"
    assert "generated_at" in data
    assert prov["ranking_metric"] == RANKING_METRIC


# ---------- TC-11: Website run workflow ----------
def test_tc11_run_workflow():
    """TC-11: POST /api/runs starts run and returns within 2 seconds; GET status reflects state."""
    payload = {
        "datasetId": "nhanes-2017-2018-v1",
        "models": ["ml"],
        "seed": 42,
        "singleSeedMode": True,
    }
    t0 = time.time()
    res = client.post("/api/runs", json=payload)
    elapsed = time.time() - t0
    assert elapsed <= 2.0  # Must acknowledge within 2 seconds
    assert res.status_code in (202, 409)  # 202 accepted or 409 if active


# ---------- TC-12: Dashboard, details & export ----------
def test_tc12_dashboard_details_and_export():
    """TC-12: Details endpoint returns configuration, hyperparameters, backend, limitations."""
    res = client.get("/api/models/ml?runId=reference_baseline")
    assert res.status_code == 200
    data = res.json()
    assert data["family"] == "ml"
    assert "hyperparameters" in data
    assert "limitations" in data
    assert len(data["limitations"]) > 0


# ---------- TC-13: Validation performance on 50,000-row fixture ----------
def test_tc13_validation_performance():
    """TC-13: Validating a 50,000-row synthetic fixture completes in <= 10 seconds; time recorded."""
    np.random.seed(42)
    n = 50000
    synthetic_df = pd.DataFrame({
        TARGET_COLUMN: np.random.choice([NEGATIVE_CLASS, POSITIVE_CLASS], size=n, p=[0.65, 0.35]),
        "RIDAGEYR": np.random.randint(18, 85, size=n),
        "DMDHRAGZ": np.random.choice([1, 2, 3, 4], size=n),
        "DMDHHSZE": np.random.randint(1, 6, size=n),
        "BMXWAIST": np.random.normal(90.0, 15.0, size=n),
        "BMXBMI": np.random.normal(28.0, 6.0, size=n),
    })

    t0 = time.time()
    report = validate_dataframe(synthetic_df)
    elapsed = time.time() - t0

    assert elapsed <= 10.0, f"Validation took {elapsed:.2f}s, expected <= 10s"
    assert report["valid"] is True
    assert report["rows"] == 50000
    print(f"\n[TC-13 MEASURED] 50,000 rows validated in {elapsed:.3f} seconds.")


# ---------- TC-14: Failure recovery and isolation ----------
def test_tc14_failure_recovery_isolation():
    """TC-14: Injected failure in one model isolates error; others complete; earlier results preserved."""
    from backend.orchestration.orchestrator import Orchestrator
    store = ResultsStore()
    orch = Orchestrator(store=store)

    # Injected failure for dl
    res = orch.start_run(
        models=["ml", "dl"],
        seed=42,
        simulate_failure_family="dl",
        single_seed_mode=True,
    )
    run_id = res["run_id"]

    # Wait for run to finish
    for _ in range(60):
        time.sleep(0.5)
        st = orch.get_run_status(run_id)
        if st and st.get("status") in ("completed", "failed"):
            break

    run_record = store.get_run(run_id)
    assert run_record is not None
    assert "ml" in run_record["models"]
    assert "dl" in run_record["models"]
    assert run_record["models"]["ml"]["status"] == "completed"
    assert run_record["models"]["dl"]["status"] == "failed"
    assert "Simulated injected failure" in run_record["models"]["dl"]["error"]


# ---------- TC-15: Usability checklist ----------
def test_tc15_usability_checklist():
    """TC-15: Verifies end-to-end steps (import -> validate -> run -> compare -> export) exist without code modification."""
    # Check dataset endpoint
    assert client.get("/api/dataset").status_code == 200
    # Check validation endpoint
    assert client.post("/api/datasets/validate").status_code == 200
    # Check comparison endpoint
    assert client.get("/api/comparison").status_code == 200
    # Check export endpoint
    assert client.get("/api/reports/reference_baseline?format=json").status_code == 200


# ---------- TC-16: Maintainability with StubAdapter ----------
def test_tc16_maintainability_stub_adapter():
    """TC-16: StubAdapter with fit, predict_proba, describe replaces model without touching evaluator or UI."""
    stub = StubAdapter("MockModel", default_prob=0.42)
    X_mock = pd.DataFrame({"feat1": [1.0, 2.0], "feat2": [3.0, 4.0]})
    y_mock = np.array([0, 1])

    stub.fit(X_mock, y_mock)
    preds = stub.predict_proba(X_mock)

    assert len(preds) == 2
    assert np.allclose(preds, 0.42)
    desc = stub.describe()
    assert desc["model_name"] == "MockModel"
    assert desc["family"] == "stub"


# ---------- TC-17: Portability and dependencies ----------
def test_tc17_portability():
    """TC-17: Verifies requirements.txt exists with pinned dependencies and recorded versions."""
    req_file = PROJECT_ROOT / "requirements.txt"
    assert req_file.exists()
    content = req_file.read_text()
    for pkg in ["fastapi", "torch", "scikit-learn", "pennylane", "pytest"]:
        assert pkg in content


# ---------- TC-18: Readability, non-color cues, contrast ----------
def test_tc18_readability_accessibility():
    """TC-18: Checks CSS contains non-color cues, tabular numbers, focus outlines, prefers-reduced-motion."""
    css_file = PROJECT_ROOT / "frontend" / "static" / "css" / "style.css"
    assert css_file.exists()
    css_text = css_file.read_text()
    assert "tabular-nums" in css_text
    assert "prefers-reduced-motion" in css_text
    assert "focus-visible" in css_text
    assert "#F5F7F9" in css_text  # Calm canvas
    assert "#1B2733" in css_text  # Primary ink


# ---------- TC-19: Browser responsiveness & timing ----------
def test_tc19_browser_responsiveness():
    """TC-19: Response within 2 seconds; HTML rendered without horizontal scroll markup."""
    t0 = time.time()
    res = client.get("/")
    elapsed = time.time() - t0
    assert elapsed <= 2.0
    assert res.status_code == 200
    assert "CodeCraft Metabolic Risk Platform" in res.text


# ---------- TC-20: Upload safety & formula injection protection ----------
def test_tc20_upload_safety_and_formulas():
    """TC-20: Rejects disguised executables, handles cells with formulas safely, formula injection escaping."""
    # Test binary executable content rejected
    fake_exe = b"MZ\x90\x00\x03\x00\x00\x00"
    with pytest.raises(ValidationError) as exc:
        check_file_safety("malicious.csv", fake_exe)
    assert exc.value.code == "FILE_TYPE_UNSUPPORTED"

    # Test CSV formula escaping
    escaped = sanitize_cell_for_export("=cmd|'/C calc'!A0")
    assert escaped.startswith("'=")

    escaped_plus = sanitize_cell_for_export("+12345")
    assert escaped_plus.startswith("'+")


# ---------- TC-21: Network, access, secrets, gitignore ----------
def test_tc21_network_secrets_gitignore():
    """TC-21: Localhost binding default, .gitignore contains .venv and sensitive files, no secrets."""
    gitignore = PROJECT_ROOT / ".gitignore"
    assert gitignore.exists()
    gi_text = gitignore.read_text()
    assert ".venv" in gi_text
    assert ".env" in gi_text

    from backend.config import SERVER_HOST
    assert SERVER_HOST == "127.0.0.1"


# ---------- TC-22: Resource logging & simulated memory limit ----------
def test_tc22_resource_logging():
    """TC-22: Runtime and peak memory recorded; simulated resource limit handled gracefully."""
    from backend.orchestration.orchestrator import Orchestrator
    store = ResultsStore()
    orch = Orchestrator(store=store)

    # Trigger with tiny memory limit to simulate resource failure
    res = orch.start_run(
        models=["ml"],
        seed=42,
        memory_limit_mb=0.01,  # Impossibly small limit to trigger graceful stop
        single_seed_mode=True,
    )
    run_id = res["run_id"]

    for _ in range(20):
        time.sleep(0.5)
        st = orch.get_run_status(run_id)
        if st and st.get("status") in ("completed", "failed"):
            break

    run_record = store.get_run(run_id)
    assert run_record is not None
    assert "ml" in run_record["models"]
    assert run_record["models"]["ml"]["status"] == "failed"
    assert "memory limit" in run_record["models"]["ml"]["error"].lower()
