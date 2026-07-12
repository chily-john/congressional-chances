import { chamberSeatLimits, deriveChamberComposition } from "$lib/domain/congress";
import type { InferenceResult, ModelArtifacts } from "$lib/model-runtime";
import {
  buildModelInputs,
  derivePolarizationIndex,
  type ModelInputBuildResult,
  type ModelInputFormState,
} from "$lib/model-runtime";

export type PredictionReadinessState = "loading" | "ready" | "failed";

export type PredictionUiState = {
  controlsDisabled: boolean;
  inferenceStatus: string;
  inferenceDetail: string;
  resultText: string;
};

export type ProbabilitySpectrumValue = {
  markerPercent: number;
  displayText: string;
  label: string;
};

export type PredictionFormState = ModelInputFormState;

export type SeatCountField =
  | "democraticSeats"
  | "republicanSeats"
  | "independentSeats";

export type IdeologyField =
  | "democraticIdeologyMean"
  | "democraticIdeologyMedian"
  | "republicanIdeologyMean"
  | "republicanIdeologyMedian";

export type IdeologyFieldRange = {
  min: number;
  max: number;
};

const ideologyFieldRanges: Record<IdeologyField, IdeologyFieldRange> = {
  democraticIdeologyMean: { min: -1, max: 0 },
  democraticIdeologyMedian: { min: -1, max: 0 },
  republicanIdeologyMean: { min: 0, max: 1 },
  republicanIdeologyMedian: { min: 0, max: 1 },
};

export type PredictionRunner = (
  inputs: Record<string, string | number>,
) => Promise<InferenceResult>;

function firstCategory(
  artifacts: ModelArtifacts,
  key: "chamber" | "policy_area" | "vote_question_type",
): string {
  return artifacts.categoryMaps.categories[key]?.[0] ?? "";
}

function defaultSeatComposition(chamber: string): Pick<
  PredictionFormState,
  "democraticSeats" | "republicanSeats" | "independentSeats"
> {
  if (chamber === "senate") {
    return { democraticSeats: 48, republicanSeats: 49, independentSeats: 3 };
  }
  if (chamber === "house") {
    return { democraticSeats: 213, republicanSeats: 222, independentSeats: 0 };
  }
  return { democraticSeats: 0, republicanSeats: 0, independentSeats: 0 };
}

export function createDefaultPredictionFormState(
  artifacts: ModelArtifacts,
): PredictionFormState {
  const chamber = firstCategory(artifacts, "chamber");

  return {
    chamber,
    policyArea: firstCategory(artifacts, "policy_area"),
    voteQuestionType: firstCategory(artifacts, "vote_question_type"),
    ...defaultSeatComposition(chamber),
    democraticIdeologyMean: -0.25,
    democraticIdeologyMedian: -0.25,
    republicanIdeologyMean: 0.25,
    republicanIdeologyMedian: 0.25,
  };
}

const editableSeatFields = [
  "democraticSeats",
  "republicanSeats",
  "independentSeats",
] as const satisfies readonly SeatCountField[];

function sanitizeSeatEditValue(value: number | undefined): number {
  if (value === undefined || !Number.isFinite(value) || value < 0) return 0;
  return Math.floor(value);
}

function seatTotal(state: Pick<PredictionFormState, SeatCountField>): number {
  return editableSeatFields.reduce(
    (total, field) => total + sanitizeSeatEditValue(state[field]),
    0,
  );
}

export function getManualSeatFieldMax(
  state: PredictionFormState,
  field: SeatCountField,
): number {
  const chamberLimit = chamberSeatLimits[state.chamber] ?? Number.POSITIVE_INFINITY;
  const otherEditableTotal = editableSeatFields
    .filter((candidate) => candidate !== field)
    .reduce((total, candidate) => total + sanitizeSeatEditValue(state[candidate]), 0);

  return Math.max(0, chamberLimit - otherEditableTotal);
}

