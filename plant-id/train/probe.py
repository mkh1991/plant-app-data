"""Linear probe definitions: sklearn LogisticRegression and PyTorch MLP."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import torch
import torch.nn as nn
from sklearn.linear_model import LogisticRegression


# ---------------------------------------------------------------------------
# sklearn probe
# ---------------------------------------------------------------------------

def train_sklearn_probe(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    C_values: list[float],
    max_iter: int,
    solver: str,
    model_path: Path,
) -> LogisticRegression:
    """Grid-search over C on val set, save best model."""
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)

    best_acc = -1.0
    best_model: Optional[LogisticRegression] = None

    for C in C_values:
        lr = LogisticRegression(
            C=C,
            max_iter=max_iter,
            solver=solver,
            multi_class="multinomial",
            n_jobs=-1,
            random_state=42,
        )
        lr.fit(X_train, y_train)
        val_acc = (lr.predict(X_val) == y_val).mean()
        print(f"  C={C:.4f} → val acc {val_acc:.4f}")
        if val_acc > best_acc:
            best_acc = val_acc
            best_model = lr

    print(f"Best val acc: {best_acc:.4f}")
    joblib.dump(best_model, model_path)
    print(f"Saved sklearn probe to {model_path}")
    return best_model  # type: ignore[return-value]


def load_sklearn_probe(model_path: Path) -> LogisticRegression:
    return joblib.load(model_path)


# ---------------------------------------------------------------------------
# MLP probe
# ---------------------------------------------------------------------------

class MLPProbe(nn.Module):
    """Two-layer MLP head over frozen BioCLIP embeddings."""

    def __init__(self, input_dim: int, hidden_dim: int, num_classes: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def save_mlp_probe(model: MLPProbe, model_path: Path) -> None:
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), model_path)


def load_mlp_probe(
    model_path: Path,
    input_dim: int,
    hidden_dim: int,
    num_classes: int,
    dropout: float,
    device: str = "cpu",
) -> MLPProbe:
    model = MLPProbe(input_dim, hidden_dim, num_classes, dropout)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    return model
