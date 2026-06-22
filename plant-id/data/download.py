"""Download plant images from GBIF (iNaturalist subset)."""

from __future__ import annotations

import csv
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

import pandas as pd
import requests
from pygbif import occurrences as occ
from tqdm import tqdm

logger = logging.getLogger(__name__)

INATURALIST_DATASET_KEY = "50c9509d-22c7-4a22-a47d-8c48425ef4a7"
ALLOWED_LICENSES = {"CC_BY_4_0", "CC0"}
IMAGE_TIMEOUT = 15  # seconds


def _gbif_occurrences(
    taxon_key: int,
    limit: int,
    offset: int = 0,
) -> dict:
    return occ.search(
        taxonKey=taxon_key,
        datasetKey=INATURALIST_DATASET_KEY,
        mediaType="StillImage",
        occurrenceStatus="PRESENT",
        limit=limit,
        offset=offset,
    )


def _iter_occurrence_pages(taxon_key: int, max_records: int, delay: float) -> Iterator[dict]:
    """Yield individual occurrence dicts up to max_records."""
    page_size = min(300, max_records)
    offset = 0
    fetched = 0

    while fetched < max_records:
        try:
            result = _gbif_occurrences(taxon_key, page_size, offset)
        except Exception as exc:
            logger.warning("GBIF API error (taxon %s, offset %s): %s", taxon_key, offset, exc)
            break

        records = result.get("results", [])
        if not records:
            break

        for rec in records:
            if fetched >= max_records:
                return
            # Filter by license
            license_str = (rec.get("license") or "").replace("http://creativecommons.org/", "")
            license_str = license_str.replace("publicdomain/", "CC0").upper()
            license_str = license_str.replace("LICENSES/", "").replace("/4.0/", "_4_0").strip("/")
            if not any(lic in license_str for lic in ALLOWED_LICENSES):
                continue

            media_list = rec.get("media", [])
            image_urls = [
                m.get("identifier")
                for m in media_list
                if m.get("type") == "StillImage" and m.get("identifier")
            ]
            if not image_urls:
                continue

            yield {
                "occurrence_id": str(rec.get("key", "")),
                "image_urls": image_urls,
                "species_name": rec.get("species", ""),
            }
            fetched += 1

        if result.get("endOfRecords", True):
            break
        offset += len(records)
        time.sleep(delay)


def _download_image(url: str, dest_path: Path) -> bool:
    """Download a single image, return True on success."""
    if dest_path.exists():
        return True
    try:
        resp = requests.get(url, timeout=IMAGE_TIMEOUT, stream=True)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "image" not in content_type and "jpeg" not in content_type:
            logger.debug("Non-image content-type %s for %s", content_type, url)
            return False
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as exc:
        logger.debug("Failed to download %s: %s", url, exc)
        return False


def download_species(
    species_name: str,
    taxon_key: int,
    image_dir: Path,
    max_images: int,
    delay: float,
    workers: int,
) -> list[dict]:
    """Download up to max_images for a species, returns list of metadata dicts."""
    safe_name = species_name.replace(" ", "_").replace("/", "_")
    species_dir = image_dir / safe_name
    species_dir.mkdir(parents=True, exist_ok=True)

    # Collect occurrence -> image url mappings (one image per observation to spread diversity)
    tasks: list[tuple[str, str, Path]] = []
    seen_obs: set[str] = set()

    for rec in _iter_occurrence_pages(taxon_key, max_images * 3, delay):
        obs_id = rec["occurrence_id"]
        if obs_id in seen_obs:
            continue
        seen_obs.add(obs_id)
        for n, url in enumerate(rec["image_urls"]):
            # Use safe filename derived from URL extension
            ext = Path(urlparse(url).path).suffix.lower() or ".jpg"
            if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
                ext = ".jpg"
            fname = f"{obs_id}_{n}{ext}"
            dest = species_dir / fname
            tasks.append((obs_id, url, dest))
        if len(tasks) >= max_images * 2:
            break

    results: list[dict] = []
    downloaded = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {
            pool.submit(_download_image, url, dest): (obs_id, dest)
            for obs_id, url, dest in tasks
            if downloaded < max_images
        }
        for future in as_completed(future_map):
            obs_id, dest = future_map[future]
            try:
                ok = future.result()
            except Exception as exc:
                logger.warning("Download error for obs %s: %s", obs_id, exc)
                ok = False
            if ok:
                results.append({
                    "image_path": str(dest),
                    "species_name": species_name,
                    "observation_id": obs_id,
                })
                downloaded += 1
            if downloaded >= max_images:
                break

    return results[:max_images]


def download_all(
    species_csv: Path,
    image_dir: Path,
    splits_csv: Path,
    max_images_per_species: int = 200,
    delay: float = 0.5,
    workers: int = 4,
) -> None:
    """Download images for all species listed in species_csv."""
    species_df = pd.read_csv(species_csv)
    required_cols = {"species_name", "gbif_taxon_key"}
    if not required_cols.issubset(set(species_df.columns)):
        raise ValueError(f"species_csv must have columns: {required_cols}")

    image_dir = Path(image_dir)
    splits_csv = Path(splits_csv)
    splits_csv.parent.mkdir(parents=True, exist_ok=True)

    all_records: list[dict] = []

    for _, row in tqdm(species_df.iterrows(), total=len(species_df), desc="Species"):
        name = row["species_name"]
        key = int(row["gbif_taxon_key"])
        logger.info("Downloading %s (taxon %s)", name, key)
        records = download_species(name, key, image_dir, max_images_per_species, delay, workers)
        logger.info("  Got %d images for %s", len(records), name)
        all_records.extend(records)

    # Write raw image manifest (splits assigned later)
    df = pd.DataFrame(all_records)
    df["split"] = ""
    df.to_csv(splits_csv, index=False)
    logger.info("Saved manifest with %d images to %s", len(df), splits_csv)


if __name__ == "__main__":
    import argparse
    import yaml

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Download GBIF plant images")
    parser.add_argument("--config", default="configs/default.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    download_all(
        species_csv=Path(cfg["data"]["species_csv"]),
        image_dir=Path(cfg["data"]["image_dir"]),
        splits_csv=Path(cfg["data"]["splits_csv"]),
        max_images_per_species=cfg["data"]["max_images_per_species"],
        delay=cfg["data"].get("request_delay", 0.5),
        workers=cfg["data"].get("download_workers", 4),
    )
