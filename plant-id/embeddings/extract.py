"""Extract BioCLIP vision embeddings and text embeddings, cache to disk."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import open_clip
import torch
from PIL import Image
from tqdm import tqdm

from embeddings.cache import EmbeddingCache, save_text_embeddings

logger = logging.getLogger(__name__)


def _load_model(hub_id: str, device: str) -> tuple:
    """Load BioCLIP model and preprocessing transform."""
    logger.info("Loading BioCLIP from %s on %s", hub_id, device)
    model, _, preprocess = open_clip.create_model_and_transforms(hub_id)
    model = model.to(device)
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    tokenizer = open_clip.get_tokenizer(hub_id)
    return model, preprocess, tokenizer


def _l2_normalize(x: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(x, axis=-1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return x / norms


def extract_image_embeddings(
    image_paths: list[str],
    cache: EmbeddingCache,
    model,
    preprocess,
    device: str,
    batch_size: int = 64,
) -> None:
    """Extract and cache image embeddings, skipping already-cached paths."""
    to_process = [p for p in image_paths if p not in cache]
    if not to_process:
        logger.info("All %d images already cached.", len(image_paths))
        return

    logger.info("Extracting embeddings for %d / %d images", len(to_process), len(image_paths))

    for start in tqdm(range(0, len(to_process), batch_size), desc="Embedding batches"):
        batch_paths = to_process[start : start + batch_size]
        imgs: list[torch.Tensor] = []
        valid_paths: list[str] = []

        for p in batch_paths:
            try:
                img = Image.open(p).convert("RGB")
                imgs.append(preprocess(img))
                valid_paths.append(p)
            except Exception as exc:
                logger.warning("Skipping %s: %s", p, exc)

        if not imgs:
            continue

        batch_tensor = torch.stack(imgs).to(device)
        with torch.no_grad():
            embs = model.encode_image(batch_tensor).cpu().numpy().astype(np.float32)

        embs = _l2_normalize(embs)
        cache.put_batch(list(zip(valid_paths, embs)))


def _text_prompts(scientific_name: str) -> list[str]:
    return [
        f"a photo of {scientific_name}",
        f"a photo of {scientific_name}, a plant",
        scientific_name,
    ]


def extract_text_embeddings(
    species_list: list[str],
    model,
    tokenizer,
    device: str,
    emb_path: Path,
    index_path: Path,
    batch_size: int = 64,
) -> tuple[np.ndarray, dict[str, int]]:
    """Compute averaged text embeddings for each species, save to disk."""
    logger.info("Extracting text embeddings for %d species", len(species_list))

    all_embeddings: list[np.ndarray] = []

    for start in tqdm(range(0, len(species_list), batch_size), desc="Text embeddings"):
        batch_species = species_list[start : start + batch_size]
        # Stack 3 prompts per species
        prompts = [p for s in batch_species for p in _text_prompts(s)]
        tokens = tokenizer(prompts).to(device)
        with torch.no_grad():
            embs = model.encode_text(tokens).cpu().numpy().astype(np.float32)
        # Reshape to (batch, 3, dim) and average
        embs = embs.reshape(len(batch_species), 3, -1).mean(axis=1)
        embs = _l2_normalize(embs)
        all_embeddings.append(embs)

    text_embs = np.concatenate(all_embeddings, axis=0)  # (num_species, dim)
    save_text_embeddings(text_embs, species_list, emb_path, index_path)
    logger.info("Saved text embeddings to %s", emb_path)

    species_index = {name: i for i, name in enumerate(species_list)}
    return text_embs, species_index


def run_extraction(
    splits_csv: Path,
    cache_path: Path,
    text_emb_path: Path,
    species_index_path: Path,
    hub_id: str,
    device: str,
    batch_size: int = 64,
) -> None:
    import pandas as pd

    df = pd.read_csv(splits_csv)
    image_paths = df["image_path"].tolist()
    species_list = sorted(df["species_name"].unique().tolist())

    model, preprocess, tokenizer = _load_model(hub_id, device)
    cache = EmbeddingCache(cache_path)

    extract_image_embeddings(image_paths, cache, model, preprocess, device, batch_size)
    extract_text_embeddings(
        species_list, model, tokenizer, device, text_emb_path, species_index_path, batch_size
    )


if __name__ == "__main__":
    import argparse
    import yaml

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Extract BioCLIP embeddings")
    parser.add_argument("--config", default="configs/default.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    run_extraction(
        splits_csv=Path(cfg["data"]["splits_csv"]),
        cache_path=Path(cfg["embeddings"]["cache_path"]),
        text_emb_path=Path(cfg["embeddings"]["text_embeddings_path"]),
        species_index_path=Path(cfg["embeddings"]["species_index_path"]),
        hub_id=cfg["model"]["bioclip_hub"],
        device=cfg["model"]["device"],
        batch_size=cfg["embeddings"]["batch_size"],
    )
