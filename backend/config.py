"""Application configuration and constants."""
from pathlib import Path
import os
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT
RESULTS_DIR = PROJECT_ROOT / "results"
UPLOADS_DIR = PROJECT_ROOT / "uploads"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

DATASET_VERSION = "nhanes-2017-2018-v1"
TARGET_COLUMN = "risk_label"
POSITIVE_CLASS = "Elevated Risk"
NEGATIVE_CLASS = "Normal"

FORBIDDEN_COLUMNS = [
    "SEQN",
    "LBXGH",
    "WTINT2YR",
    "WTMEC2YR",
    "SDMVPSU",
    "SDMVSTRA",
]

ADMIN_EXACT_DROP = {"BMDSTATS", "RIDSTATR", "SDDSRVYR", "RIDEXMON"}

DEFAULT_SEED = 42
DEFAULT_SEEDS = [42, 43, 44, 45, 46]

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {".csv"}

WARNING_TEXT = "Research/educational use only. Not a diagnosis or medical advice."
RANKING_METRIC = "sensitivity@spec>=0.70"
MIN_SPECIFICITY_TARGET = 0.70

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000

# MLflow Experiment Tracking Configuration
MLFLOW_ENABLED = os.environ.get("MLFLOW_ENABLED", "true").lower() in ("true", "1", "yes")
MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
MLFLOW_EXPERIMENT_NAME = os.environ.get("MLFLOW_EXPERIMENT_NAME", "CodeCraft-Metabolic-Risk-Benchmark")
MLFLOW_TRACKING_USERNAME = os.environ.get("MLFLOW_TRACKING_USERNAME", "")
MLFLOW_TRACKING_PASSWORD = os.environ.get("MLFLOW_TRACKING_PASSWORD", "")
MLFLOW_ARTIFACTS_DIR = PROJECT_ROOT / "mlartifacts"


# Main shared feature set configuration
MAX_TRANSFORMED_DIM = 8
DEFAULT_SHARED_FEATURES = [
    "RIDAGEYR",
    "DMDHRAGZ",
    "DMDHHSZE",
    "BMXWAIST",
    "BMXBMI",
]
NUMERIC_FEATURES = ["RIDAGEYR", "DMDHHSZE", "BMXWAIST", "BMXBMI"]
CATEGORICAL_FEATURES = ["DMDHRAGZ"]
