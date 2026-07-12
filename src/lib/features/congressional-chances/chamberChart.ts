import type { Options } from "highcharts";
import { chamberSeatLimits } from "$lib/domain/congress";

export type ChamberSeatParty =
  "democratic" | "independent" | "republican" | "vacancy" | "gap";

type MajorParty = "democratic" | "republican";

export type ChamberSeatInput = {
  chamber: keyof typeof chamberSeatLimits;
  democraticSeats: number;
  republicanSeats: number;
  independentSeats?: number;
  democraticIdeologyMean?: number;
  democraticIdeologyMedian?: number;
  republicanIdeologyMean?: number;
  republicanIdeologyMedian?: number;
};

export type ChamberChartSummaryGroup = {
  count: number;
  percentage: number;
  percentageLabel: string;
};

export type ChamberChartSummary = {
  capacity: number;
  groups: Record<Exclude<ChamberSeatParty, "gap">, ChamberChartSummaryGroup>;
  majority: {
    party: Exclude<ChamberSeatParty, "gap"> | "tie";
    label: string;
    margin: number;
  };
};

export type ChamberChartSeriesDatum = {
  name: string;
  y: number;
  color: string;
  party: ChamberSeatParty;
  borderColor?: string;
  borderWidth?: number;
  marker?: Record<string, unknown>;
  states?: Record<string, unknown>;
};

type CountedSeatParty = Exclude<ChamberSeatParty, "gap">;
type ClampedSeatCounts = Record<CountedSeatParty, number>;

export const chamberChartColors: Record<CountedSeatParty, string> = {
  democratic: "#2f4a6d",
  republican: "#9f4238",
  independent: "#c59a38",
  vacancy: "#e8dcc7",
};

const democratFactionLabels = [
  "Moderate",
  "Mainstream",
  "Core",
  "Progressive",
  "Far-Left",
].toReversed();
const republicanFactionLabels = [
  "Moderate",
  "Mainstream",
  "Core",
  "Conservative",
  "Far-Right",
];
const factionColorIntensities = [0.02, 0.22, 0.5, 0.75, 1];
const factionSkewWeight = 0.06;

export function buildChamberChartSummary(
  input: ChamberSeatInput,
): ChamberChartSummary {
  const chamberLimit = chamberSeatLimits[input.chamber];
  const counts = clampSeatCounts(input, chamberLimit);
  const groups = Object.fromEntries(
    (["democratic", "independent", "republican", "vacancy"] as const).map(
      (party) => [
        party,
        {
          count: counts[party],
          percentage: counts[party] / chamberLimit,
          percentageLabel: formatPercentage(counts[party], chamberLimit),
        },
      ],
    ),
  ) as Record<CountedSeatParty, ChamberChartSummaryGroup>;
  const majority = getMajoritySummary(counts);

  return { capacity: chamberLimit, groups, majority };
}

export function buildChamberChartAriaLabel(
  chamberLabel: string,
  summary: ChamberChartSummary,
): string {
  return `${chamberLabel} chamber composition chart with ${summary.capacity} total seats. ${summary.majority.label} by ${summary.majority.margin}: ${summary.groups.democratic.count} Democratic (${summary.groups.democratic.percentageLabel}), ${summary.groups.republican.count} Republican (${summary.groups.republican.percentageLabel}), ${summary.groups.independent.count} Independent (${summary.groups.independent.percentageLabel}), and ${summary.groups.vacancy.count} vacancy or unknown (${summary.groups.vacancy.percentageLabel}).`;
}

export function buildChamberChartSeriesData(
  input: ChamberSeatInput,
): ChamberChartSeriesDatum[] {
  const chamberLimit = chamberSeatLimits[input.chamber];
  const counts = clampSeatCounts(input, chamberLimit);
  const vacancies = splitCenterSeatsForChart(
    counts.vacancy,
    counts.democratic,
    counts.republican,
    chamberLimit,
  );
  const independents = splitCenterSeatsForChart(
    counts.independent,
    counts.democratic + vacancies.left,
    counts.republican + vacancies.right,
    chamberLimit,
  );
  const gap = buildPolarizationGap(input, chamberLimit);

  return [
    ...buildMajorPartyFactions(
      "democratic",
      counts.democratic,
      input.democraticIdeologyMean,
      input.democraticIdeologyMedian,
    ),
    buildSeriesDatum("vacancy", vacancies.left),
    buildSeriesDatum("independent", independents.left),
    gap,
    buildSeriesDatum("independent", independents.right),
    buildSeriesDatum("vacancy", vacancies.right),
    ...buildMajorPartyFactions(
      "republican",
      counts.republican,
      input.republicanIdeologyMean,
      input.republicanIdeologyMedian,
    ),
  ];
}

