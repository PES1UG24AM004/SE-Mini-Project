"""Data preprocessing, splitting, feature selection, and transformation routines."""
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_selection import mutual_info_classif
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, StandardScaler

from backend.config import (
    ADMIN_EXACT_DROP,
    CATEGORICAL_FEATURES,
    DATASET_VERSION,
    DEFAULT_SEED,
    DEFAULT_SHARED_FEATURES,
    FORBIDDEN_COLUMNS,
    MAX_TRANSFORMED_DIM,
    NEGATIVE_CLASS,
    NUMERIC_FEATURES,
    POSITIVE_CLASS,
    PROJECT_ROOT,
    RESULTS_DIR,
    TARGET_COLUMN,
)


def compute_file_sha256(paths: List[Union[str, Path]]) -> str:
    """Computes SHA-256 hash across a sequence of files."""
    h = hashlib.sha256()
    for p in paths:
        path = Path(p)
        if path.exists():
            h.update(path.read_bytes())
    return h.hexdigest()


def compute_df_sha256(dfs: List[pd.DataFrame]) -> str:
    """Computes deterministic SHA-256 hash of DataFrames."""
    h = hashlib.sha256()
    for df in dfs:
        h.update(pd.util.hash_pandas_object(df, index=True).to_numpy().tobytes())
    return h.hexdigest()


def learn_feature_pruning(X_tr: pd.DataFrame) -> Dict[str, str]:
    """Identifies columns to drop based on training data only."""
    dropped: Dict[str, str] = {}
    for c in X_tr.columns:
        if c.upper() in FORBIDDEN_COLUMNS:
            dropped[c] = "forbidden / survey design / leakage column"
            continue
        if (c.startswith("BMI") and c != "BMXBMI") or c in ADMIN_EXACT_DROP:
            dropped[c] = "administrative / comment-code column"
            continue
        miss = float(X_tr[c].isna().mean())
        if miss > 0.50:
            dropped[c] = f">50% missing in train ({miss:.1%})"
            continue
        if X_tr[c].nunique(dropna=True) <= 1:
            dropped[c] = "constant in train"
            continue
    return dropped


def classify_column_type(series: pd.Series) -> str:
    """Classifies a series as numeric or categorical (integer-coded with <=10 unique is categorical)."""
    if (not pd.api.types.is_numeric_dtype(series)) or pd.api.types.is_bool_dtype(series):
        return "categorical"
    v = series.dropna().to_numpy(dtype=float)
    if v.size and np.all(np.isfinite(v)) and np.all(v == np.round(v)) and len(np.unique(v)) <= 10:
        return "categorical"
    return "numeric"


def make_standard_preprocessor(numeric_cols: List[str], categorical_cols: List[str]) -> ColumnTransformer:
    """Builds standard ColumnTransformer pipeline."""
    transformers = []
    if numeric_cols:
        transformers.append((
            "num",
            Pipeline([
                ("imp", SimpleImputer(strategy="median")),
                ("sc", StandardScaler()),
            ]),
            list(numeric_cols),
        ))
    if categorical_cols:
        transformers.append((
            "cat",
            Pipeline([
                ("imp", SimpleImputer(strategy="most_frequent")),
                ("oh", OneHotEncoder(handle_unknown="ignore", sparse_output=False, drop="if_binary")),
            ]),
            list(categorical_cols),
        ))
    return ColumnTransformer(transformers, remainder="drop", verbose_feature_names_out=False)


