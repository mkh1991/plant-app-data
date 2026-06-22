"""Disk cache for image embeddings using h5py."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

import h5py
import numpy as np


def _path_key(image_path: str) -> str:
    """Convert an image path to a safe h5py dataset name."""
    # Use MD5 of the path so long paths with special chars are safe
    return hashlib.md5(image_path.encode()).hexdigest()


class EmbeddingCache:
    """Read/write embedding cache backed by a single HDF5 file.

    Each image's embedding is stored as a dataset named by the MD5 of its path.
    A separate string dataset maps MD5 keys back to original paths for lookup.
    """

    def __init__(self, cache_path: Path) -> None:
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        # Keep a local dict of path -> key for fast membership tests
        self._path_to_key: dict[str, str] = {}
        if self.cache_path.exists():
            self._load_index()

    def _load_index(self) -> None:
        with h5py.File(self.cache_path, "r") as f:
            if "_paths" in f:
                paths = [p.decode() if isinstance(p, bytes) else p for p in f["_paths"][:]]
                keys = [p.decode() if isinstance(p, bytes) else p for p in f["_keys"][:]]
                self._path_to_key = dict(zip(paths, keys))

    def __contains__(self, image_path: str) -> bool:
        return image_path in self._path_to_key

    def get(self, image_path: str) -> Optional[np.ndarray]:
        if image_path not in self._path_to_key:
            return None
        key = self._path_to_key[image_path]
        with h5py.File(self.cache_path, "r") as f:
            if key in f:
                return f[key][:]
        return None

    def put_batch(self, path_embedding_pairs: list[tuple[str, np.ndarray]]) -> None:
        """Write a batch of (image_path, embedding) pairs atomically."""
        if not path_embedding_pairs:
            return
        mode = "a" if self.cache_path.exists() else "w"
        with h5py.File(self.cache_path, mode) as f:
            for image_path, emb in path_embedding_pairs:
                key = _path_key(image_path)
                if key not in f:
                    f.create_dataset(key, data=emb.astype(np.float32))
                self._path_to_key[image_path] = key
            # Rewrite index datasets
            paths = list(self._path_to_key.keys())
            keys = list(self._path_to_key.values())
            dt = h5py.string_dtype(encoding="utf-8")
            for name, data in [("_paths", paths), ("_keys", keys)]:
                if name in f:
                    del f[name]
                f.create_dataset(name, data=np.array(data, dtype=object), dtype=dt)

    def load_split(
        self,
        image_paths: list[str],
    ) -> tuple[np.ndarray, list[str]]:
        """Load embeddings for a list of paths. Returns (embeddings, found_paths)."""
        found_paths: list[str] = []
        embeddings: list[np.ndarray] = []
        with h5py.File(self.cache_path, "r") as f:
            for p in image_paths:
                key = self._path_to_key.get(p)
                if key and key in f:
                    embeddings.append(f[key][:])
                    found_paths.append(p)
        if not embeddings:
            return np.empty((0, 0), dtype=np.float32), []
        return np.stack(embeddings, axis=0).astype(np.float32), found_paths


def save_text_embeddings(
    embeddings: np.ndarray,
    species_list: list[str],
    emb_path: Path,
    index_path: Path,
) -> None:
    import json
    emb_path = Path(emb_path)
    index_path = Path(index_path)
    emb_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(emb_path), embeddings.astype(np.float32))
    with open(index_path, "w") as f:
        json.dump({name: i for i, name in enumerate(species_list)}, f, indent=2)


def load_text_embeddings(
    emb_path: Path,
    index_path: Path,
) -> tuple[np.ndarray, dict[str, int]]:
    import json
    emb = np.load(str(emb_path))
    with open(index_path) as f:
        index = json.load(f)
    return emb, index
