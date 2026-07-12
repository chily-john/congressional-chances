import type { Options } from "highcharts";
import type { ConfusionMatrixCounts, ModelMetricsArtifact } from "$lib/model-runtime";

export type ConfusionMatrixClass = "failed" | "passed";

export type ConfusionMatrixCell = {
  actual: ConfusionMatrixClass;
  predicted: ConfusionMatrixClass;
  count: number;
  rate: number;
  label: string;
  x: number;
  y: number;
};

export type ConfusionMatrixSummary = {
  total: number;
  correct: number;
  incorrect: number;
  accuracy: number;
  actualPassed: number;
  actualFailed: number;
  predictedPassed: number;
  predictedFailed: number;
};

const classLabels: Record<ConfusionMatrixClass, string> = {
  failed: "Failed",
  passed: "Passed",
};

const matrixKeys = [
  "true_negative",
  "false_positive",
  "false_negative",
  "true_positive",
] as const satisfies readonly (keyof ConfusionMatrixCounts)[];

export function getConfusionMatrixFromMetrics(
  modelMetrics: ModelMetricsArtifact,
): ConfusionMatrixCounts | undefined {
  const candidate = modelMetrics.metrics.confusion_matrix;
  if (!isConfusionMatrix(candidate)) return undefined;

  return Object.fromEntries(
    matrixKeys.map((key) => [key, Math.max(0, Math.round(candidate[key]))]),
  ) as ConfusionMatrixCounts;
}

export function buildConfusionMatrixSummary(
  matrix: ConfusionMatrixCounts,
): ConfusionMatrixSummary {
  const total = matrixKeys.reduce((sum, key) => sum + matrix[key], 0);
  const correct = matrix.true_negative + matrix.true_positive;
  const incorrect = matrix.false_positive + matrix.false_negative;

  return {
    total,
    correct,
    incorrect,
    accuracy: total === 0 ? 0 : correct / total,
    actualPassed: matrix.false_negative + matrix.true_positive,
    actualFailed: matrix.true_negative + matrix.false_positive,
    predictedPassed: matrix.false_positive + matrix.true_positive,
    predictedFailed: matrix.true_negative + matrix.false_negative,
  };
}

export function buildConfusionMatrixChartData(
  matrix: ConfusionMatrixCounts,
): ConfusionMatrixCell[] {
  const total = buildConfusionMatrixSummary(matrix).total;

  return [
    buildCell("failed", "failed", matrix.true_negative, total, "True negative", 0, 0),
    buildCell("failed", "passed", matrix.false_positive, total, "False positive", 1, 0),
    buildCell("passed", "failed", matrix.false_negative, total, "False negative", 0, 1),
    buildCell("passed", "passed", matrix.true_positive, total, "True positive", 1, 1),
  ];
}

export function buildConfusionMatrixAriaLabel(
  matrix: ConfusionMatrixCounts,
): string {
  const summary = buildConfusionMatrixSummary(matrix);

  return `Model validation confusion matrix for ${formatCount(summary.total)} roll calls: ${formatCount(summary.correct)} correct predictions (${formatPercent(summary.accuracy)} accuracy), ${formatCount(matrix.true_negative)} true negatives, ${formatCount(matrix.false_positive)} false positives, ${formatCount(matrix.false_negative)} false negatives, and ${formatCount(matrix.true_positive)} true positives.`;
}

export function buildConfusionMatrixHighchartsOptions(
  matrix: ConfusionMatrixCounts,
): Options {
  const data = buildConfusionMatrixChartData(matrix);

  return {
    chart: {
      type: "heatmap",
      backgroundColor: "transparent",
      height: 340,
      spacing: [8, 8, 8, 8],
    },
    title: { text: undefined },
    subtitle: { text: undefined },
    credits: { enabled: false },
    accessibility: { enabled: false },
    legend: {
      align: "right",
      layout: "vertical",
      margin: 0,
      verticalAlign: "middle",
      symbolHeight: 180,
    },
    xAxis: {
      categories: ["Predicted failed", "Predicted passed"],
      opposite: true,
      title: { text: undefined },
      lineWidth: 0,
      tickWidth: 0,
    },
    yAxis: {
      categories: ["Actually failed", "Actually passed"],
      reversed: true,
      title: { text: undefined },
      gridLineWidth: 0,
    },
    colorAxis: {
      min: 0,
      minColor: "#f7ecd4",
      maxColor: "#2f4a6d",
    },
    tooltip: {
      pointFormat:
        "<b>{point.name}</b><br/>Count: <b>{point.value}</b><br/>Share: <b>{point.custom.rateLabel}</b>",
    },
    plotOptions: {
      series: {
        borderColor: "#fffaf0",
        borderWidth: 4,
        dataLabels: {
          enabled: true,
          color: "#24150b",
          format: "{point.value}",
          style: {
            fontSize: "1.1rem",
            fontWeight: "900",
            textOutline: "none",
          },
        },
      } as NonNullable<Options["plotOptions"]>["series"],
    },
    series: [
      {
        type: "heatmap",
        name: "Validation roll calls",
        data: data.map((cell) => ({
          x: cell.x,
          y: cell.y,
          value: cell.count,
          name: cell.label,
          custom: {
            actual: classLabels[cell.actual],
            predicted: classLabels[cell.predicted],
            rate: cell.rate,
            rateLabel: formatPercent(cell.rate),
          },
        })),
      },
    ],
  };
}

export function formatCount(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(
    value,
  );
}

export function formatPercent(value: number): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 1,
    minimumFractionDigits: 1,
    style: "percent",
  }).format(value);
}

export function formatMetricPercent(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value)
    ? formatPercent(value)
    : "—";
}

function buildCell(
  actual: ConfusionMatrixClass,
  predicted: ConfusionMatrixClass,
  count: number,
  total: number,
  label: string,
  x: number,
  y: number,
): ConfusionMatrixCell {
  return {
    actual,
    predicted,
    count,
    rate: total === 0 ? 0 : count / total,
    label,
    x,
    y,
  };
}

function isConfusionMatrix(
  value: unknown,
): value is Record<keyof ConfusionMatrixCounts, number> {
  if (!value || typeof value !== "object") return false;
  const record = value as Record<string, unknown>;

  return matrixKeys.every(
    (key) => typeof record[key] === "number" && Number.isFinite(record[key]),
  );
}
