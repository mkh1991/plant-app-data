"""PyTorch dataset for plant images, reading from the splits CSV."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import pandas as pd
from PIL import Image
from torch.utils.data import Dataset


class PlantDataset(Dataset):
    """Loads plant images according to the splits manifest.

    Args:
        splits_csv: path to CSV with columns image_path, species_name, observation_id, split.
        split: "train", "val", or "test". Pass None to load all.
        transform: torchvision transform applied to PIL images.
    """

    def __init__(
        self,
        splits_csv: Path,
        split: Optional[str],
        transform: Optional[Callable] = None,
    ) -> None:
        df = pd.read_csv(splits_csv)
        if split is not None:
            df = df[df["split"] == split].reset_index(drop=True)
        self.df = df
        self.transform = transform
        self.species_list = sorted(df["species_name"].unique().tolist())
        self.species_to_idx = {s: i for i, s in enumerate(self.species_list)}

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> tuple:
        row = self.df.iloc[idx]
        img = Image.open(row["image_path"]).convert("RGB")
        if self.transform is not None:
            img = self.transform(img)
        label = self.species_to_idx[row["species_name"]]
        return img, label, row["image_path"]

    @property
    def num_classes(self) -> int:
        return len(self.species_list)


class EmbeddingDataset(Dataset):
    """Dataset that returns pre-computed embeddings instead of raw images.

    Args:
        embeddings: float32 numpy array of shape (N, D).
        labels: integer array of shape (N,).
    """

    def __init__(self, embeddings, labels) -> None:
        import torch
        self.embeddings = torch.tensor(embeddings, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int) -> tuple:
        return self.embeddings[idx], self.labels[idx]
