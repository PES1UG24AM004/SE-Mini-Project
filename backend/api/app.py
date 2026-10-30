"""FastAPI application providing REST endpoints and serving the local research interface."""
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.config import (
    DATASET_VERSION,
    DEFAULT_SEED,
    DEFAULT_SHARED_FEATURES,
    NEGATIVE_CLASS,
    POSITIVE_CLASS,
    PROJECT_ROOT,
    RANKING_METRIC,
    SERVER_HOST,
    SERVER_PORT,
    TARGET_COLUMN,
    WARNING_TEXT,
)
from backend.data.preprocessor import DataSplitManager
from backend.data.validator import (
    ValidationError,
    check_file_safety,
    parse_csv_bytes,
    validate_dataframe,
)
from backend.orchestration.orchestrator import Orchestrator
from backend.reports.generator import ReportGenerator
from backend.storage.store import ResultsStore

app = FastAPI(
    title="CodeCraft Early Metabolic Risk Detection",
    description="Local-first comparison platform for Classical ML vs Deep Learning vs Quantum ML",
    version="1.0.0",
)

# Enable CORS for localhost access only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Persistent stores and orchestrator
store = ResultsStore()
split_manager = DataSplitManager()
orchestrator = Orchestrator(store=store)

# Static and template directories
FRONTEND_DIR = PROJECT_ROOT / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"
TEMPLATES_DIR = FRONTEND_DIR / "templates"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "css").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "js").mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def make_error_response(status_code: int, code: str, message: str, issues: Optional[List[Any]] = None) -> JSONResponse:
    """Formats standardized, safe error responses without stack traces."""
    req_id = str(uuid.uuid4())[:8]
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "issues": issues or [{"field": "general", "error": message}],
                "requestId": req_id,
            }
        },
    )


# ---------- Pydantic Schemas ----------
class RunRequest(BaseModel):
    datasetId: Optional[str] = DATASET_VERSION
    models: Optional[List[str]] = ["ml", "dl", "qml"]
    seed: Optional[int] = DEFAULT_SEED
    singleSeedMode: Optional[bool] = False


class PredictRequest(BaseModel):
    runId: Optional[str] = "reference_baseline"
    family: Optional[str] = "ml"
    features: Dict[str, Any]


# ---------- REST Endpoints ----------

@app.get("/api/dataset")
def get_dataset_info():
    """Returns dataset version, label definition, row/column counts, class balance, and split details."""
    try:
        train_df, val_df, test_df, split_hash = split_manager.load_trio_splits()
        total_rows = len(train_df) + len(val_df) + len(test_df)
        all_cols = list(train_df.columns)

        class_counts = {
            POSITIVE_CLASS: int((train_df[TARGET_COLUMN] == POSITIVE_CLASS).sum() +
                                (val_df[TARGET_COLUMN] == POSITIVE_CLASS).sum() +
                                (test_df[TARGET_COLUMN] == POSITIVE_CLASS).sum()),
            NEGATIVE_CLASS: int((train_df[TARGET_COLUMN] == NEGATIVE_CLASS).sum() +
                                (val_df[TARGET_COLUMN] == NEGATIVE_CLASS).sum() +
                                (test_df[TARGET_COLUMN] == NEGATIVE_CLASS).sum()),
        }

        shared_info = split_manager.derive_or_load_shared_features(train_df, split_hash)

        return {
            "cycle": "NHANES 2017-2018",
            "datasetId": DATASET_VERSION,
            "version": DATASET_VERSION,
            "target": TARGET_COLUMN,
            "positiveClass": POSITIVE_CLASS,
            "negativeClass": NEGATIVE_CLASS,
            "labelDefinition": "Normal: HbA1c < 5.7%; Elevated Risk: 5.7% <= HbA1c < 6.5%. Excludes HbA1c >= 6.5%.",
            "warning": WARNING_TEXT,
            "rows": total_rows,
            "columns": len(all_cols),
            "splitCounts": {
                "train": len(train_df),
                "validation": len(val_df),
                "test": len(test_df),
            },
            "classCounts": class_counts,
            "splitHash": split_hash,
            "sharedFeatures": shared_info.get("selected_features", DEFAULT_SHARED_FEATURES),
            "transformedDimension": shared_info.get("transformed_dim", 8),
            "forbiddenFieldsExcluded": [
                "SEQN", "LBXGH", "WTINT2YR", "WTMEC2YR", "SDMVPSU", "SDMVSTRA"
            ],
        }
    except Exception as e:
        return make_error_response(404, "DATASET_NOT_PREPARED", f"Failed to load dataset: {str(e)}")