export function buildChamberHighchartsOptions(
  seriesData: ChamberChartSeriesDatum[],
): Options {
  return {
    chart: {
      type: "item",
      backgroundColor: "transparent",
      height: 220,
      spacing: [0, 0, 0, 0],
    },
    title: { text: undefined },
    subtitle: { text: undefined },
    legend: { enabled: false },
    credits: { enabled: false },
    accessibility: { enabled: false },
    tooltip: {
      pointFormat: "{point.name}: <b>{point.custom.tooltipValue}</b>",
    },
    plotOptions: {
      series: {
        dataLabels: { enabled: false },
        center: ["50%", "105%"],
        size: "210%",
        startAngle: -90,
        endAngle: 90,
        borderColor: "rgba(0, 0, 0, 0)",
        borderWidth: 0,
        marker: {
          lineWidth: 0,
          states: {
            hover: { lineWidth: 0, lineWidthPlus: 0 },
          },
        },
        states: {
          hover: { borderWidth: 0, lineWidthPlus: 0 },
        },
      } as NonNullable<Options["plotOptions"]>["series"],
    },
    series: [
      {
        type: "item",
        data: seriesData.map((row) => ({
          name: row.name,
          y: row.y,
          color: row.color,
          showInLegend: false,
          borderColor: row.borderColor,
          borderWidth: row.borderWidth,
          marker: row.marker,
          states: row.states,
          custom: {
            party: row.party,
            isSeat: row.party !== "gap",
            seatCount: row.party === "gap" ? 0 : row.y,
            tooltipValue:
              row.party === "gap" ? "visual separation only" : `${row.y} seats`,
          },
        })),
      },
    ],
  };
}

function buildMajorPartyFactions(
  party: MajorParty,
  count: number,
  mean = 0,
  median = 0,
): ChamberChartSeriesDatum[] {
  if (count <= 0) return [];

  return allocateFactionSeats(count, mean, median).map((seats, index) => {
    const name = `${partyLabel(party) === "Democrat" ? democratFactionLabels[index] : republicanFactionLabels[index]} ${partyLabel(party)} `;
    return {
      name,
      y: seats,
      color: majorPartyFactionColor(party, median, index),
      party,
    };
  });
}

// Illustrative only: these buckets are a visual distribution, not member-level claims.
function allocateFactionSeats(
  count: number,
  mean: number,
  median: number,
): number[] {
  const skew = clampNumber(mean - median, -1, 1);
  const base = [0.12, 0.2, 0.36, 0.2, 0.12];
  const adjusted = base.map((weight, index) => {
    const side = index - 2;
    return Math.max(0.02, weight + side * skew * factionSkewWeight);
  });
  const total = adjusted.reduce((sum, weight) => sum + weight, 0);
  const exact = adjusted.map((weight) => (weight / total) * count);
  const seats = exact.map(Math.floor);
  let remaining = count - seats.reduce((sum, value) => sum + value, 0);

  exact
    .map((value, index) => ({ index, remainder: value - Math.floor(value) }))
    .toSorted((a, b) => b.remainder - a.remainder || a.index - b.index)
    .forEach(({ index }) => {
      if (remaining > 0) {
        seats[index] += 1;
        remaining -= 1;
      }
    });

  return seats;
}

function majorPartyFactionColor(
  party: MajorParty,
  ideology: number,
  factionIndex: number,
): string {
  const ideologyIntensity =
    party === "democratic"
      ? clampNumber(-ideology, 0, 1)
      : clampNumber(ideology, 0, 1);
  const factionIntensity =
    (party === "democratic"
      ? factionColorIntensities.toReversed()[factionIndex]
      : factionColorIntensities[factionIndex]) ?? factionColorIntensities[2];

  return majorPartyColorByIntensity(
    party,
    clampNumber(factionIntensity * 0.75 + ideologyIntensity * 0.25, 0, 1),
  );
}

function majorPartyColorByIntensity(
  party: MajorParty,
  intensity: number,
): string {
  const palette: Record<
    MajorParty,
    [number, number, number, number, number, number]
  > = {
    democratic: [74, 116, 169, 23, 52, 95],
    republican: [196, 94, 82, 126, 35, 30],
  };
  const [r0, g0, b0, r1, g1, b1] = palette[party];
  const mix = (start: number, end: number) =>
    Math.round(start + (end - start) * intensity);

  return rgbToHex(mix(r0, r1), mix(g0, g1), mix(b0, b1));
}

