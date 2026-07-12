#!/usr/bin/env python3

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml

MODEL_DIR = ROOT / "ml" / "browser-artifacts"
PUBLIC_MODEL_DIR = ROOT / "static" / "model"
GENERATED_BY = "ml/pipeline/stages/export_model.py"

def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)

def load_feature_config(path: Path) -> tuple[dict[str, Any], list[str], list[str]]:
    data = load_yaml(path)
    ordered_features = list(data["ordered_features"])
    categorical_features = list(data.get("feature_groups", {}).get("categorical", []))
    return data, ordered_features, categorical_features

def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")

def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

def load_training_pipeline(path: Path) -> Any:
    import joblib

    artifact = joblib.load(path)
    return artifact["pipeline"]

def normalize_for_onnx(pipeline: Any) -> None:
    preprocessor = pipeline.named_steps.get("preprocessor") if hasattr(pipeline, "named_steps") else None
    categorical_transformer = None
    if preprocessor is not None and hasattr(preprocessor, "named_transformers_"):
        categorical_transformer = preprocessor.named_transformers_.get("categorical")
    if categorical_transformer is None or not hasattr(categorical_transformer, "named_steps"):
        return
    imputer = categorical_transformer.named_steps.get("imputer")
    if imputer is not None and getattr(imputer, "strategy", None) == "constant":
        imputer.missing_values = ""

def convert_pipeline_to_onnx(
    pipeline: Any,
    ordered_features: list[str],
    categorical_features: list[str],
) -> bytes:
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import FloatTensorType, StringTensorType

    export_pipeline = copy.deepcopy(pipeline)
    normalize_for_onnx(export_pipeline)
    categorical_feature_set = set(categorical_features)
    initial_types = [
        (
            feature,
            StringTensorType([None, 1]) if feature in categorical_feature_set else FloatTensorType([None, 1]),
        )
        for feature in ordered_features
    ]
    classifier = export_pipeline.named_steps.get("classifier") if hasattr(export_pipeline, "named_steps") else None
    options = {id(classifier): {"zipmap": False}} if classifier is not None else None
    onnx_model = convert_sklearn(
        export_pipeline,
        initial_types=initial_types,
        target_opset=15,
        options=options,
    )
    return onnx_model.SerializeToString()

def extract_category_maps(pipeline: Any, categorical_features: list[str]) -> dict[str, list[str]]:
    if not categorical_features:
        return {}
    preprocessor = pipeline.named_steps["preprocessor"]
    categorical_transformer = preprocessor.named_transformers_["categorical"]
    categories = categorical_transformer.named_steps["one_hot"].categories_
    return {
        feature: [str(value) for value in values.tolist()]
        for feature, values in zip(categorical_features, categories)
    }

def build_feature_schema(feature_config: dict[str, Any], ordered_features: list[str], categorical_features: list[str]) -> dict[str, Any]:
    categorical_feature_set = set(categorical_features)
    return {
        "generated_by": GENERATED_BY,
        "is_sample": False,
        "schema_version": feature_config["schema_version"],
        "ordered_features": ordered_features,
        "feature_groups": feature_config.get("feature_groups", {}),
        "input_types": {
            feature: "string" if feature in categorical_feature_set else "float"
            for feature in ordered_features
        },
        "notes": [
            "Feature order is synchronized from ml/config/features.yaml.",
            "The ONNX graph accepts one tensor per ordered feature, each with shape [batch, 1].",
        ],
    }

def build_category_maps(category_maps: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "generated_by": GENERATED_BY,
        "is_sample": False,
        "categories": category_maps,
        "category_encoding": {
            "encoder": "OneHotEncoder",
            "handle_unknown": "ignore",
            "missing_string_value": "",
        },
        "notes": [
            "Categories are extracted from the fitted training pipeline.",
            "Unseen browser input categories are accepted by the exported encoder and map to all-zero one-hot values.",
        ],
    }

def build_model_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_by": GENERATED_BY,
        "is_sample": False,
        "model_available": True,
        "model_type": metrics.get("model_type"),
        "target_column": metrics.get("target_column"),
        "split_column": metrics.get("split_column"),
        "training_rows": metrics.get("training_rows"),
        "test_rows": metrics.get("test_rows"),
        "train_class_balance": metrics.get("train_class_balance"),
        "test_class_balance": metrics.get("test_class_balance"),
        "feature_columns": metrics.get("feature_columns"),
        "categorical_features": metrics.get("categorical_features"),
        "numeric_features": metrics.get("numeric_features"),
        "polarization_index_distribution": metrics.get("polarization_index_distribution"),
        "metrics": metrics.get("metrics", {}),
    }

def synchronize_public_adapter() -> None:
    PUBLIC_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for artifact_path in sorted(path for path in MODEL_DIR.iterdir() if path.is_file()):
        write_bytes(PUBLIC_MODEL_DIR / artifact_path.name, artifact_path.read_bytes())


if __name__ == "__main__":
    PROCESSED_DATA_DIR = ROOT / "ml" / "pipeline" / "generated-data" / "processed"
    ONNX_MODEL_FILENAME = "model.onnx"

    feature_config, ordered_features, categorical_features = load_feature_config(ROOT / "ml" / "config" / "features.yaml")
    pipeline = load_training_pipeline(PROCESSED_DATA_DIR / "model.joblib")
    metrics = load_json(PROCESSED_DATA_DIR / "training_metrics.json")

    onnx_bytes = convert_pipeline_to_onnx(
        pipeline,
        ordered_features=ordered_features,
        categorical_features=categorical_features,
    )
    category_maps = extract_category_maps(pipeline, categorical_features)

    write_bytes(MODEL_DIR / ONNX_MODEL_FILENAME, onnx_bytes)
    write_json(MODEL_DIR / "feature_schema.json", build_feature_schema(feature_config, ordered_features, categorical_features))
    write_json(MODEL_DIR / "category_maps.json", build_category_maps(category_maps))
    write_json(MODEL_DIR / "model_metrics.json", build_model_metrics(metrics))
    synchronize_public_adapter()

    print(f"Exported ONNX roll-call passage model: {MODEL_DIR / ONNX_MODEL_FILENAME}")
    print(f"Synchronized static model artifacts: {PUBLIC_MODEL_DIR}")