@app.post("/api/datasets/validate")
async def validate_dataset(file: Optional[UploadFile] = None):
    """
    Validates either the existing prepared NHANES trio files or an uploaded CSV file.
    Returns all detected issues, row/column counts, class distribution, and validation timing.
    """
    try:
        if file is not None:
            content = await file.read()
            check_file_safety(file.filename or "uploaded.csv", content)
            df = parse_csv_bytes(content, file.filename or "uploaded.csv")
            report = validate_dataframe(df, is_split_file=False, split_name=file.filename or "uploaded")
            return {
                "valid": report["valid"],
                "source": "upload",
                "filename": file.filename,
                "rows": report["rows"],
                "columns": report["columns"],
                "classCounts": report["class_counts"],
                "missingRate": report["missing_rate"],
                "issues": report["issues"],
                "validationTimeSec": report["validation_time_sec"],
            }
        else:
            # Validate trio files
            train_df, val_df, test_df, _ = split_manager.load_trio_splits()
            t_report = validate_dataframe(train_df, is_split_file=True, split_name="train.csv")
            v_report = validate_dataframe(val_df, is_split_file=True, split_name="validation.csv")
            ts_report = validate_dataframe(test_df, is_split_file=True, split_name="test.csv")

            all_issues = t_report["issues"] + v_report["issues"] + ts_report["issues"]
            total_rows = t_report["rows"] + v_report["rows"] + ts_report["rows"]
            combined_class_counts = {
                POSITIVE_CLASS: (t_report["class_counts"].get(POSITIVE_CLASS, 0) +
                                 v_report["class_counts"].get(POSITIVE_CLASS, 0) +
                                 ts_report["class_counts"].get(POSITIVE_CLASS, 0)),
                NEGATIVE_CLASS: (t_report["class_counts"].get(NEGATIVE_CLASS, 0) +
                                 v_report["class_counts"].get(NEGATIVE_CLASS, 0) +
                                 ts_report["class_counts"].get(NEGATIVE_CLASS, 0)),
            }
            total_time = round(t_report["validation_time_sec"] + v_report["validation_time_sec"] + ts_report["validation_time_sec"], 4)

            return {
                "valid": t_report["valid"] and v_report["valid"] and ts_report["valid"],
                "source": "prepared_nhanes_trio",
                "rows": total_rows,
                "columns": t_report["columns"],
                "classCounts": combined_class_counts,
                "missingRate": round((t_report["missing_rate"] + v_report["missing_rate"] + ts_report["missing_rate"]) / 3, 4),
                "issues": all_issues,
                "validationTimeSec": total_time,
            }
    except ValidationError as ve:
        return make_error_response(422 if ve.code != "FILE_TOO_LARGE" else 413, ve.code, ve.message, ve.issues)
    except Exception as e:
        return make_error_response(422, "VALIDATION_FAILED", str(e))


@app.post("/api/runs", status_code=202)
def start_model_run(payload: RunRequest):
    """Starts training and evaluation on the shared split and acknowledges within 2 seconds."""
    if orchestrator.is_running():
        return make_error_response(409, "RUN_IN_PROGRESS", "Another run is currently active. Please wait for it to complete.")

    try:
        res = orchestrator.start_run(
            dataset_id=payload.datasetId or DATASET_VERSION,
            models=payload.models,
            seed=payload.seed or DEFAULT_SEED,
            single_seed_mode=payload.singleSeedMode or False,
        )
        return res
    except Exception as e:
        return make_error_response(500, "MODEL_FAILED", f"Failed to initialize run: {str(e)}")


@app.get("/api/runs/{runId}")
def get_run_progress(runId: str):
    """Retrieves execution status, model progress, elapsed runtime, and any readable error."""
    status = orchestrator.get_run_status(runId)
    if not status:
        return make_error_response(404, "RUN_NOT_FOUND", f"Run with ID '{runId}' was not found. Please initiate a run first.")
    return status


