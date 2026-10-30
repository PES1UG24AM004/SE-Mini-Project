"""Deep Learning adapter using PyTorch MLP."""
import sys
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from backend.data.preprocessor import make_standard_preprocessor
from backend.models.base import ModelAdapter


class MLPModule(nn.Module):
    """Feed-forward multi-layer perceptron for binary classification."""
    def __init__(self, in_dim: int, hidden: List[int], dropout: float):
        super().__init__()
        layers: List[nn.Module] = []
        d = in_dim
        for h in hidden:
            layers.append(nn.Linear(d, h))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            d = h
        layers.append(nn.Linear(d, 1))  # Output logit
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


class DLAdapter(ModelAdapter):
    """PyTorch MLP model adapter with validation early stopping."""

    def __init__(
        self,
        feature_cols: List[str],
        numeric_cols: List[str],
        categorical_cols: List[str],
        seed: int = 42,
        hidden: Optional[List[int]] = None,
        dropout: float = 0.3,
        lr: float = 0.001,
        weight_decay: float = 1e-4,
        batch_size: int = 128,
        max_epochs: int = 100,
        patience: int = 10,
        device: Optional[str] = None,
        val_data: Optional[Tuple[pd.DataFrame, np.ndarray]] = None,
    ):
        self.feature_cols = list(feature_cols)
        self.numeric_cols = [c for c in self.feature_cols if c in numeric_cols]
        self.categorical_cols = [c for c in self.feature_cols if c in categorical_cols]
        self.seed = int(seed)
        self.hidden = hidden or [64, 32]
        self.dropout = dropout
        self.lr = lr
        self.weight_decay = weight_decay
        self.batch_size = batch_size
        self.max_epochs = max_epochs
        self.patience = patience
        self.val_data = val_data

        self.device = torch.device(device if device else ("cuda" if torch.cuda.is_available() else "cpu"))
        self.preprocessor_: Optional[Any] = None
        self.model_: Optional[MLPModule] = None
        self.history_: Dict[str, Any] = {}

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "DLAdapter":
        """Fits preprocessing and trains the MLP with early stopping on validation loss."""
        # 1. Reproducibility seed setup
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)

        # 2. Fit standard preprocessor on train only
        X_sub = X[self.feature_cols]
        self.preprocessor_ = make_standard_preprocessor(self.numeric_cols, self.categorical_cols).fit(X_sub)
        Z_tr = self.preprocessor_.transform(X_sub)

        in_dim = Z_tr.shape[1]
        self.model_ = MLPModule(in_dim, self.hidden, self.dropout).to(self.device)

        # 3. Class balance weighting
        n_pos = int(np.sum(y))
        n_neg = int(len(y) - n_pos)
        pos_weight = float(n_neg / max(n_pos, 1))

        loss_fn = nn.BCEWithLogitsLoss(
            pos_weight=torch.tensor([pos_weight], dtype=torch.float32, device=self.device)
        )
        optimizer = torch.optim.Adam(
            self.model_.parameters(), lr=self.lr, weight_decay=self.weight_decay
        )

        Xt = torch.from_numpy(np.ascontiguousarray(Z_tr, dtype=np.float32)).to(self.device)
        yt = torch.from_numpy(np.asarray(y, dtype=np.float32)).to(self.device)

        # Validation set for early stopping (if provided)
        has_val = self.val_data is not None
        if has_val:
            X_val, y_val = self.val_data
            Z_va = self.preprocessor_.transform(X_val[self.feature_cols])
            Xv = torch.from_numpy(np.ascontiguousarray(Z_va, dtype=np.float32)).to(self.device)
            yv = torch.from_numpy(np.asarray(y_val, dtype=np.float32)).to(self.device)

        gen = torch.Generator()
        gen.manual_seed(self.seed)

        best_loss = float("inf")
        best_epoch = -1
        best_state = None
        bad_epochs = 0
        train_hist: List[float] = []
        val_hist: List[float] = []

        for epoch in range(self.max_epochs):
            self.model_.train()
            perm = torch.randperm(len(Xt), generator=gen)
            running_loss = 0.0
            cnt = 0

            for i in range(0, len(perm), self.batch_size):
                idx = perm[i : i + self.batch_size]
                optimizer.zero_grad()
                logits = self.model_(Xt[idx])
                loss = loss_fn(logits, yt[idx])
                loss.backward()
                optimizer.step()
                running_loss += float(loss.item()) * len(idx)
                cnt += len(idx)

            ep_tr_loss = running_loss / max(cnt, 1)
            train_hist.append(ep_tr_loss)

            if has_val:
                self.model_.eval()
                with torch.no_grad():
                    val_loss = float(loss_fn(self.model_(Xv), yv).item())
                val_hist.append(val_loss)

                if val_loss < best_loss:
                    best_loss = val_loss
                    best_epoch = epoch
                    bad_epochs = 0
                    best_state = {k: v.detach().clone() for k, v in self.model_.state_dict().items()}
                else:
                    bad_epochs += 1
                    if bad_epochs >= self.patience:
                        break
            else:
                best_epoch = epoch
                best_state = {k: v.detach().clone() for k, v in self.model_.state_dict().items()}

        if best_state is not None:
            self.model_.load_state_dict(best_state)
        self.model_.eval()

        self.history_ = {
            "train_loss": train_hist,
            "val_loss": val_hist,
            "best_epoch": best_epoch + 1,
            "epochs_run": len(train_hist),
            "stopped_early": len(train_hist) < self.max_epochs,
            "pos_weight": pos_weight,
        }
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Transforms input using fitted preprocessor and returns positive class probability."""
        if self.preprocessor_ is None or self.model_ is None:
            raise RuntimeError("DLAdapter must be fitted before predict_proba.")
        X_sub = X[self.feature_cols]
        Z = self.preprocessor_.transform(X_sub)
        self.model_.eval()
        with torch.no_grad():
            tensor_x = torch.from_numpy(np.ascontiguousarray(Z, dtype=np.float32)).to(self.device)
            logits = self.model_(tensor_x)
            probs = torch.sigmoid(logits).cpu().numpy().astype(np.float64)
        return probs.reshape(-1)

    def describe(self) -> Dict[str, Any]:
        return {
            "family": "dl",
            "model_name": "PyTorch Feed-Forward MLP",
            "backend": f"PyTorch on {self.device.type.upper()}",
            "seed": self.seed,
            "feature_set": self.feature_cols,
            "n_features": len(self.feature_cols),
            "n_transformed_features": len(self.preprocessor_.get_feature_names_out()) if self.preprocessor_ else 8,
            "hyperparameters": {
                "hidden_layers": self.hidden,
                "dropout": self.dropout,
                "lr": self.lr,
                "weight_decay": self.weight_decay,
                "batch_size": self.batch_size,
                "max_epochs": self.max_epochs,
                "patience": self.patience,
                "loss": "BCEWithLogitsLoss with positive weighting",
                "optimizer": "Adam",
                "early_stopping": "patience 10 on validation loss; best weights restored",
            },
            "history": self.history_,
            "library_versions": {
                "python": sys.version.split()[0],
                "torch": torch.__version__,
                "numpy": np.__version__,
                "pandas": pd.__version__,
            },
            "limitations": [
                "Small sample size relative to parameter space; regularized with dropout and weight decay.",
                "Non-convex optimization introduces seed variation across random initializations.",
                "Clinical utility requires external cohort calibration.",
            ],
        }
