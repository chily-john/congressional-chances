"""Small CSV aggregation and SVG helpers for phenomenon-detection scripts.

These helpers intentionally use only the Python standard library so the scripts can
run in a bare environment after the processed CSV has been generated.
"""

from __future__ import annotations

import csv
import html
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "ml" / "pipeline" / "generated-data" / "processed" / "training_data.csv"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"

PASSED_VALUES = {"1", "true", "t", "yes", "y", "passed", "pass"}


def read_processed_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def is_passed(value: str) -> bool:
    return str(value).strip().lower() in PASSED_VALUES


def clean_label(value: str | None) -> str:
    value = (value or "").strip()
    return value if value else "(missing)"


def aggregate_pass_fail(rows: Iterable[dict[str, str]], group_column: str) -> list[dict[str, object]]:
    groups: dict[str, dict[str, int]] = {}

    for row in rows:
        label = clean_label(row.get(group_column))
        bucket = groups.setdefault(label, {"passed": 0, "failed": 0})
        if is_passed(row.get("roll_call_passed", "")):
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1

    summary: list[dict[str, object]] = []
    for label, counts in groups.items():
        total = counts["passed"] + counts["failed"]
        pass_pct = (counts["passed"] / total * 100) if total else 0.0
        summary.append(
            {
                "label": label,
                "total": total,
                "passed": counts["passed"],
                "failed": counts["failed"],
                "pass_pct": pass_pct,
                "fail_pct": 100 - pass_pct,
            }
        )

    return sorted(summary, key=lambda item: (-int(item["total"]), str(item["label"])))


def write_summary_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def svg_escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def short_label(value: object, max_chars: int = 42) -> str:
    text = str(value)
    return text if len(text) <= max_chars else text[: max_chars - 1] + "…"