@app.get("/api/comparison")
def get_comparison(runId: Optional[str] = Query("reference_baseline")):
    """Returns side-by-side comparison metrics and confusion matrices for the requested run."""
    run_id = runId or "reference_baseline"

    # Check if run is still in progress
    if orchestrator.active_run_id == run_id:
        return make_error_response(409, "RUN_NOT_COMPLETE", "Run is currently in progress. Please check status at /api/runs/{runId}.")

    record = store.get_run(run_id)
    if not record:
        return make_error_response(404, "RUN_NOT_FOUND", f"No comparison results found for runId '{run_id}'.")

    models_list = []
    for fam in ["ml", "dl", "qml"]:
        if fam in record.get("models", {}):
            m = record["models"][fam]
            models_list.append({
                "family": fam,
                "modelName": m.get("model_name"),
                "status": m.get("status"),
                "backend": m.get("backend"),
                "seed": m.get("seed"),
                "seeds": m.get("seeds"),
                "isMultiSeed": m.get("is_multi_seed", False),
                "threshold": m.get("threshold"),
                "metrics": m.get("metrics_at_threshold"),
                "metricsAt05": m.get("metrics_at_0.5"),
                "headlineMetrics": m.get("headline_metrics"),
                "ci95": m.get("ci95"),
                "confusion": m.get("confusion"),
                "confusionNote": m.get("confusion_note"),
                "rocCurve": m.get("roc_curve"),
                "runtimeSec": m.get("runtime_sec"),
                "peakMemoryMB": m.get("peak_memory_mb"),
                "error": m.get("error"),
            })

    return {
        "runId": record.get("run_id"),
        "source": record.get("source"),
        "datasetVersion": record.get("dataset_version"),
        "createdAt": record.get("created_at"),
        "splitHash": record.get("split_hash"),
        "splitProtocol": record.get("split_protocol"),
        "testSet": record.get("test_split", {}),
        "rankingMetric": record.get("ranking_metric", RANKING_METRIC),
        "thresholdRule": record.get("threshold_rule"),
        "warning": WARNING_TEXT,
        "models": models_list,
    }


@app.get("/api/models/{family}")
def get_model_details(family: str, runId: Optional[str] = Query("reference_baseline")):
    """Returns in-depth configuration, hyperparameters, feature set, and limitations for a model family."""
    fam = family.lower()
    run_id = runId or "reference_baseline"
    record = store.get_run(run_id)
    if not record:
        return make_error_response(404, "RUN_NOT_FOUND", f"Run with ID '{run_id}' not found.")

    model_info = record.get("models", {}).get(fam)
    if not model_info:
        return make_error_response(404, "RUN_NOT_FOUND", f"Model family '{family}' was not part of run '{run_id}'.")

    return {
        "runId": run_id,
        "family": fam,
        "modelName": model_info.get("model_name"),
        "status": model_info.get("status"),
        "backend": model_info.get("backend"),
        "seed": model_info.get("seed"),
        "seeds": model_info.get("seeds"),
        "runtimeSec": model_info.get("runtime_sec"),
        "peakMemoryMB": model_info.get("peak_memory_mb"),
        "hyperparameters": model_info.get("hyperparameters"),
        "features": record.get("feature_set", {}),
        "circuitDiagram": model_info.get("circuit_diagram"),
        "libraryVersions": model_info.get("library_versions"),
        "limitations": model_info.get("limitations", []),
        "warning": WARNING_TEXT,
    }


@app.post("/api/predict")
def predict_single_record(payload: PredictRequest):
    """Performs validated inference on a single participant record."""
    try:
        run_id = payload.runId or "reference_baseline"
        family = (payload.family or "ml").lower()
        res = orchestrator.predict_single_record(run_id, family, payload.features)
        if not res.get("valid", False):
            return JSONResponse(status_code=422, content=res)
        return res
    except Exception as e:
        return make_error_response(503, "PREDICTION_UNAVAILABLE", str(e))


@app.get("/api/reports/{runId}")
def export_aggregate_report(runId: str, format: Optional[str] = Query("json")):
    """Exports aggregate-only comparison report with full provenance in JSON, CSV, or HTML."""
    record = store.get_run(runId)
    if not record:
        return make_error_response(404, "RUN_NOT_FOUND", f"Run with ID '{runId}' not found.")

    fmt = (format or "json").lower()
    if fmt == "csv":
        csv_text = ReportGenerator.generate_csv_report(record)
        return Response(
            content=csv_text,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="codecraft_report_{runId}.csv"'},
        )
    elif fmt == "html":
        html_text = ReportGenerator.generate_html_report(record)
        return HTMLResponse(content=html_text)
    else:
        json_text = ReportGenerator.generate_json_report(record)
        return Response(
            content=json_text,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="codecraft_report_{runId}.json"'},
        )


@app.get("/api/runs_list")
def list_available_runs():
    """Lists all available run IDs."""
    return store.list_runs()


# ---------- Front-End Single-Page Application ----------

@app.get("/", response_class=HTMLResponse)
def index_page():
    """Serves the main application UI."""
    index_file = TEMPLATES_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>CodeCraft UI loading...</h1>")
