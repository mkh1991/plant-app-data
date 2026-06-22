# Plant Species Classification with BioCLIP

Linear probe trained on frozen [BioCLIP v1](https://huggingface.co/imageomics/bioclip) embeddings for plant species classification from iNaturalist images sourced via GBIF.

## Pipeline overview

```
GBIF download → embedding extraction → probe training → evaluation → inference
```

All heavy computation (embedding extraction, training) runs on CPU by default. Change `model.device` to `cuda` in `configs/default.yaml` if a GPU is available.

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare your species list

Create `data/species.csv` with columns `species_name` and `gbif_taxon_key`:

```csv
species_name,gbif_taxon_key
Rosa canina,3004010
Quercus robur,2878688
Taraxacum officinale,5395024
```

Find taxon keys at [GBIF species search](https://www.gbif.org/species/search).

### 3. Download images

```bash
python -m data.download --config configs/default.yaml
```

Downloads up to `max_images_per_species` (default 200) images per species from iNaturalist via GBIF. Saves images to `data/images/{species_name}/` and a manifest to `data/splits.csv`.

### 4. Assign train/val/test splits

```bash
python -m data.splits --config configs/default.yaml
```

Splits are assigned by **observation ID** (not image), stratified per species: 70% train / 15% val / 15% test. An observation with multiple photos stays entirely in one split.

### 5. Extract BioCLIP embeddings

```bash
python -m embeddings.extract --config configs/default.yaml
```

Downloads BioCLIP weights on first run, then extracts L2-normalised 512-d embeddings for every image. Saves to an HDF5 cache. Re-running skips already-cached images — the process is fully resumable.

Also extracts averaged text embeddings for all species using three prompt formats.

### 6. Train the probe

```bash
python -m train.train --config configs/default.yaml
```

Select the probe type in `configs/default.yaml` under `probe.type`:

| Option | Description |
|--------|-------------|
| `sklearn` | `LogisticRegression` with grid-search over C ∈ {0.01, 0.1, 1, 10} |
| `mlp` | Two-layer MLP (512 → 256 → num_classes), AdamW, early stopping |

### 7. Evaluate

```bash
python -m eval.evaluate --config configs/default.yaml
```

Reports on the held-out test split:

- Macro top-1 / top-3 / top-5 accuracy
- Per-species top-1 accuracy (worst first)
- Top-20 confusion pairs
- Genus-level accuracy
- Zero-shot BioCLIP baseline (no probe)

Results saved to `eval/results.json`.

### 8. Inference on a single image

```bash
python serve/predict.py --image path/to/photo.jpg --top_k 5
```

## Project structure

```
plant-id/
├── data/
│   ├── download.py        # GBIF image download (iNaturalist, CC-licensed)
│   ├── dataset.py         # PyTorch dataset classes
│   └── splits.py          # Observation-level stratified splits
├── embeddings/
│   ├── extract.py         # BioCLIP embedding extraction (resumable)
│   └── cache.py           # HDF5 embedding cache
├── train/
│   ├── probe.py           # sklearn LR + PyTorch MLP definitions
│   └── train.py           # Training loop with val monitoring
├── eval/
│   ├── metrics.py         # Macro top-k, per-species, genus accuracy
│   └── evaluate.py        # Evaluation runner + zero-shot baseline
├── serve/
│   └── predict.py         # Single-image inference CLI
├── configs/
│   └── default.yaml       # All hyperparameters
└── requirements.txt
```

## Configuration

All parameters live in `configs/default.yaml`. Key settings:

```yaml
model:
  device: "cpu"   # change to "cuda" for GPU

probe:
  type: "sklearn"   # or "mlp"

data:
  max_images_per_species: 200
```

## Notes

- BioCLIP backbone weights are **always frozen** — this is a linear probe / MLP head only.
- The zero-shot baseline uses cosine similarity between image and averaged text embeddings. It requires no training and gives the BioCLIP floor to compare against.
- Image downloads gracefully skip failed URLs and log them without aborting the run.
