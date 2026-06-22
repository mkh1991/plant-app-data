"""Assign train/val/test splits by observation ID (stratified per species)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

Split = Literal["train", "val", "test"]

TRAIN_FRAC = 0.70
VAL_FRAC = 0.15
# test = 1 - TRAIN_FRAC - VAL_FRAC = 0.15


def _assign_obs_splits(obs_ids: np.ndarray, seed: int = 42) -> dict[str, Split]:
    """Assign each observation ID to a split, stratified at observation level."""
    obs_ids = np.unique(obs_ids)

    if len(obs_ids) < 3:
        # Too few observations — put everything in train
        return {oid: "train" for oid in obs_ids}

    # First split off test, then split remainder into train/val
    val_test_frac = VAL_FRAC + (1.0 - TRAIN_FRAC - VAL_FRAC)  # 0.30
    try:
        train_ids, valtest_ids = train_test_split(
            obs_ids, test_size=val_test_frac, random_state=seed
        )
        # val_frac within valtest portion
        val_frac_of_valtest = VAL_FRAC / val_test_frac
        val_ids, test_ids = train_test_split(
            valtest_ids, test_size=0.5, random_state=seed
        )
    except ValueError:
        # Fallback for tiny sets
        train_ids, val_ids, test_ids = obs_ids, np.array([]), np.array([])

    mapping: dict[str, Split] = {}
    for oid in train_ids:
        mapping[str(oid)] = "train"
    for oid in val_ids:
        mapping[str(oid)] = "val"
    for oid in test_ids:
        mapping[str(oid)] = "test"
    return mapping


def assign_splits(
    splits_csv: Path,
    seed: int = 42,
    overwrite: bool = False,
) -> pd.DataFrame:
    """
    Read the image manifest from splits_csv, assign splits by observation ID
    stratified per species, write back, and return the updated DataFrame.
    """
    splits_csv = Path(splits_csv)
    df = pd.read_csv(splits_csv)

    if "split" in df.columns and df["split"].notna().all() and not overwrite:
        already_assigned = (df["split"] != "").all()
        if already_assigned:
            print("Splits already assigned. Use overwrite=True to reassign.")
            return df

    if "observation_id" not in df.columns:
        raise ValueError("splits_csv must contain an 'observation_id' column")

    obs_to_split: dict[str, Split] = {}

    for species, group in df.groupby("species_name"):
        obs_ids = group["observation_id"].astype(str).unique()
        mapping = _assign_obs_splits(obs_ids, seed=seed)
        obs_to_split.update(mapping)

    df["split"] = df["observation_id"].astype(str).map(obs_to_split).fillna("train")
    df.to_csv(splits_csv, index=False)

    counts = df["split"].value_counts()
    print(f"Split counts: {dict(counts)}")
    return df


def load_splits(splits_csv: Path) -> pd.DataFrame:
    return pd.read_csv(splits_csv)


if __name__ == "__main__":
    import argparse
    import yaml

    parser = argparse.ArgumentParser(description="Assign train/val/test splits")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    assign_splits(Path(cfg["data"]["splits_csv"]), overwrite=args.overwrite)
