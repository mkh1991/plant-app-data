"""Training loop for both sklearn and MLP probes."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from data.dataset import EmbeddingDataset
from embeddings.cache import EmbeddingCache
from train.probe import (
    MLPProbe,
    load_sklearn_probe,
    save_mlp_probe,
    train_sklearn_probe,
)

logger = logging.getLogger(__name__)


def _load_split_embeddings(
    df: pd.DataFrame,
    split: str,
    cache: EmbeddingCache,
    species_to_idx: dict[str, int],
) -> tuple[np.ndarray, np.ndarray]:
    split_df = df[df["split"] == split]
    paths = split_df["image_path"].tolist()
    embs, found_paths = cache.load_split(paths)
    found_set = set(found_paths)
    labels = np.array([
        species_to_idx[r["species_name"]]
        for _, r in split_df.iterrows()
        if r["image_path"] in found_set
    ], dtype=np.int64)
    return embs, labels


def train(
    splits_csv: Path,
    cache_path: Path,
    probe_cfg: dict,
    device: str = "cpu",
) -> None:
    df = pd.read_csv(splits_csv)
    species_list = sorted(df["species_name"].unique().tolist())
    species_to_idx = {s: i for i, s in enumerate(species_list)}
    num_classes = len(species_list)

    cache = EmbeddingCache(cache_path)

    logger.info("Loading train embeddings...")
    X_train, y_train = _load_split_embeddings(df, "train", cache, species_to_idx)
    logger.info("Loading val embeddings...")
    X_val, y_val = _load_split_embeddings(df, "val", cache, species_to_idx)
    logger.info(
        "Train: %d samples | Val: %d samples | Classes: %d",
        len(X_train), len(X_val), num_classes,
    )

    probe_type = probe_cfg["type"]

    if probe_type == "sklearn":
        sk_cfg = probe_cfg["sklearn"]
        train_sklearn_probe(
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            C_values=sk_cfg["C_values"],
            max_iter=sk_cfg.get("max_iter", 1000),
            solver=sk_cfg.get("solver", "lbfgs"),
            model_path=Path(sk_cfg["model_path"]),
        )

    elif probe_type == "mlp":
        mlp_cfg = probe_cfg["mlp"]
        _train_mlp(
            X_train, y_train, X_val, y_val,
            num_classes=num_classes,
            hidden_dim=mlp_cfg["hidden_dim"],
            dropout=mlp_cfg["dropout"],
            lr=mlp_cfg["lr"],
            weight_decay=mlp_cfg.get("weight_decay", 1e-4),
            epochs=mlp_cfg["epochs"],
            patience=mlp_cfg["patience"],
            batch_size=mlp_cfg["batch_size"],
            model_path=Path(mlp_cfg["model_path"]),
            device=device,
        )
    else:
        raise ValueError(f"Unknown probe type: {probe_type}")


def _top1_accuracy(logits: torch.Tensor, labels: torch.Tensor) -> float:
    preds = logits.argmax(dim=1)
    return (preds == labels).float().mean().item()


def _train_mlp(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    num_classes: int,
    hidden_dim: int,
    dropout: float,
    lr: float,
    weight_decay: float,
    epochs: int,
    patience: int,
    batch_size: int,
    model_path: Path,
    device: str,
) -> MLPProbe:
    input_dim = X_train.shape[1]
    model = MLPProbe(input_dim, hidden_dim, num_classes, dropout).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    criterion = torch.nn.CrossEntropyLoss()

    train_ds = EmbeddingDataset(X_train, y_train)
    val_ds = EmbeddingDataset(X_val, y_val)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size * 4, shuffle=False)

    best_val_acc = -1.0
    patience_counter = 0
    best_state = None

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for embs, labels in tqdm(train_loader, desc=f"Epoch {epoch}/{epochs}", leave=False):
            embs, labels = embs.to(device), labels.to(device)
            optimizer.zero_grad()
            logits = model(embs)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * len(labels)

        train_loss /= len(train_ds)

        model.eval()
        val_acc_sum = 0.0
        with torch.no_grad():
            for embs, labels in val_loader:
                embs, labels = embs.to(device), labels.to(device)
                logits = model(embs)
                val_acc_sum += _top1_accuracy(logits, labels) * len(labels)
        val_acc = val_acc_sum / len(val_ds)

        logger.info("Epoch %d | loss %.4f | val_acc %.4f", epoch, train_loss, val_acc)

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            save_mlp_probe(model, model_path)
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info("Early stopping at epoch %d (best val acc %.4f)", epoch, best_val_acc)
                break

    if best_state is not None:
        model.load_state_dict(best_state)
    return model


if __name__ == "__main__":
    import argparse
    import yaml

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Train linear probe on BioCLIP embeddings")
    parser.add_argument("--config", default="configs/default.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    train(
        splits_csv=Path(cfg["data"]["splits_csv"]),
        cache_path=Path(cfg["embeddings"]["cache_path"]),
        probe_cfg=cfg["probe"],
        device=cfg["model"]["device"],
    )
