"""Evaluation metrics: macro top-k accuracy, per-species accuracy, genus accuracy."""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

import numpy as np


def top_k_correct(scores: np.ndarray, labels: np.ndarray, k: int) -> np.ndarray:
    """Return boolean array of shape (N,): True if correct class is in top-k."""
    top_k_preds = np.argsort(scores, axis=1)[:, -k:]  # (N, k)
    return np.any(top_k_preds == labels[:, None], axis=1)


def macro_top_k_accuracy(
    scores: np.ndarray,
    labels: np.ndarray,
    k: int,
    num_classes: Optional[int] = None,
) -> float:
    """Mean per-species top-k accuracy (macro average)."""
    if num_classes is None:
        num_classes = int(scores.shape[1])
    correct = top_k_correct(scores, labels, k)
    per_class: dict[int, list[bool]] = defaultdict(list)
    for i, label in enumerate(labels):
        per_class[int(label)].append(bool(correct[i]))
    class_accs = [np.mean(per_class[c]) for c in range(num_classes) if c in per_class]
    return float(np.mean(class_accs)) if class_accs else 0.0


def per_species_top1_accuracy(
    scores: np.ndarray,
    labels: np.ndarray,
    idx_to_species: dict[int, str],
) -> dict[str, float]:
    """Return dict mapping species name → top-1 accuracy, sorted ascending."""
    preds = np.argmax(scores, axis=1)
    per_class: dict[int, list[bool]] = defaultdict(list)
    for pred, label in zip(preds, labels):
        per_class[int(label)].append(int(pred) == int(label))

    result = {
        idx_to_species[cls]: float(np.mean(hits))
        for cls, hits in per_class.items()
        if cls in idx_to_species
    }
    return dict(sorted(result.items(), key=lambda x: x[1]))


def genus_accuracy(
    scores: np.ndarray,
    labels: np.ndarray,
    idx_to_species: dict[int, str],
) -> float:
    """Collapse predictions to genus level, return macro top-1 accuracy."""
    def _genus(name: str) -> str:
        return name.split()[0]

    preds = np.argmax(scores, axis=1)
    per_genus: dict[str, list[bool]] = defaultdict(list)
    for pred, label in zip(preds, labels):
        true_genus = _genus(idx_to_species.get(int(label), "Unknown"))
        pred_genus = _genus(idx_to_species.get(int(pred), "Unknown"))
        per_genus[true_genus].append(pred_genus == true_genus)

    genus_accs = [float(np.mean(hits)) for hits in per_genus.values()]
    return float(np.mean(genus_accs)) if genus_accs else 0.0


def confusion_pairs(
    scores: np.ndarray,
    labels: np.ndarray,
    idx_to_species: dict[int, str],
    top_n: int = 20,
) -> list[dict]:
    """Return the top_n most common (true_species, predicted_species) confusion pairs."""
    preds = np.argmax(scores, axis=1)
    pair_counts: dict[tuple[str, str], int] = defaultdict(int)
    for pred, label in zip(preds, labels):
        if int(pred) != int(label):
            true_name = idx_to_species.get(int(label), str(label))
            pred_name = idx_to_species.get(int(pred), str(pred))
            pair_counts[(true_name, pred_name)] += 1

    sorted_pairs = sorted(pair_counts.items(), key=lambda x: -x[1])[:top_n]
    return [
        {"true": t, "predicted": p, "count": c}
        for (t, p), c in sorted_pairs
    ]
