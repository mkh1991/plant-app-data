"""Inference: load probe + text embeddings, classify a single image."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Union

import numpy as np
import torch
from PIL import Image

logger = logging.getLogger(__name__)


def _l2_normalize(x: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(x)
    return x / norm if norm > 0 else x


def _load_bioclip(hub_id: str, device: str):
    import open_clip
    model, _, preprocess = open_clip.create_model_and_transforms(hub_id)
    model = model.to(device)
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    return model, preprocess


def embed_image(image_path: Union[str, Path], model, preprocess, device: str) -> np.ndarray:
    img = Image.open(image_path).convert("RGB")
    tensor = preprocess(img).unsqueeze(0).to(device)
    with torch.no_grad():
        emb = model.encode_image(tensor).cpu().numpy()[0]
    return _l2_normalize(emb.astype(np.float32))


def _probe_scores_from_emb(
    emb: np.ndarray,
    probe_cfg: dict,
    species_list: list[str],
) -> np.ndarray:
    probe_type = probe_cfg["type"]
    if probe_type == "sklearn":
        from train.probe import load_sklearn_probe
        model = load_sklearn_probe(Path(probe_cfg["sklearn"]["model_path"]))
        return model.predict_proba(emb[None])[0]
    elif probe_type == "mlp":
        from train.probe import load_mlp_probe
        mlp_cfg = probe_cfg["mlp"]
        model = load_mlp_probe(
            Path(mlp_cfg["model_path"]),
            input_dim=emb.shape[0],
            hidden_dim=mlp_cfg["hidden_dim"],
            num_classes=len(species_list),
            dropout=mlp_cfg["dropout"],
        )
        with torch.no_grad():
            logits = model(torch.tensor(emb[None], dtype=torch.float32))[0]
        scores = torch.softmax(logits, dim=0).numpy()
        return scores
    else:
        raise ValueError(f"Unknown probe type: {probe_type}")


def predict(
    image_path: Union[str, Path],
    cfg: dict,
    top_k: int = 5,
) -> list[dict]:
    """
    Returns a list of top_k dicts: [{"species": str, "score": float}, ...],
    sorted descending by score.
    """
    device = cfg["model"]["device"]
    hub_id = cfg["model"]["bioclip_hub"]

    # Load species list from splits CSV or species index
    index_path = Path(cfg["embeddings"]["species_index_path"])
    with open(index_path) as f:
        species_index: dict[str, int] = json.load(f)
    species_list = [k for k, _ in sorted(species_index.items(), key=lambda x: x[1])]

    logger.info("Loading BioCLIP model...")
    model, preprocess = _load_bioclip(hub_id, device)

    logger.info("Embedding image: %s", image_path)
    emb = embed_image(image_path, model, preprocess, device)

    scores = _probe_scores_from_emb(emb, cfg["probe"], species_list)

    top_k_indices = np.argsort(scores)[::-1][:top_k]
    results = [
        {"species": species_list[i], "score": float(scores[i])}
        for i in top_k_indices
    ]
    return results


if __name__ == "__main__":
    import sys
    import yaml

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # Allow running from project root or serve/ directory
    for candidate in ["configs/default.yaml", "../configs/default.yaml"]:
        if Path(candidate).exists():
            default_config = candidate
            break
    else:
        default_config = "configs/default.yaml"

    parser = argparse.ArgumentParser(description="Predict plant species from an image")
    parser.add_argument("--image", required=True, help="Path to the input image")
    parser.add_argument("--top_k", type=int, default=5, help="Number of top predictions")
    parser.add_argument("--config", default=default_config)
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    predictions = predict(args.image, cfg, top_k=args.top_k)

    print(f"\nTop-{args.top_k} predictions for: {args.image}")
    print("-" * 55)
    for rank, p in enumerate(predictions, 1):
        print(f"  {rank}. {p['species']:<45} {p['score']:.4f}")
