"""Render pass/fail percentages grouped by vote type.

Default input: ml/pipeline/generated-data/processed/training_data.csv
Outputs: output/pass_fail_by_vote_type.csv and .svg
"""

from __future__ import annotations

import argparse
from pathlib import Path

from chart_helpers import (
    DEFAULT_INPUT,
    DEFAULT_OUTPUT_DIR,
    aggregate_pass_fail,
    read_processed_rows,
    render_pass_fail_bar_svg,
    write_summary_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pass/fail roll-call rates by vote type.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Processed training_data.csv path.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for CSV and SVG outputs.")
    parser.add_argument("--top", type=int, default=25, help="Number of largest vote types to include in the SVG.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_processed_rows(args.input)
    summary = aggregate_pass_fail(rows, "vote_question_type")

    csv_path = args.output_dir / "pass_fail_by_vote_type.csv"
    svg_path = args.output_dir / "pass_fail_by_vote_type.svg"

    write_summary_csv(
        csv_path,
        summary,
        ["label", "total", "passed", "failed", "pass_pct", "fail_pct"],
    )
    render_pass_fail_bar_svg(
        summary[: args.top],
        svg_path,
        title="Pass/Fail by Vote Type",
        subtitle=f"Top {min(args.top, len(summary))} vote types by roll-call count from {args.input.name}",
        group_name="Vote type",
    )

    print(f"Read {len(rows)} roll calls")
    print(f"Wrote {csv_path}")
    print(f"Wrote {svg_path}")


if __name__ == "__main__":
    main()