function clampSeatsToChamberLimit(state: PredictionFormState): PredictionFormState {
  const chamberLimit = chamberSeatLimits[state.chamber];
  if (chamberLimit === undefined) return state;

  const sanitizedState = {
    ...state,
    democraticSeats: sanitizeSeatEditValue(state.democraticSeats),
    republicanSeats: sanitizeSeatEditValue(state.republicanSeats),
    independentSeats: sanitizeSeatEditValue(state.independentSeats),
  };
  const totalSeats = seatTotal(sanitizedState);
  if (totalSeats <= chamberLimit) return sanitizedState;
  if (totalSeats === 0) return sanitizedState;

  const scaledSeats = editableSeatFields.map((field) => {
    const scaled = (sanitizedState[field] * chamberLimit) / totalSeats;
    return {
      field,
      seats: Math.floor(scaled),
      remainder: scaled % 1,
    };
  });
  let remainingSeats =
    chamberLimit - scaledSeats.reduce((total, entry) => total + entry.seats, 0);

  for (const entry of [...scaledSeats].sort((a, b) => b.remainder - a.remainder)) {
    if (remainingSeats <= 0) break;
    entry.seats += 1;
    remainingSeats -= 1;
  }

  return {
    ...sanitizedState,
    democraticSeats: scaledSeats.find((entry) => entry.field === "democraticSeats")?.seats ?? 0,
    republicanSeats: scaledSeats.find((entry) => entry.field === "republicanSeats")?.seats ?? 0,
    independentSeats: scaledSeats.find((entry) => entry.field === "independentSeats")?.seats ?? 0,
  };
}

export function applyManualChamberEdit(
  state: PredictionFormState,
  chamber: string,
): PredictionFormState {
  return clampSeatsToChamberLimit({
    ...state,
    chamber,
  });
}

export function applyManualSeatEdit(
  state: PredictionFormState,
  field: SeatCountField,
  value: number,
): PredictionFormState {
  const editedSeats = Math.min(
    sanitizeSeatEditValue(value),
    getManualSeatFieldMax(state, field),
  );

  return { ...state, [field]: editedSeats };
}

export function getIdeologyFieldRange(field: IdeologyField): IdeologyFieldRange {
  return ideologyFieldRanges[field];
}

export function applyManualIdeologyEdit(
  state: PredictionFormState,
  field: IdeologyField,
  value: number,
): PredictionFormState {
  const sanitizedValue = Number.isFinite(value) ? value : 0;
  const range = getIdeologyFieldRange(field);
  return { ...state, [field]: Math.min(range.max, Math.max(range.min, sanitizedValue)) };
}

export { derivePolarizationIndex };

export function derivePredictionFormComposition(state: PredictionFormState) {
  try {
    return deriveChamberComposition(state);
  } catch {
    return deriveChamberComposition({
      democraticSeats: 0,
      republicanSeats: 0,
      independentSeats: 0,
    });
  }
}

export type LatestPredictionResult = {
  stale: boolean;
  build: ModelInputBuildResult;
  prediction?: InferenceResult;
};

export async function runLatestValidPrediction(options: {
  artifacts: ModelArtifacts;
  form: PredictionFormState;
  runPrediction: PredictionRunner;
  requestId: number;
  latestRequestId: () => number;
}): Promise<LatestPredictionResult> {
  const build = buildModelInputs(options.artifacts, options.form);
  if (!build.ok) return { stale: false, build };
  const prediction = await options.runPrediction(build.inputs);
  const stale = options.requestId !== options.latestRequestId();
  return { stale, build, prediction: stale ? undefined : prediction };
}

export function formatProbability(probability: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 0,
  }).format(probability);
}

export function formatPredictionResult(result: InferenceResult): string {
  return `${formatProbability(result.probability)} roll-call passage probability — ${result.label}`;
}

export function getProbabilitySpectrumValue(
  result: InferenceResult,
): ProbabilitySpectrumValue {
  const boundedProbability = Math.min(1, Math.max(0, result.probability));
  return {
    markerPercent: Math.round(boundedProbability * 100),
    displayText: formatProbability(boundedProbability),
    label: result.label,
  };
}

export function createPredictionUiState(
  readiness: PredictionReadinessState,
  prediction: InferenceResult | undefined,
  predictionError: string,
  generatedBy: string,
): PredictionUiState {
  const controlsDisabled = false;
  const resultText = prediction ? formatPredictionResult(prediction) : "";

  if (readiness === "loading") {
    return {
      controlsDisabled,
      inferenceStatus: "Loading model...",
      inferenceDetail: generatedBy,
      resultText: "Loading model...",
    };
  }

  if (readiness === "failed") {
    return {
      controlsDisabled,
      inferenceStatus: "Prediction unavailable",
      inferenceDetail: predictionError,
      resultText: `Model unavailable: ${predictionError}`,
    };
  }

  return {
    controlsDisabled,
    inferenceStatus: "Prediction ready",
    inferenceDetail: generatedBy,
    resultText: resultText || predictionError,
  };
}
