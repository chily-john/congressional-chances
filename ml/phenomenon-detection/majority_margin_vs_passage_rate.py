"""Render passage rate by majority-party seat margin.

Default input: ml/pipeline/generated-data/processed/training_data.csv
Outputs: output/majority_margin_vs_passage_rate.csv and .svg
"""

from __future__ import annotations

import argparse
from pathlib import Path

from chart_helpers import (
    DEFAULT_INPUT,
    DEFAULT_OUTPUT_DIR,
    is_passed,
    read_processed_rows,
    render_margin_line_svg,
    write_summary_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Passage rate by majority-party seat margin.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Processed training_data.csv path.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for CSV and SVG outputs.")
    parser.add_argument("--min-count", type=int, default=1, help="Drop margin values with fewer roll calls than this.")
    return parser.parse_args()


def aggregate_by_majority_margin(rows: list[dict[str, str]], min_count: int) -> list[dict[str, object]]:
    groups: dict[int, dict[str, int]] = {}

    for row in rows:
        raw_margin = (row.get("majority_margin") or "").strip()
        if not raw_margin:
            continue

        try:
            margin = round(float(raw_margin))
        except ValueError:
            continue

        bucket = groups.setdefault(margin, {"passed": 0, "failed": 0})
        if is_passed(row.get("roll_call_passed", "")):
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1

    summary: list[dict[str, object]] = []
    for margin, counts in groups.items():
        total = counts["passed"] + counts["failed"]
        if total < min_count:
            continue

        passage_rate = counts["passed"] / total * 100 if total else 0.0
        summary.append(
            {
                "majority_margin": margin,
                "total": total,
                "passed": counts["passed"],
                "failed": counts["failed"],
                "passage_rate_pct": passage_rate,
            }
        )

    return sorted(summary, key=lambda item: int(item["majority_margin"]))


def main() -> None:
    args = parse_args()
    rows = read_processed_rows(args.input)
    summary = aggregate_by_majority_margin(rows, args.min_count)

    csv_path = args.output_dir / "majority_margin_vs_passage_rate.csv"
    svg_path = args.output_dir / "majority_margin_vs_passage_rate.svg"

    write_summary_csv(
        csv_path,
        summary,
        ["majority_margin", "total", "passed", "failed", "passage_rate_pct"],
    )
    render_margin_line_svg(
        summary,
        svg_path,
        title="Majority Margin vs. Passage Rate",
        subtitle=f"Each point is one majority-seat margin from {args.input.name}; point size reflects roll-call count",
    )

    print(f"Read {len(rows)} roll calls")
    print(f"Kept {len(summary)} majority-margin groups")
    print(f"Wrote {csv_path}")
    print(f"Wrote {svg_path}")


if __name__ == "__main__":
    main()
