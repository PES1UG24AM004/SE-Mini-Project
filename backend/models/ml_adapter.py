"""Classical Machine Learning adapter using scikit-learn."""
import sys
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.utils.class_weight import compute_sample_weight

from backend.data.preprocessor import make_standard_preprocessor
from backend.models.base import ModelAdapter


class MLAdapter(ModelAdapter):
    """Classical ML model adapter wrapping HistGradientBoostingClassifier."""

    def __init__(
        self,
        feature_cols: List[str],
        numeric_cols: List[str],
        categorical_cols: List[str],
        seed: int = 42,
        learning_rate: float = 0.05,
        max_iter: int = 100,
        max_leaf_nodes: int = 8,
    ):
        self.feature_cols = list(feature_cols)
        self.numeric_cols = [c for c in self.feature_cols if c in numeric_cols]
        self.categorical_cols = [c for c in self.feature_cols if c in categorical_cols]
        self.seed = int(seed)
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.max_leaf_nodes = max_leaf_nodes

        self.preprocessor_: Optional[Any] = None
        self.classifier_: Optional[HistGradientBoostingClassifier] = None

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "MLAdapter":
        """Fits preprocessing and classifier on training data only."""
        X_sub = X[self.feature_cols]
        self.preprocessor_ = make_standard_preprocessor(self.numeric_cols, self.categorical_cols).fit(X_sub)
        X_trans = self.preprocessor_.transform(X_sub)

        sample_weights = compute_sample_weight("balanced", y)
        self.classifier_ = HistGradientBoostingClassifier(
            learning_rate=self.learning_rate,
            max_iter=self.max_iter,
            max_leaf_nodes=self.max_leaf_nodes,
            early_stopping=False,
            random_state=self.seed,
        )
        self.classifier_.fit(X_trans, y, sample_weight=sample_weights)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Transforms input using fitted preprocessor and returns positive class probability."""
        if self.preprocessor_ is None or self.classifier_ is None:
            raise RuntimeError("MLAdapter must be fitted before predict_proba.")
        X_sub = X[self.feature_cols]
        X_trans = self.preprocessor_.transform(X_sub)
        probs = self.classifier_.predict_proba(X_trans)
        return probs[:, 1].astype(np.float64)

    def describe(self) -> Dict[str, Any]:
        return {
            "family": "ml",
            "model_name": "HistGradientBoosting",
            "backend": "CPU",
            "seed": self.seed,
            "feature_set": self.feature_cols,
            "n_features": len(self.feature_cols),
            "n_transformed_features": len(self.preprocessor_.get_feature_names_out()) if self.preprocessor_ else 8,
            "hyperparameters": {
                "learning_rate": self.learning_rate,
                "max_iter": self.max_iter,
                "max_leaf_nodes": self.max_leaf_nodes,
                "class_weight": "balanced (via compute_sample_weight)",
                "early_stopping": False,
            },
            "library_versions": {
                "python": sys.version.split()[0],
                "scikit-learn": sklearn.__version__,
                "numpy": np.__version__,
                "pandas": pd.__version__,
            },
            "limitations": [
                "Tree-based ensemble cannot extrapolate outside the domain of training predictor ranges.",
                "Cross-sectional survey data; identifies concurrent risk rather than predicting incidence.",
                "Unweighted survey sample; reflects cohort rather than national prevalence.",
            ],
        }