// The gap uses a Highcharts item `y` value only to reserve visual space; callers must
// use party !== "gap" or point.custom.seatCount for all seat accounting.
function buildPolarizationGap(
  input: ChamberSeatInput,
  chamberLimit: number,
): ChamberChartSeriesDatum {
  const polarization = clampNumber(
    Math.abs(
      (input.republicanIdeologyMedian ?? 0) -
        (input.democraticIdeologyMedian ?? 0),
    ),
    0,
    1,
  );
  return {
    name: "Polarization gap",
    y: Math.min(
      Math.round(chamberLimit * 0.1),
      Math.max(0, Math.round(polarization * chamberLimit * 0.1)),
    ),
    color: "rgba(0, 0, 0, 0)",
    party: "gap",
    borderColor: "rgba(0, 0, 0, 0)",
    borderWidth: 0,
    marker: {
      lineColor: "rgba(0, 0, 0, 0)",
      lineWidth: 0,
      states: {
        hover: { lineWidth: 0, lineWidthPlus: 0 },
      },
    },
    states: {
      hover: { borderColor: "rgba(0, 0, 0, 0)", borderWidth: 0 },
    },
  };
}

function buildSeriesDatum(
  party: CountedSeatParty,
  count: number,
): ChamberChartSeriesDatum {
  return {
    name: partyLabel(party),
    y: count,
    color: chamberChartColors[party],
    party,
  };
}

function splitCenterSeatsForChart(
  seatsToSplit: number,
  leftStart: number,
  rightStart: number,
  chamberLimit: number,
): { left: number; right: number } {
  const halfCapacity = chamberLimit / 2;
  let leftOccupied = leftStart;
  let rightOccupied = rightStart;
  let left = 0;
  let right = 0;

  for (let seat = 0; seat < seatsToSplit; seat += 1) {
    const leftCanReceive = leftOccupied < halfCapacity;
    const rightCanReceive = rightOccupied < halfCapacity;

    if (!leftCanReceive && rightCanReceive) {
      right += 1;
      rightOccupied += 1;
    } else if (!rightCanReceive && leftCanReceive) {
      left += 1;
      leftOccupied += 1;
    } else if (leftOccupied <= rightOccupied) {
      left += 1;
      leftOccupied += 1;
    } else {
      right += 1;
      rightOccupied += 1;
    }
  }

  return { left, right };
}

function clampSeatCounts(
  input: ChamberSeatInput,
  chamberLimit: number,
): ClampedSeatCounts {
  const democratic = clampWholeSeat(input.democraticSeats, chamberLimit);
  const republican = clampWholeSeat(
    input.republicanSeats,
    chamberLimit - democratic,
  );
  const independent = clampWholeSeat(
    input.independentSeats ?? 0,
    chamberLimit - democratic - republican,
  );
  const vacancy = chamberLimit - democratic - republican - independent;

  return { democratic, independent, republican, vacancy };
}

function clampWholeSeat(value: number, max: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.min(Math.max(0, Math.floor(value)), Math.max(0, max));
}

function clampNumber(value: number, min: number, max: number): number {
  if (!Number.isFinite(value)) return min;
  return Math.min(Math.max(value, min), max);
}

function rgbToHex(red: number, green: number, blue: number): string {
  return `#${[red, green, blue]
    .map((value) => value.toString(16).padStart(2, "0"))
    .join("")}`;
}

function formatPercentage(count: number, capacity: number): string {
  const percentage = (count / capacity) * 100;
  const rounded =
    percentage < 1 && percentage > 0
      ? Math.round(percentage * 10) / 10
      : Math.round(percentage);

  return `${rounded}%`;
}

function getMajoritySummary(
  counts: ClampedSeatCounts,
): ChamberChartSummary["majority"] {
  const contenders = (["democratic", "independent", "republican"] as const)
    .map((party) => ({ party, count: counts[party] }))
    .toSorted((a, b) => b.count - a.count);
  const [leader, runnerUp] = contenders;

  if (!leader || !runnerUp || leader.count === runnerUp.count) {
    return { party: "tie", label: "Tie", margin: 0 };
  }

  return {
    party: leader.party,
    label: `${partyLabel(leader.party)} lead`,
    margin: leader.count - runnerUp.count,
  };
}

function partyLabel(party: CountedSeatParty): string {
  const labels: Record<CountedSeatParty, string> = {
    democratic: "Democrat",
    independent: "Independent",
    republican: "Republican",
    vacancy: "Vacancy/unknown",
  };

  return labels[party];
}
