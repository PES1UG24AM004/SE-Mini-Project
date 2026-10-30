"""Stub model adapter demonstrating maintainability and pluggability (TC-16)."""
from typing import Any, Dict, List
import numpy as np
import pandas as pd
from backend.models.base import ModelAdapter


class StubAdapter(ModelAdapter):
    """Minimal pluggable model adapter for maintainability and regression testing."""

    def __init__(self, name: str = "StubModel", default_prob: float = 0.35):
        self.name = name
        self.default_prob = default_prob
        self.fitted_ = False
        self.feature_cols_: List[str] = []

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "StubAdapter":
        self.feature_cols_ = list(X.columns)
        self.fitted_ = True
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if not self.fitted_:
            raise RuntimeError("StubAdapter must be fitted before predict_proba.")
        return np.full(len(X), self.default_prob, dtype=np.float64)

    def describe(self) -> Dict[str, Any]:
        return {
            "family": "stub",
            "model_name": self.name,
            "backend": "Mock / Stub Engine",
            "features": self.feature_cols_,
            "fitted": self.fitted_,
            "hyperparameters": {"default_prob": self.default_prob},
            "limitations": ["Stub model for architectural maintainability testing only."],
        }
