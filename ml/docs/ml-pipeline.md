# ML Pipeline

The Python pipeline prepares Voteview data, trains a build-time baseline, and exports browser-readable artifacts for **roll-call passage** prediction.

## Commands

```sh
pnpm install
pip install -r requirements.txt
pnpm build:ml
pnpm check
pnpm build
```

`pnpm build:ml` runs the pipeline sequence:

1. `pnpm ml:download`
2. `pnpm ml:prepare`
3. `pnpm ml:train`
4. `pnpm ml:export`

## Scripts

- `ml/pipeline/stages/download_data.py`: fetches or validates source roll-call data into `ml/pipeline/generated-data/raw/`.
- `ml/pipeline/stages/prepare_data.py`: cleans data, enforces `ml/config/features.yaml`, excludes leakage fields, and writes `ml/pipeline/generated-data/processed/training_data.csv` with a chronological split.
- `ml/pipeline/stages/train_model.py`: trains a leakage-safe sklearn logistic-regression baseline from prepared data and writes `ml/pipeline/generated-data/processed/model.joblib` plus `ml/pipeline/generated-data/processed/training_metrics.json`.
- `ml/pipeline/stages/export_model.py`: exports `ml/pipeline/generated-data/processed/model.joblib` to `ml/browser-artifacts/model.onnx` and synchronizes feature schema/category maps/metrics JSON to `static/model/`.

## Current status

Training metrics are real held-out metrics from the prepared chronological test split. The export stage copies those metrics into `static/model/model_metrics.json` only after a trained artifact is converted to ONNX and metrics can mark `model_available: true`. Preserve TODOs for unconfirmed Voteview fields, categorical values, Independent/tie majority-party semantics, and platform-sensitive ONNX runtime installation.