def render_pass_fail_bar_svg(
    rows: list[dict[str, object]],
    output_path: Path,
    *,
    title: str,
    subtitle: str,
    group_name: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    width = 1100
    left = 330
    bar_width = 600
    top = 115
    row_height = 30
    height = top + max(len(rows), 1) * row_height + 75
    passed_color = "#2f855a"
    failed_color = "#c53030"
    text_color = "#1a202c"
    muted_color = "#718096"

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="40" y="42" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="{text_color}">{svg_escape(title)}</text>',
        f'<text x="40" y="68" font-family="Arial, sans-serif" font-size="14" fill="{muted_color}">{svg_escape(subtitle)}</text>',
        f'<rect x="{left}" y="84" width="18" height="12" fill="{passed_color}"/>',
        f'<text x="{left + 26}" y="95" font-family="Arial, sans-serif" font-size="13" fill="{text_color}">Passed</text>',
        f'<rect x="{left + 100}" y="84" width="18" height="12" fill="{failed_color}"/>',
        f'<text x="{left + 126}" y="95" font-family="Arial, sans-serif" font-size="13" fill="{text_color}">Failed</text>',
        f'<text x="40" y="103" font-family="Arial, sans-serif" font-size="12" font-weight="700" fill="{muted_color}">{svg_escape(group_name)}</text>',
        f'<text x="{left}" y="103" font-family="Arial, sans-serif" font-size="12" font-weight="700" fill="{muted_color}">0%</text>',
        f'<text x="{left + bar_width / 2 - 14}" y="103" font-family="Arial, sans-serif" font-size="12" font-weight="700" fill="{muted_color}">50%</text>',
        f'<text x="{left + bar_width - 28}" y="103" font-family="Arial, sans-serif" font-size="12" font-weight="700" fill="{muted_color}">100%</text>',
        f'<line x1="{left}" y1="108" x2="{left + bar_width}" y2="108" stroke="#e2e8f0"/>',
    ]

    for index, row in enumerate(rows):
        y = top + index * row_height
        pass_pct = float(row["pass_pct"])
        fail_pct = float(row["fail_pct"])
        passed_width = bar_width * pass_pct / 100
        failed_width = bar_width - passed_width
        label = short_label(row["label"])
        full_label = svg_escape(row["label"])
        total = int(row["total"])

        lines.extend(
            [
                f'<text x="40" y="{y + 17}" font-family="Arial, sans-serif" font-size="13" fill="{text_color}">{svg_escape(label)}<title>{full_label}</title></text>',
                f'<rect x="{left}" y="{y}" width="{passed_width:.2f}" height="20" fill="{passed_color}"><title>{full_label}: {pass_pct:.1f}% passed</title></rect>',
                f'<rect x="{left + passed_width:.2f}" y="{y}" width="{failed_width:.2f}" height="20" fill="{failed_color}"><title>{full_label}: {fail_pct:.1f}% failed</title></rect>',
                f'<text x="{left + bar_width + 15}" y="{y + 15}" font-family="Arial, sans-serif" font-size="13" fill="{text_color}">{pass_pct:.1f}% pass / {fail_pct:.1f}% fail</text>',
                f'<text x="{left + bar_width + 185}" y="{y + 15}" font-family="Arial, sans-serif" font-size="12" fill="{muted_color}">n={total}</text>',
            ]
        )

    lines.append("</svg>\n")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def render_margin_line_svg(rows: list[dict[str, object]], output_path: Path, *, title: str, subtitle: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    width = 950
    height = 560
    left = 80
    right = 40
    top = 88
    bottom = 70
    plot_width = width - left - right
    plot_height = height - top - bottom
    text_color = "#1a202c"
    muted_color = "#718096"
    line_color = "#2b6cb0"
    point_color = "#dd6b20"

    margins = [float(row["majority_margin"]) for row in rows]
    min_x = min(margins) if margins else 0.0
    max_x = max(margins) if margins else 1.0
    if min_x == max_x:
        min_x -= 1
        max_x += 1

    def x_pos(value: float) -> float:
        return left + (value - min_x) / (max_x - min_x) * plot_width

    def y_pos(rate_pct: float) -> float:
        return top + (100 - rate_pct) / 100 * plot_height

    points = [(x_pos(float(row["majority_margin"])), y_pos(float(row["passage_rate_pct"]))) for row in rows]
    polyline = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="40" y="42" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="{text_color}">{svg_escape(title)}</text>',
        f'<text x="40" y="68" font-family="Arial, sans-serif" font-size="14" fill="{muted_color}">{svg_escape(subtitle)}</text>',
    ]

    for pct in range(0, 101, 20):
        y = y_pos(pct)
        lines.extend(
            [
                f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}" stroke="#edf2f7"/>',
                f'<text x="35" y="{y + 4:.2f}" font-family="Arial, sans-serif" font-size="12" fill="{muted_color}">{pct}%</text>',
            ]
        )

    lines.extend(
        [
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#2d3748"/>',
            f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#2d3748"/>',
            f'<text x="{left + plot_width / 2 - 65}" y="{height - 25}" font-family="Arial, sans-serif" font-size="13" fill="{text_color}">Majority margin (seats)</text>',
            f'<text x="18" y="{top + plot_height / 2 + 55}" transform="rotate(-90 18 {top + plot_height / 2 + 55})" font-family="Arial, sans-serif" font-size="13" fill="{text_color}">Passage rate</text>',
        ]
    )

    for tick in range(0, 6):
        value = min_x + (max_x - min_x) * tick / 5
        x = x_pos(value)
        lines.extend(
            [
                f'<line x1="{x:.2f}" y1="{top + plot_height}" x2="{x:.2f}" y2="{top + plot_height + 6}" stroke="#2d3748"/>',
                f'<text x="{x - 14:.2f}" y="{top + plot_height + 24}" font-family="Arial, sans-serif" font-size="12" fill="{muted_color}">{value:.0f}</text>',
            ]
        )

    if polyline:
        lines.append(f'<polyline points="{polyline}" fill="none" stroke="{line_color}" stroke-width="2.5"/>')

    max_total = max((int(row["total"]) for row in rows), default=1)
    for row in rows:
        margin = float(row["majority_margin"])
        rate = float(row["passage_rate_pct"])
        total = int(row["total"])
        radius = 3 + (total / max_total) * 6
        lines.append(
            f'<circle cx="{x_pos(margin):.2f}" cy="{y_pos(rate):.2f}" r="{radius:.2f}" fill="{point_color}" opacity="0.78">'
            f'<title>Margin {margin:.0f}: {rate:.1f}% passed, n={total}</title></circle>'
        )

    lines.append("</svg>\n")
    output_path.write_text("\n".join(lines), encoding="utf-8")