class AngleEncoder:
    """Angle-encoding preprocessor for PennyLane: scales features to [0, pi] and clips."""
    def __init__(self, numeric_cols: List[str], categorical_cols: List[str]):
        self.numeric_cols = list(numeric_cols)
        self.categorical_cols = list(categorical_cols)
        self.cols_ = self.numeric_cols + self.categorical_cols
        self.pre_: Optional[ColumnTransformer] = None
        self.scaler_: Optional[MinMaxScaler] = None

    def fit(self, X: pd.DataFrame) -> "AngleEncoder":
        """Fits imputer, standard scaler/encoder, and [0, pi] scaler on TRAIN rows only."""
        self.pre_ = make_standard_preprocessor(self.numeric_cols, self.categorical_cols).fit(X[self.cols_])
        transformed = self.pre_.transform(X[self.cols_])
        self.scaler_ = MinMaxScaler(feature_range=(0.0, float(np.pi))).fit(transformed)
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transforms and clips features to [0, pi]."""
        if self.pre_ is None or self.scaler_ is None:
            raise RuntimeError("AngleEncoder must be fit before transform.")
        raw = self.scaler_.transform(self.pre_.transform(X[self.cols_]))
        return np.clip(raw, 0.0, float(np.pi))

    def n_features(self) -> int:
        if self.pre_ is None:
            return 0
        return int(len(self.pre_.get_feature_names_out()))


class DataSplitManager:
    """Handles dataset loading, splitting, and shared feature set curation."""

    def __init__(self, project_root: Path = PROJECT_ROOT):
        self.root = project_root
        self.results_dir = project_root / "results"
        self.shared_feature_path = self.results_dir / "shared_feature_set.json"

    def load_trio_splits(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
        """Loads fixed train.csv, validation.csv, test.csv and computes split_hash."""
        # Check canonical data/splits/ directory first, then root fallback
        train_path = self.root / "data" / "splits" / "train.csv"
        val_path = self.root / "data" / "splits" / "validation.csv"
        test_path = self.root / "data" / "splits" / "test.csv"

        if not (train_path.exists() and val_path.exists() and test_path.exists()):
            train_path = self.root / "train.csv"
            val_path = self.root / "validation.csv"
            test_path = self.root / "test.csv"

        if not (train_path.exists() and val_path.exists() and test_path.exists()):
            raise FileNotFoundError("Missing one or more required split files: train.csv, validation.csv, test.csv")

        train_df = pd.read_csv(train_path)
        val_df = pd.read_csv(val_path)
        test_df = pd.read_csv(test_path)

        # Remove forbidden columns if present
        for df in (train_df, val_df, test_df):
            for col in list(df.columns):
                if col.upper() in FORBIDDEN_COLUMNS:
                    df.drop(columns=[col], inplace=True)

        split_hash = compute_file_sha256([train_path, val_path, test_path])
        return train_df, val_df, test_df, split_hash

    def split_single_csv(
        self,
        df: pd.DataFrame,
        seed: int = DEFAULT_SEED,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
        """Creates reproducible stratified split (70/15/15) from a single CSV."""
        # Clean forbidden columns
        clean_df = df.copy()
        for col in list(clean_df.columns):
            if col.upper() in FORBIDDEN_COLUMNS:
                clean_df.drop(columns=[col], inplace=True)

        y = clean_df[TARGET_COLUMN]
        # First split into train and temp (val + test)
        temp_ratio = val_ratio + test_ratio
        train_df, temp_df = train_test_split(
            clean_df,
            test_size=temp_ratio,
            random_state=seed,
            stratify=y,
        )
        # Split temp into val and test equally (0.15 / 0.30 = 0.5)
        val_test_ratio = test_ratio / temp_ratio
        val_df, test_df = train_test_split(
            temp_df,
            test_size=val_test_ratio,
            random_state=seed,
            stratify=temp_df[TARGET_COLUMN],
        )

        split_hash = compute_df_sha256([train_df, val_df, test_df])
        return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True), split_hash

    def derive_or_load_shared_features(
        self,
        train_df: pd.DataFrame,
        split_hash: str,
        seed: int = DEFAULT_SEED,
        max_dim: int = MAX_TRANSFORMED_DIM,
    ) -> Dict[str, Any]:
        """
        Loads shared_feature_set.json if split_hash matches.
        Otherwise derives the feature set using training data only (mutual info ranking) and saves it.
        """
        if self.shared_feature_path.exists():
            try:
                with open(self.shared_feature_path, "r", encoding="utf-8") as f:
                    shared = json.load(f)
                if (
                    shared.get("split_hash") == split_hash
                    and set(shared.get("selected_features", [])) == set(DEFAULT_SHARED_FEATURES)
                    and shared.get("transformed_dim", 0) <= max_dim
                ):
                    return shared
            except Exception:
                pass

        # Compute from train_df only
        X_train = train_df.drop(columns=[TARGET_COLUMN])
        y_train = (train_df[TARGET_COLUMN] == POSITIVE_CLASS).astype(int).to_numpy()

        dropped = learn_feature_pruning(X_train)
        kept_cols = [c for c in X_train.columns if c not in dropped]
        col_type = {c: classify_column_type(X_train[c]) for c in kept_cols}
        numeric_cols = [c for c in kept_cols if col_type[c] == "numeric"]
        cat_cols = [c for c in kept_cols if col_type[c] == "categorical"]

        # Impute train for MI computation
        parts = []
        if numeric_cols:
            parts.append(pd.DataFrame(
                SimpleImputer(strategy="median").fit_transform(X_train[numeric_cols]),
                columns=numeric_cols,
                index=X_train.index,
            ))
        cat_codes = {}
        for c in cat_cols:
            v = SimpleImputer(strategy="most_frequent").fit_transform(X_train[[c]])[:, 0]
            cat_codes[c] = pd.factorize(pd.Series(v))[0]
        if cat_codes:
            parts.append(pd.DataFrame(cat_codes, index=X_train.index))
        X_mi = pd.concat(parts, axis=1)[kept_cols]

        mi = {
            c: float(mutual_info_classif(
                X_mi[[c]].to_numpy(dtype=float),
                y_train,
                discrete_features=(c in cat_cols),
                random_state=seed,
            )[0])
            for c in kept_cols
        }

        order = {c: i for i, c in enumerate(kept_cols)}
        ranking = sorted(kept_cols, key=lambda c: (-mi[c], order[c]))

        def calc_dim(cols: List[str]) -> int:
            num = [c for c in cols if c in numeric_cols]
            cat = [c for c in cols if c in cat_cols]
            return len(make_standard_preprocessor(num, cat).fit(X_train[list(cols)]).get_feature_names_out())

        selected: List[str] = []
        for f in ranking:
            d = calc_dim(selected + [f])
            if d <= max_dim:
                selected.append(f)

        sel_num = [c for c in selected if col_type[c] == "numeric"]
        sel_cat = [c for c in selected if col_type[c] == "categorical"]
        final_dim = calc_dim(selected)

        shared_obj = {
            "selected_features": selected,
            "numeric_features": sel_num,
            "categorical_features": sel_cat,
            "transformed_dim": int(final_dim),
            "mi_ranking": [
                {"feature": f, "mutual_info": round(mi[f], 5), "type": col_type[f]}
                for f in ranking
            ],
            "split_hash": split_hash,
            "seed": seed,
            "dataset_version": DATASET_VERSION,
            "created": pd.Timestamp.now(tz="UTC").isoformat(),
        }

        # Save atomically
        self.results_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self.shared_feature_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(shared_obj, f, indent=2)
        tmp_path.replace(self.shared_feature_path)

        return shared_obj
