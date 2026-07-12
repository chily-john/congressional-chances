#!/usr/bin/env python3

# This stage converts the original downloaded Voteview files into a single cleaned CSV:

# There is:
#   * one row per congressional roll-call vote;
#   * only House and Senate votes with official Voteview result labels;
#   * leakage-safe model feature columns ordered by ``ml/config/features.yaml``;
#   * audit metadata columns and a chronological train/test split column.

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
RAW_DATA_DIR = ROOT / "ml" / "pipeline" / "generated-data" / "raw"
PROCESSED_DATA_DIR = ROOT / "ml" / "pipeline" / "generated-data" / "processed"
FEATURE_CONFIG = ROOT / "ml" / "config" / "features.yaml"
ROLLCALLS_FILENAME = "HSall_rollcalls.json"
PARTIES_FILENAME = "HSall_parties.csv"
TRAINING_DATA_FILENAME = "training_data.csv"
TEST_SIZE = 0.20
TARGET_COLUMN = "roll_call_passed"
SPLIT_COLUMN = "split"
SUPPORTED_CHAMBERS = {"House", "Senate"}

# We only rows that actually clearly passed or failed - there are others that aren't clear
# This keeps the ml model trained on more consistent data
POSITIVE_RESULT_KEYWORDS = ("passed", "agreed to", "confirmed", "overridden")
NEGATIVE_RESULT_KEYWORDS = ("failed", "rejected", "defeated")

# =======================================================================================
#  Helper functions below
# =======================================================================================
def classify_vote_result(value: Any) -> int | None:
    if pd.isna(value):
        return None
    normalized = str(value).strip().lower()
    if not normalized:
        return None
    if any(keyword in normalized for keyword in NEGATIVE_RESULT_KEYWORDS):
        return 0
    if any(keyword in normalized for keyword in POSITIVE_RESULT_KEYWORDS):
        return 1
    return None


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, tuple, set, dict)):
        return False
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def normalize_category(value: Any, fallback: str = "unknown") -> str:
    if is_missing(value):
        return fallback
    normalized = str(value).strip().lower()
    if not normalized or normalized in {"nan", "none", "null"}:
        return fallback
    return " ".join(normalized.replace("_", " ").replace("-", " ").split())


def first_non_empty(*values: Any) -> str:
    for value in values:
        if is_missing(value):
            continue
        text = str(value).strip()
        if text and text.lower() not in {"nan", "none", "null"}:
            return text
    return ""


def first_sequence_value(value: Any) -> str:
    if is_missing(value):
        return ""
    if isinstance(value, (list, tuple, set)):
        for item in value:
            text = first_non_empty(item)
            if text:
                return text
        return ""
    return first_non_empty(value)


def derive_vote_question_type(row: pd.Series) -> str:
    text = normalize_category(first_non_empty(row.get("vote_question"), row.get("vote_desc")))
    if text == "unknown":
        return "unknown"
    if "cloture" in text:
        return "cloture"
    if "veto" in text:
        return "veto override"
    if "suspend" in text:
        return "suspension of rules"
    if "nomination" in text or "confirm" in text:
        return "nomination"
    if "conference report" in text:
        return "conference report"
    if "motion to table" in text or "table" in text:
        return "motion to table"
    if "motion to proceed" in text:
        return "motion to proceed"
    if "recommit" in text:
        return "motion to recommit"
    if "amend" in text or "amdt" in text or "amendment" in text:
        return "amendment"
    if "passage" in text or text.startswith("pass") or " pass " in f" {text} ":
        return "passage"
    if "resolution" in text:
        return "resolution"
    if "quorum" in text or "attendance" in text:
        return "quorum or attendance"
    if "speaker" in text:
        return "speaker election"
    if "motion" in text:
        return "procedural motion"
    return "other"


def derive_policy_area(row: pd.Series) -> str:
    crs_policy_area = normalize_category(row.get("crs_policy_area"))
    if crs_policy_area != "unknown":
        return crs_policy_area
    for fallback_column in ["issue_codes", "peltzman_codes", "clausen_codes"]:
        fallback_value = normalize_category(first_sequence_value(row.get(fallback_column)))
        if fallback_value != "unknown":
            return fallback_value
    return "unknown"


