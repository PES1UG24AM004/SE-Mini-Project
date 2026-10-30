"""Abstract base class defining the common ModelAdapter interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


class ModelAdapter(ABC):
    """
    Common adapter interface for ML, DL, and QML models.
    All model families accept the same input format and return probabilities for the positive class.
    """

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "ModelAdapter":
        """
        Fits the model pipeline using training data only.
        Returns self.
        """
        pass

    @abstractmethod
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predicts positive-class probabilities for input records.
        Returns a 1D numpy array of floats in range [0, 1].
        """
        pass

    @abstractmethod
    def describe(self) -> Dict[str, Any]:
        """
        Returns machine-readable configuration, backend, hyper-parameters,
        library versions, and known model limitations.
        """
        pass
