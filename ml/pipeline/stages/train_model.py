#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import yaml
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DATA_DIR = ROOT / "ml" / "pipeline" / "generated-data" / "processed"
FEATURE_CONFIG = ROOT / "ml" / "config" / "features.yaml"
TRAINING_DATA_FILENAME = "training_data.csv"
MODEL_ARTIFACT_FILENAME = "model.joblib"
METRICS_FILENAME = "training_metrics.json"
TARGET_COLUMN = "roll_call_passed"
SPLIT_COLUMN = "split"
TRAIN_SPLIT = "train"
TEST_SPLIT = "test"


def load_feature_config(path: Path) -> tuple[list[str], list[str]]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    ordered_features = list(data["ordered_features"])
    feature_groups = data.get("feature_groups", {})
    categorical_features = list(feature_groups.get("categorical", []))
    return ordered_features, categorical_features


def load_training_data(path: Path) -> pd.DataFrame:
    dataframe = pd.read_csv(path, low_memory=False).copy()
    dataframe[SPLIT_COLUMN] = dataframe[SPLIT_COLUMN].astype(str).str.strip().str.lower()
    dataframe[TARGET_COLUMN] = dataframe[TARGET_COLUMN].astype(int)
    return dataframe


def build_pipeline(categorical_features: list[str], numeric_features: list[str]) -> Pipeline:
    transformers: list[tuple[str, Pipeline, list[str]]] = []
    if categorical_features:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
                        ("one_hot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                categorical_features,
            )
        )
    if numeric_features:
        transformers.append(
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            )
        )

    return Pipeline(
        steps=[
            ("preprocessor", ColumnTransformer(transformers=transformers, remainder="drop")),
            (
                "classifier",
                LogisticRegression(class_weight="balanced", max_iter=1000, solver="lbfgs"),
            ),
        ]
    )


def class_balance(labels: pd.Series) -> dict[str, int]:
    counts = labels.value_counts().to_dict()
    return {"0": int(counts.get(0, 0)), "1": int(counts.get(1, 0))}


def build_polarization_index_distribution(train_rows: pd.DataFrame) -> dict[str, Any] | None:
    if "polarization_index" not in train_rows.columns:
        return None
    values = pd.to_numeric(train_rows["polarization_index"], errors="coerce").dropna()
    if values.empty:
        return None
    return {
        "feature": "polarization_index",
        "source": "training_data_quantiles",
        "quantiles": {
            "0.33": float(values.quantile(0.33)),
            "0.67": float(values.quantile(0.67)),
        },
        "thresholds": {
            "moderate_min": float(values.quantile(0.33)),
            "high_min": float(values.quantile(0.67)),
        },
        "labels": {
            "low": "Low polarization",
            "moderate": "Moderate polarization",
            "high": "High polarization",
        },
        "notes": [
            "Thresholds are computed from the train split polarization_index distribution during model training.",
            "Use values below moderate_min as low, values below high_min as moderate, and values at or above high_min as high.",
        ],
    }


def evaluate_model(model: Pipeline, x_test: pd.DataFrame, y_test: pd.Series) -> dict[str, Any]:
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)
    positive_class_index = list(model.named_steps["classifier"].classes_).index(1)
    positive_scores = probabilities[:, positive_class_index]
    tn, fp, fn, tp = confusion_matrix(y_test, predictions, labels=[0, 1]).ravel()

    roc_auc: float | None = None
    if y_test.nunique() == 2:
        roc_auc = float(roc_auc_score(y_test, positive_scores))

    return {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "f1": float(f1_score(y_test, predictions, zero_division=0)),
        "roc_auc": roc_auc,
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
    }


def train_model(
    dataframe: pd.DataFrame,
    ordered_features: list[str],
    categorical_features: list[str],
) -> tuple[Pipeline, dict[str, Any]]:
    train_rows = dataframe[dataframe[SPLIT_COLUMN] == TRAIN_SPLIT]
    test_rows = dataframe[dataframe[SPLIT_COLUMN] == TEST_SPLIT]

    categorical_feature_set = set(categorical_features)
    numeric_features = [feature for feature in ordered_features if feature not in categorical_feature_set]
    model = build_pipeline(categorical_features=categorical_features, numeric_features=numeric_features)

    x_train = train_rows[ordered_features]
    y_train = train_rows[TARGET_COLUMN]
    x_test = test_rows[ordered_features]
    y_test = test_rows[TARGET_COLUMN]
    model.fit(x_train, y_train)

    metrics = {
        "model_type": "sklearn_logistic_regression",
        "target_column": TARGET_COLUMN,
        "split_column": SPLIT_COLUMN,
        "training_rows": int(len(train_rows)),
        "test_rows": int(len(test_rows)),
        "train_class_balance": class_balance(y_train),
        "test_class_balance": class_balance(y_test),
        "feature_columns": ordered_features,
        "categorical_features": categorical_features,
        "numeric_features": numeric_features,
        "polarization_index_distribution": build_polarization_index_distribution(train_rows),
        "metrics": evaluate_model(model, x_test, y_test),
    }
    return model, metrics


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_model_artifact(path: Path, model: Pipeline, metadata: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": model, "metadata": metadata}, path)


def main() -> None:
    training_data = PROCESSED_DATA_DIR / TRAINING_DATA_FILENAME
    model_output = PROCESSED_DATA_DIR / MODEL_ARTIFACT_FILENAME
    metrics_output = PROCESSED_DATA_DIR / METRICS_FILENAME

    ordered_features, categorical_features = load_feature_config(FEATURE_CONFIG)
    dataframe = load_training_data(training_data)
    model, metrics = train_model(dataframe, ordered_features, categorical_features)
    artifact_metadata = {
        key: value
        for key, value in metrics.items()
        if key in {"model_type", "target_column", "split_column", "feature_columns", "categorical_features", "numeric_features"}
    }
    write_model_artifact(model_output, model, artifact_metadata)
    write_json(metrics_output, metrics)

    print(f"Trained roll-call passage model: {model_output}")
    print(f"Wrote evaluation metrics: {metrics_output}")


if __name__ == "__main__":
    main()
