"""Quantum Machine Learning adapter using PennyLane Variational Quantum Circuit on default.qubit simulator."""
import sys
import time
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import pennylane as qml
from sklearn.model_selection import StratifiedShuffleSplit
import torch

from backend.data.preprocessor import AngleEncoder
from backend.models.base import ModelAdapter


class QMLAdapter(ModelAdapter):
    """
    Variational Quantum Classifier implemented using PennyLane on the default.qubit simulator.
    Uses AngleEmbedding on 8 qubits, StronglyEntanglingLayers ansatz, and classical readout.
    """

    def __init__(
        self,
        feature_cols: List[str],
        numeric_cols: List[str],
        categorical_cols: List[str],
        seed: int = 42,
        n_layers: int = 2,
        lr: float = 0.05,
        epochs: int = 15,
        batch_size: int = 64,
        eval_batch_size: int = 256,
        subsample_n: int = 1500,
    ):
        self.feature_cols = list(feature_cols)
        self.numeric_cols = [c for c in self.feature_cols if c in numeric_cols]
        self.categorical_cols = [c for c in self.feature_cols if c in categorical_cols]
        self.seed = int(seed)
        self.n_layers = n_layers
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.eval_batch_size = eval_batch_size
        self.subsample_n = subsample_n

        self.encoder_: Optional[AngleEncoder] = None
        self.weights_: Optional[torch.Tensor] = None
        self.scale_a_: Optional[torch.Tensor] = None
        self.bias_b_: Optional[torch.Tensor] = None
        self.circuit_ = None
        self.device_ = None
        self.history_: Dict[str, Any] = {}
        self.diagram_: str = ""

    def _build_circuit(self, n_qubits: int):
        dev = qml.device("default.qubit", wires=n_qubits, shots=None)

        @qml.qnode(dev, interface="torch", diff_method="backprop")
        def circuit(inputs, weights):
            qml.AngleEmbedding(inputs, wires=range(n_qubits), rotation="Y")
            qml.StronglyEntanglingLayers(weights, wires=range(n_qubits))
            return qml.expval(qml.PauliZ(0))

        return dev, circuit

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "QMLAdapter":
        """Fits AngleEncoder on train and trains variational circuit weights using Adam."""
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)

        # 1. Fit AngleEncoder on training data only
        self.encoder_ = AngleEncoder(self.numeric_cols, self.categorical_cols).fit(X)
        Z_tr = self.encoder_.transform(X)
        n_qubits = self.encoder_.n_features()

        self.device_, self.circuit_ = self._build_circuit(n_qubits)

        # Draw circuit for documentation
        try:
            sample_in = torch.linspace(0.3, 2.8, n_qubits, dtype=torch.float64)
            sample_w = torch.zeros(self.n_layers, n_qubits, 3, dtype=torch.float64)
            self.diagram_ = qml.draw(self.circuit_, decimals=2)(sample_in, sample_w)
        except Exception:
            self.diagram_ = "Circuit diagram unavailable."

        # 2. Stratified subsample if configured and X is large
        if self.subsample_n and len(Z_tr) > self.subsample_n:
            sss = StratifiedShuffleSplit(n_splits=1, train_size=self.subsample_n, random_state=self.seed)
            sub_idx, _ = next(sss.split(Z_tr, y))
            Z_train_fit = Z_tr[sub_idx]
            y_train_fit = y[sub_idx]
        else:
            Z_train_fit = Z_tr
            y_train_fit = y

        # 3. Initialize parameters
        g = torch.Generator()
        g.manual_seed(self.seed)
        w = (torch.rand(self.n_layers, n_qubits, 3, generator=g, dtype=torch.float64) * 2.0 * np.pi).requires_grad_(True)
        a = torch.tensor(1.0, dtype=torch.float64, requires_grad=True)
        b = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)

        n_pos = int(np.sum(y_train_fit))
        n_neg = int(len(y_train_fit) - n_pos)
        pw = float(n_neg / max(n_pos, 1))

        loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pw], dtype=torch.float64))
        optimizer = torch.optim.Adam([w, a, b], lr=self.lr)

        X_t = torch.from_numpy(np.ascontiguousarray(Z_train_fit, dtype=np.float64))
        y_t = torch.from_numpy(np.asarray(y_train_fit, dtype=np.float64))

        epoch_losses: List[float] = []
        t0 = time.time()

        for epoch in range(self.epochs):
            perm = torch.randperm(len(X_t), generator=g)
            running_loss = 0.0
            cnt = 0
            for i in range(0, len(perm), self.batch_size):
                idx = perm[i : i + self.batch_size]
                optimizer.zero_grad()
                z = self.circuit_(X_t[idx], w).reshape(-1).to(torch.float64)
                logits = a * z + b
                loss = loss_fn(logits, y_t[idx])
                loss.backward()
                optimizer.step()
                running_loss += float(loss.item()) * len(idx)
                cnt += len(idx)
            ep_loss = running_loss / max(cnt, 1)
            epoch_losses.append(ep_loss)

        self.weights_ = w.detach().clone()
        self.scale_a_ = a.detach().clone()
        self.bias_b_ = b.detach().clone()

        self.history_ = {
            "train_loss": epoch_losses,
            "train_time_sec": round(time.time() - t0, 2),
            "n_parameters": int(self.weights_.numel() + 2),
            "n_qubits": n_qubits,
            "subsample_n": len(Z_train_fit),
        }
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Transforms input with AngleEncoder and computes quantum circuit probabilities."""
        if self.encoder_ is None or self.weights_ is None or self.circuit_ is None:
            raise RuntimeError("QMLAdapter must be fitted before predict_proba.")
        Z = self.encoder_.transform(X)

        out_probs = []
        with torch.no_grad():
            for i in range(0, len(Z), self.eval_batch_size):
                batch_Z = Z[i : i + self.eval_batch_size]
                X_b = torch.from_numpy(np.ascontiguousarray(batch_Z, dtype=np.float64))
                z = self.circuit_(X_b, self.weights_).reshape(-1).to(torch.float64)
                logits = self.scale_a_ * z + self.bias_b_
                probs = torch.sigmoid(logits).cpu().numpy()
                out_probs.append(probs)

        return np.concatenate(out_probs).astype(np.float64)

    def describe(self) -> Dict[str, Any]:
        return {
            "family": "qml",
            "model_name": "PennyLane Variational Quantum Classifier (VQC)",
            "backend": "PennyLane default.qubit simulator (classical simulation on CPU; no quantum hardware)",
            "seed": self.seed,
            "feature_set": self.feature_cols,
            "n_features": len(self.feature_cols),
            "n_qubits": self.encoder_.n_features() if self.encoder_ else 8,
            "n_trainable_parameters": int(self.weights_.numel() + 2) if self.weights_ is not None else 50,
            "circuit_diagram": self.diagram_,
            "hyperparameters": {
                "ansatz": "StronglyEntanglingLayers",
                "embedding": "AngleEmbedding (RY rotation, [0, pi])",
                "n_layers": self.n_layers,
                "learning_rate": self.lr,
                "epochs": self.epochs,
                "batch_size": self.batch_size,
                "subsample_size": self.subsample_n,
                "classical_readout": "logit = a * <Z0> + b",
                "shots": "analytic (None)",
            },
            "history": self.history_,
            "library_versions": {
                "python": sys.version.split()[0],
                "pennylane": qml.__version__,
                "torch": torch.__version__,
                "numpy": np.__version__,
                "pandas": pd.__version__,
            },
            "limitations": [
                "Simulated locally on CPU with PennyLane default.qubit; does NOT execute on quantum hardware.",
                "No quantum speedup or quantum advantage claimed; pedagogical benchmark comparison only.",
                "Subsampled training set used to fit within academic demonstration execution budgets.",
            ],
        }
