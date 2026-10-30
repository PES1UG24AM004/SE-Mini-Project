"""Dataset and file validator ensuring schema, privacy, and safety compliance."""
import io
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from backend.config import (
    ALLOWED_EXTENSIONS,
    FORBIDDEN_COLUMNS,
    MAX_FILE_SIZE_BYTES,
    NEGATIVE_CLASS,
    POSITIVE_CLASS,
    TARGET_COLUMN,
)


class ValidationError(Exception):
    """Raised when data validation fails."""
    def __init__(self, message: str, code: str = "VALIDATION_FAILED", issues: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.issues = issues or [{"field": "general", "error": message}]


def check_file_safety(filename: str, content: bytes) -> None:
    """Validates file extension, size, and content binary safety (rejects disguised executables)."""
    # 1. Size check
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ValidationError(
            f"File exceeds maximum allowed size of 50 MB (got {len(content) / (1024 * 1024):.2f} MB)",
            code="FILE_TOO_LARGE",
            issues=[{"field": "file_size", "error": "Exceeds 50 MB limit"}],
        )

    # 2. Extension check
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file extension '{ext}'. Only .csv files are supported.",
            code="FILE_TYPE_UNSUPPORTED",
            issues=[{"field": "filename", "error": f"Invalid extension '{ext}', expected .csv"}],
        )

    # 3. Binary executable signature check (e.g. DOS MZ header, ELF \x7fELF, Mach-O, or null bytes)
    if content.startswith(b"MZ") or content.startswith(b"\x7fELF") or b"\x00" in content[:2048]:
        raise ValidationError(
            "Uploaded file appears to be a binary executable or contains invalid binary data.",
            code="FILE_TYPE_UNSUPPORTED",
            issues=[{"field": "file_content", "error": "Binary executable format detected"}],
        )


def sanitize_cell_for_export(val: Any) -> Any:
    """Sanitizes text values to prevent CSV formula injection in spreadsheet viewers."""
    if isinstance(val, str):
        val_strip = val.strip()
        if val_strip and val_strip[0] in ("=", "+", "-", "@", "\t", "\r"):
            return "'" + val
    return val


def validate_dataframe(
    df: pd.DataFrame,
    is_split_file: bool = False,
    split_name: str = "dataset"
) -> Dict[str, Any]:
    """
    Validates a pandas DataFrame for schema, types, missingness, target classes, and privacy.
    Returns a comprehensive validation dictionary with timings and every identified issue.
    """
    t0 = time.time()
    issues: List[Dict[str, Any]] = []

    # 1. Check duplicate columns
    if df.columns.duplicated().any():
        dups = df.columns[df.columns.duplicated()].unique().tolist()
        issues.append({
            "field": "columns",
            "error": f"Duplicate column names found: {dups}",
            "type": "duplicate_columns"
        })

    # 2. Check target presence and integrity
    if TARGET_COLUMN not in df.columns:
        issues.append({
            "field": TARGET_COLUMN,
            "error": f"Required target column '{TARGET_COLUMN}' is missing.",
            "type": "missing_target"
        })
    else:
        # Check target missing values
        null_target_count = int(df[TARGET_COLUMN].isna().sum())
        if null_target_count > 0:
            issues.append({
                "field": TARGET_COLUMN,
                "error": f"Target column '{TARGET_COLUMN}' contains {null_target_count} missing values.",
                "type": "null_target"
            })

        # Check unique labels
        unique_labels = set(df[TARGET_COLUMN].dropna().unique())
        valid_labels = {POSITIVE_CLASS, NEGATIVE_CLASS}
        if not unique_labels.issubset(valid_labels):
            bad_labels = list(unique_labels - valid_labels)
            issues.append({
                "field": TARGET_COLUMN,
                "error": f"Target contains unexpected class labels: {bad_labels}. Expected only {valid_labels}.",
                "type": "invalid_classes"
            })

        if len(unique_labels) < 2 and len(df) >= 2:
            issues.append({
                "field": TARGET_COLUMN,
                "error": f"Both target classes must be present, found only: {list(unique_labels)}",
                "type": "single_class"
            })

    # 3. Check for privacy / forbidden survey identifier columns (SR-1, FR-12, TC-09)
    found_forbidden = [c for c in df.columns if c.upper() in FORBIDDEN_COLUMNS or c.lower() in ("participant_id", "patient_id", "ssn", "name")]
    if found_forbidden:
        issues.append({
            "field": "forbidden_columns",
            "error": f"Forbidden or identifier-leakage columns detected: {found_forbidden}. Must be removed before training.",
            "type": "privacy_violation",
            "columns": found_forbidden
        })

    # 4. Check data types and value ranges
    col_missing = df.isna().mean().to_dict()
    high_missing = [c for c, m in col_missing.items() if m > 0.50 and c != TARGET_COLUMN]
    if high_missing:
        issues.append({
            "field": "high_missingness",
            "error": f"{len(high_missing)} columns have >50% missing values (e.g. {high_missing[:5]})",
            "type": "warning",
            "columns": high_missing
        })

    # Check key numeric fields if present
    for num_col in ["RIDAGEYR", "BMXBMI", "BMXWAIST"]:
        if num_col in df.columns:
            # Check for non-numeric entries
            non_num = pd.to_numeric(df[num_col], errors="coerce")
            unparseable = int(non_num.isna().sum() - df[num_col].isna().sum())
            if unparseable > 0:
                issues.append({
                    "field": num_col,
                    "error": f"Column '{num_col}' contains {unparseable} non-numeric string values.",
                    "type": "type_error"
                })
            # Check physical sanity ranges
            valid_vals = non_num.dropna()
            if len(valid_vals) > 0:
                if valid_vals.min() < 0:
                    issues.append({
                        "field": num_col,
                        "error": f"Column '{num_col}' contains negative values (min: {valid_vals.min()}).",
                        "type": "range_error"
                    })
                if num_col == "RIDAGEYR" and valid_vals.max() > 120:
                    issues.append({
                        "field": num_col,
                        "error": f"Age value exceeds human maximum: {valid_vals.max()}.",
                        "type": "range_error"
                    })
                if num_col == "BMXBMI" and valid_vals.max() > 150:
                    issues.append({
                        "field": num_col,
                        "error": f"BMI value exceeds plausible range: {valid_vals.max()}.",
                        "type": "range_error"
                    })

    # Compute statistics
    class_counts = {}
    if TARGET_COLUMN in df.columns:
        class_counts = {str(k): int(v) for k, v in df[TARGET_COLUMN].value_counts(dropna=False).items()}

    elapsed = round(time.time() - t0, 4)
    # Determine valid: errors (excluding warnings) make valid False
    has_blocking_errors = any(issue.get("type") != "warning" for issue in issues)

    return {
        "valid": not has_blocking_errors,
        "split_name": split_name,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": list(df.columns),
        "class_counts": class_counts,
        "missing_rate": round(float(df.isna().mean().mean()), 4),
        "issues": issues,
        "validation_time_sec": elapsed,
    }


def parse_csv_bytes(content: bytes, filename: str = "dataset.csv") -> pd.DataFrame:
    """Safely decodes and parses CSV bytes into a DataFrame without executing code."""
    check_file_safety(filename, content)
    try:
        # Decode UTF-8 or fall back to latin1 safely
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1")
        df = pd.read_csv(io.StringIO(text))
        return df
    except Exception as e:
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(
            f"Failed to parse CSV file: {str(e)}",
            code="SCHEMA_INVALID",
            issues=[{"field": "csv_parser", "error": str(e)}]
        )
