"""Run evaluation on the held-out test split and output results."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from embeddings.cache import EmbeddingCache, load_text_embeddings
from eval.metrics import (
    confusion_pairs,
    genus_accuracy,
    macro_top_k_accuracy,
    per_species_top1_accuracy,
)

logger = logging.getLogger(__name__)


def _load_test_embeddings(
    df: pd.DataFrame,
    cache: EmbeddingCache,
    species_to_idx: dict[str, int],
) -> tuple[np.ndarray, np.ndarray]:
    test_df = df[df["split"] == "test"]
    paths = test_df["image_path"].tolist()
    embs, found_paths = cache.load_split(paths)
    found_set = set(found_paths)
    labels = np.array([
        species_to_idx[r["species_name"]]
        for _, r in test_df.iterrows()
        if r["image_path"] in found_set
    ], dtype=np.int64)
    return embs, labels


def _probe_scores(
    X_test: np.ndarray,
    probe_cfg: dict,
) -> np.ndarray:
    """Return score matrix (N, num_classes) from the trained probe."""
    probe_type = probe_cfg["type"]
    if probe_type == "sklearn":
        from train.probe import load_sklearn_probe
        model = load_sklearn_probe(Path(probe_cfg["sklearn"]["model_path"]))
        return model.predict_proba(X_test)
    elif probe_type == "mlp":
        import torch
        from train.probe import load_mlp_probe
        mlp_cfg = probe_cfg["mlp"]
        model = load_mlp_probe(
            Path(mlp_cfg["model_path"]),
            input_dim=X_test.shape[1],
            hidden_dim=mlp_cfg["hidden_dim"],
            num_classes=int(probe_cfg["_num_classes"]),
            dropout=mlp_cfg["dropout"],
        )
        model.eval()
        with torch.no_grad():
            logits = model(torch.tensor(X_test, dtype=torch.float32))
        return logits.numpy()
    else:
        raise ValueError(f"Unknown probe type: {probe_type}")


def _zero_shot_scores(
    X_test: np.ndarray,
    text_embs: np.ndarray,
    species_index: dict[str, int],
    idx_to_species: dict[int, str],
    num_classes: int,
) -> np.ndarray:
    """Cosine similarity between image embeddings and text embeddings."""
    # Text embs rows may not align with label indices if order differs
    text_matrix = np.zeros((num_classes, text_embs.shape[1]), dtype=np.float32)
    for name, tidx in species_index.items():
        lidx = next((i for i, s in idx_to_species.items() if s == name), None)
        if lidx is not None:
            text_matrix[lidx] = text_embs[tidx]
    # X_test already L2-normalised, text_matrix rows normalised at extraction
    return X_test @ text_matrix.T  # (N, num_classes)


def _compute_metrics(
    scores: np.ndarray,
    labels: np.ndarray,
    idx_to_species: dict[int, str],
    num_classes: int,
    top_n_confusion: int,
    label: str,
) -> dict:
    top1 = macro_top_k_accuracy(scores, labels, 1, num_classes)
    top3 = macro_top_k_accuracy(scores, labels, 3, num_classes)
    top5 = macro_top_k_accuracy(scores, labels, 5, num_classes)
    per_sp = per_species_top1_accuracy(scores, labels, idx_to_species)
    g_acc = genus_accuracy(scores, labels, idx_to_species)
    confusions = confusion_pairs(scores, labels, idx_to_species, top_n_confusion)

    print(f"\n{'='*50}")
    print(f"  {label}")
    print(f"{'='*50}")
    print(f"  Macro Top-1 accuracy : {top1:.4f}")
    print(f"  Macro Top-3 accuracy : {top3:.4f}")
    print(f"  Macro Top-5 accuracy : {top5:.4f}")
    print(f"  Genus-level accuracy : {g_acc:.4f}")
    print(f"\n  Worst-performing species (Top-1):")
    for name, acc in list(per_sp.items())[:10]:
        print(f"    {name:<45} {acc:.4f}")

    return {
        "label": label,
        "macro_top1": top1,
        "macro_top3": top3,
        "macro_top5": top5,
        "genus_accuracy": g_acc,
        "per_species_top1": per_sp,
        "confusion_pairs": confusions,
    }


def evaluate(
    splits_csv: Path,
    cache_path: Path,
    text_emb_path: Path,
    species_index_path: Path,
    probe_cfg: dict,
    output_path: Path,
    top_n_confusion: int = 20,
) -> dict:
    df = pd.read_csv(splits_csv)
    species_list = sorted(df["species_name"].unique().tolist())
    species_to_idx = {s: i for i, s in enumerate(species_list)}
    idx_to_species = {i: s for s, i in species_to_idx.items()}
    num_classes = len(species_list)

    # Patch num_classes into MLP config for loading
    probe_cfg = dict(probe_cfg)
    probe_cfg["_num_classes"] = num_classes

    cache = EmbeddingCache(cache_path)
    logger.info("Loading test embeddings...")
    X_test, y_test = _load_test_embeddings(df, cache, species_to_idx)
    logger.info("Test set: %d samples", len(X_test))

    # Probe evaluation
    logger.info("Running probe inference...")
    probe_scores = _probe_scores(X_test, probe_cfg)
    probe_results = _compute_metrics(
        probe_scores, y_test, idx_to_species, num_classes, top_n_confusion, label="Linear Probe"
    )

    # Zero-shot evaluation
    logger.info("Running zero-shot inference...")
    text_embs, species_index = load_text_embeddings(text_emb_path, species_index_path)
    zs_scores = _zero_shot_scores(X_test, text_embs, species_index, idx_to_species, num_classes)
    zs_results = _compute_metrics(
        zs_scores, y_test, idx_to_species, num_classes, top_n_confusion, label="Zero-Shot Baseline"
    )

    output = {
        "num_test_samples": int(len(X_test)),
        "num_classes": num_classes,
        "probe": probe_results,
        "zero_shot": zs_results,
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    logger.info("Saved results to %s", output_path)
    return output


if __name__ == "__main__":
    import argparse
    import yaml

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Evaluate plant species classifier")
    parser.add_argument("--config", default="configs/default.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    evaluate(
        splits_csv=Path(cfg["data"]["splits_csv"]),
        cache_path=Path(cfg["embeddings"]["cache_path"]),
        text_emb_path=Path(cfg["embeddings"]["text_embeddings_path"]),
        species_index_path=Path(cfg["embeddings"]["species_index_path"]),
        probe_cfg=cfg["probe"],
        output_path=Path(cfg["eval"]["output_path"]),
        top_n_confusion=cfg["eval"].get("confusion_matrix_top_n", 20),
    )
