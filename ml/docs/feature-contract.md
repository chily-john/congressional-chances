# Feature Contract

The feature contract lives in `ml/config/features.yaml` and supports **roll-call passage** prediction. It is not a bill-enactment model contract.

## File shape

- `schema_version`: version for the feature contract format.
- `scaffold`: marks the current file as sample scaffold content and records TODOs.
- `ordered_features`: canonical model input order. Training, export, and browser inference must use this exact order.
- `feature_groups`: named groups used for validation and documentation.
- `excluded_leakage_fields`: fields that must not be used as model inputs.

## Feature groups

Current groups are:

- `categorical`: `chamber`, `policy_area`, `vote_question_type`, `majority_party`.
- `composition`: chamber composition counts/shares and majority margin.
- `ideology`: Voteview party-level ideology inputs: Democratic and Republican mean/median values plus derived `polarization_index`.

The party medians come from Voteview member ideology scores when available. If a party median cannot be computed for a chamber/congress, the pipeline falls back to that party's mean ideology value; if no party ideology is available, the neutral value `0` is used. `polarization_index` is derived from the distance between Republican and Democratic median ideology values and is used by the UI to label chart polarization from artifact-backed training-data quantile thresholds.

## Categorical values

`ml/browser-artifacts/category_maps.json` contains categorical values synchronized to `static/model/category_maps.json` for browser serving. After export, categories are extracted from the fitted one-hot encoder; unseen browser values are still accepted by the encoder. TODO: confirm exact Voteview categorical values before treating the model as production-ready.

## Update workflow

When adding or changing model inputs:

1. Update `ml/config/features.yaml` first.
2. Regenerate `ml/browser-artifacts/feature_schema.json` and `ml/browser-artifacts/category_maps.json` through `ml/pipeline/stages/export_model.py` after retraining; the export stage synchronizes the public `static/model/` adapter.
3. Keep `ordered_features` synchronized across training, ONNX export, and browser inference.
4. Re-check `ml/docs/data-leakage.md` so outcome-revealing fields remain excluded.

Sample artifacts/metrics are not real model outputs and must not be described as production performance.
