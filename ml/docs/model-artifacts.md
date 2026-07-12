# Model Artifacts

Files under `ml/browser-artifacts/` are the canonical browser-readable artifacts for **roll-call passage** prediction. `ml/pipeline/stages/export_model.py` replaces these artifacts after training succeeds and synchronizes matching files into the SvelteKit public adapter at `static/model/`.

## `feature_schema.json`

Copies the ordered feature list for runtime validation and inference input construction. Export validates that it matches `ml/config/features.yaml` and adds input type metadata for the ONNX graph. The active ideology contract uses Voteview party mean and median fields for Democrats and Republicans, with `polarization_index` derived from the party medians.

## `category_maps.json`

Lists categorical values for fields such as `chamber`, `policy_area`, `vote_question_type`, and `majority_party`. Scaffold values are illustrative; exported values come from the fitted one-hot encoder, with unknown categories handled by the exported encoder.

## `model_metrics.json`

Contains held-out metrics copied from `ml/pipeline/generated-data/processed/training_metrics.json` during export, including training-data quantile thresholds used to label derived polarization as low, moderate, or high. Do not hand-edit performance values; they must come from the training/evaluation stage.

## `model.onnx`

`ml/browser-artifacts/model.onnx` is written by the export stage from the fitted sklearn pipeline and synchronized to `static/model/model.onnx` for browser serving. Until export has succeeded, no placeholder ONNX file should imply a trained model is available.