def classify_party_group(party_name: Any) -> str:
    normalized = normalize_category(party_name)
    if "independent" in normalized:
        return "independent"
    if "republican" in normalized:
        return "republican"
    if "democrat" in normalized:
        return "democratic"
    return "independent"


def numeric_series(dataframe: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(dataframe[column], errors="coerce")


def weighted_average(values: pd.Series, weights: pd.Series) -> float | None:
    mask = values.notna() & weights.notna() & (weights > 0)
    if not mask.any():
        return None
    return float((values[mask] * weights[mask]).sum() / weights[mask].sum())


def ideology_value_or_neutral(value: float | None) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return float(value)

# ==================================================================================
# ==================================================================================


# This builds the actual party compositions that we need for testing and training
def build_party_composition(parties: pd.DataFrame) -> pd.DataFrame:
    parties = parties[parties["chamber"].isin(SUPPORTED_CHAMBERS)].copy()
    parties["congress"] = numeric_series(parties, "congress").astype("Int64")
    parties["n_members"] = numeric_series(parties, "n_members").fillna(0)
    parties["nominate_dim1_mean"] = numeric_series(parties, "nominate_dim1_mean")
    parties["nominate_dim1_median"] = numeric_series(parties, "nominate_dim1_median")
    parties["party_group"] = parties["party_name"].apply(classify_party_group)
    parties = parties.dropna(subset=["congress"])

    records: list[dict[str, Any]] = []
    for (congress, chamber), group in parties.groupby(["congress", "chamber"], dropna=False):
        seats = {
            party_group: float(group.loc[group["party_group"] == party_group, "n_members"].sum())
            for party_group in ["democratic", "republican", "independent"]
        }
        total = float(sum(seats.values()))
        ranked_parties = sorted(seats.items(), key=lambda item: item[1], reverse=True)
        majority_party = "unknown"
        majority_margin = 0.0
        if total > 0 and ranked_parties:
            top_party, top_seats = ranked_parties[0]
            second_seats = ranked_parties[1][1] if len(ranked_parties) > 1 else 0.0
            majority_party = "tie" if math.isclose(top_seats, second_seats) else top_party
            majority_margin = top_seats - second_seats

        ideology_by_party: dict[str, dict[str, float]] = {}
        for party_group in ["democratic", "republican"]:
            party_rows = group[group["party_group"] == party_group]
            party_mean = ideology_value_or_neutral(
                weighted_average(party_rows["nominate_dim1_mean"], party_rows["n_members"])
            )
            median = weighted_average(party_rows["nominate_dim1_median"], party_rows["n_members"])
            party_median = median if median is not None and not pd.isna(median) else party_mean
            ideology_by_party[party_group] = {
                "mean": party_mean,
                "median": ideology_value_or_neutral(party_median),
            }

        democratic_voteview_median = ideology_by_party["democratic"]["median"]
        republican_voteview_median = ideology_by_party["republican"]["median"]
        polarization_index = abs(republican_voteview_median - democratic_voteview_median)

        record = {
            "congress": int(congress),
            "chamber": chamber,
            "democratic_seats": int(seats["democratic"]),
            "republican_seats": int(seats["republican"]),
            "independent_seats": int(seats["independent"]),
            "total_chamber_size": int(total),
            "majority_party": majority_party,
            "majority_margin": int(majority_margin),
            "democratic_seat_share": seats["democratic"] / total if total else 0.0,
            "republican_seat_share": seats["republican"] / total if total else 0.0,
            "independent_seat_share": seats["independent"] / total if total else 0.0,
            "democratic_voteview_mean": ideology_by_party["democratic"]["mean"],
            "democratic_voteview_median": democratic_voteview_median,
            "republican_voteview_mean": ideology_by_party["republican"]["mean"],
            "republican_voteview_median": republican_voteview_median,
            "polarization_index": polarization_index,
        }
        records.append(record)

    return pd.DataFrame.from_records(records)

def prepare_rollcalls(rollcalls: pd.DataFrame) -> pd.DataFrame:
    rollcalls = rollcalls[rollcalls["chamber"].isin(SUPPORTED_CHAMBERS)].copy()

    rollcalls["congress"] = numeric_series(rollcalls, "congress").astype("Int64")
    rollcalls["rollnumber"] = numeric_series(rollcalls, "rollnumber").astype("Int64")
    rollcalls[TARGET_COLUMN] = rollcalls["vote_result"].apply(classify_vote_result)
    rollcalls = rollcalls.dropna(subset=["congress", "rollnumber", TARGET_COLUMN]).copy()
    rollcalls[TARGET_COLUMN] = rollcalls[TARGET_COLUMN].astype(int)

    rollcalls["date"] = pd.to_datetime(rollcalls["date"], errors="coerce")
    rollcalls = rollcalls.dropna(subset=["date"])

    rollcalls["chamber"] = rollcalls["chamber"].str.lower()
    rollcalls["policy_area"] = rollcalls.apply(derive_policy_area, axis=1)
    rollcalls["vote_question_type"] = rollcalls.apply(derive_vote_question_type, axis=1)
    rollcalls["source_vote_question"] = rollcalls["vote_question"].fillna("").astype(str)
    rollcalls["source_vote_description"] = rollcalls["vote_desc"].fillna("").astype(str)
    rollcalls["target_source"] = "official_vote_result"
    return rollcalls


def add_chronological_split(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = dataframe.sort_values(["date", "congress", "chamber", "rollnumber"]).reset_index(drop=True)
    test_count = max(1, int(round(len(dataframe) * TEST_SIZE)))
    dataframe[SPLIT_COLUMN] = "train"
    dataframe.loc[dataframe.index[-test_count:], SPLIT_COLUMN] = "test"
    return dataframe

# Pretty self-explanatory
# This builds out the data need to test the model
def build_training_dataset(
    rollcalls: pd.DataFrame,
    party_composition: pd.DataFrame,
    ordered_features: list[str],
) -> pd.DataFrame:
    party_composition = party_composition.copy()
    party_composition["chamber"] = party_composition["chamber"].str.lower()
    merged = rollcalls.merge(party_composition, on=["congress", "chamber"], how="inner")
    merged = add_chronological_split(merged)
    metadata_columns = [
        "congress",
        "rollnumber",
        "date",
        "session",
        "bill_number",
        "source_vote_question",
        "source_vote_description",
        "target_source",
    ]
    columns = metadata_columns + ordered_features + [TARGET_COLUMN, SPLIT_COLUMN]
    prepared = merged[columns].copy()
    prepared["date"] = pd.to_datetime(prepared["date"]).dt.strftime("%Y-%m-%d")
    return prepared


def main() -> int:
    with FEATURE_CONFIG.open("r", encoding="utf-8") as handle:
        feature_config = yaml.safe_load(handle)
    ordered_features = list(feature_config["ordered_features"])

    with (RAW_DATA_DIR / ROLLCALLS_FILENAME).open("r", encoding="utf-8") as handle:
        rollcall_records = json.load(handle)

    rollcalls = prepare_rollcalls(pd.DataFrame.from_records(rollcall_records))
    party_composition = build_party_composition(pd.read_csv(RAW_DATA_DIR / PARTIES_FILENAME, low_memory=False))
    prepared = build_training_dataset(
        rollcalls=rollcalls,
        party_composition=party_composition,
        ordered_features=ordered_features,
    )

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DATA_DIR / TRAINING_DATA_FILENAME
    prepared.to_csv(output_path, index=False)

    split_counts = prepared[SPLIT_COLUMN].value_counts().to_dict()
    print(f"Prepared {len(prepared)} Voteview rows: {output_path}")
    print(f"Chronological split: train={split_counts.get('train', 0)}, test={split_counts.get('test', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
