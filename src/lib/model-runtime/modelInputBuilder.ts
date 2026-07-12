import { chamberSeatLimits, deriveChamberComposition } from "$lib/domain/congress";
import type {
  CategoryMapsArtifact,
  FeatureSchemaArtifact,
} from "./modelArtifacts";

export type ModelInputValue = string | number;
export type ModelInputs = Record<string, ModelInputValue>;

export type ModelInputArtifacts = {
  featureSchema: FeatureSchemaArtifact;
  categoryMaps: CategoryMapsArtifact;
};

export type ModelInputFormState = {
  chamber: string;
  policyArea: string;
  voteQuestionType: string;
  democraticSeats: number;
  republicanSeats: number;
  independentSeats?: number;
  democraticIdeologyMean?: number;
  democraticIdeologyMedian?: number;
  republicanIdeologyMean?: number;
  republicanIdeologyMedian?: number;
};

export type ValidModelInputBuildResult = {
  ok: true;
  inputs: ModelInputs;
};

export type InvalidModelInputBuildResult = {
  ok: false;
  errors: string[];
};

export type ModelInputBuildResult =
  ValidModelInputBuildResult | InvalidModelInputBuildResult;

type FeatureValues = {
  chamber: string;
  policy_area: string;
  vote_question_type: string;
  democratic_seats: number;
  republican_seats: number;
  independent_seats: number;
  total_chamber_size: number;
  majority_party: string;
  majority_margin: number;
  democratic_seat_share: number;
  republican_seat_share: number;
  independent_seat_share: number;
  democratic_voteview_mean: number;
  democratic_voteview_median: number;
  republican_voteview_mean: number;
  republican_voteview_median: number;
  polarization_index: number;
};

function ideologyValue(value: number | undefined): number {
  return value ?? 0;
}

export function derivePolarizationIndex(
  form: Pick<ModelInputFormState, "democraticIdeologyMedian" | "republicanIdeologyMedian">,
): number {
  return Math.abs(
    ideologyValue(form.republicanIdeologyMedian) -
      ideologyValue(form.democraticIdeologyMedian),
  );
}

function validateCategory(
  categories: Record<string, string[]>,
  key: "chamber" | "policy_area" | "vote_question_type",
  value: string,
  errors: string[],
): void {
  if (!categories[key]?.includes(value)) {
    errors.push(`Unsupported ${key} category: ${value}`);
  }
}

export function buildModelInputs(
  artifacts: ModelInputArtifacts,
  form: ModelInputFormState,
): ModelInputBuildResult {
  const errors: string[] = [];
  const categories = artifacts.categoryMaps.categories;

  validateCategory(categories, "chamber", form.chamber, errors);
  validateCategory(categories, "policy_area", form.policyArea, errors);
  validateCategory(
    categories,
    "vote_question_type",
    form.voteQuestionType,
    errors,
  );

  let composition: ReturnType<typeof deriveChamberComposition> | undefined;
  try {
    composition = deriveChamberComposition({
      democraticSeats: form.democraticSeats,
      republicanSeats: form.republicanSeats,
      independentSeats: form.independentSeats,
    });
    if (composition.totalSeats <= 0) {
      errors.push("Chamber total seats must be greater than zero.");
    }
    const chamberLimit = chamberSeatLimits[form.chamber];
    if (chamberLimit !== undefined && composition.totalSeats > chamberLimit) {
      errors.push(`${form.chamber} seat total cannot exceed ${chamberLimit}.`);
    }
  } catch (error) {
    errors.push(
      error instanceof Error ? error.message : "Invalid chamber composition.",
    );
  }

  const independentSeats = form.independentSeats ?? 0;
  const values: FeatureValues | undefined = composition
    ? {
        chamber: form.chamber,
        policy_area: form.policyArea,
        vote_question_type: form.voteQuestionType,
        democratic_seats: form.democraticSeats,
        republican_seats: form.republicanSeats,
        independent_seats: independentSeats,
        total_chamber_size: composition.totalSeats,
        majority_party: composition.majorityParty,
        majority_margin: composition.majorityMargin,
        democratic_seat_share: composition.partyShares.democratic,
        republican_seat_share: composition.partyShares.republican,
        independent_seat_share: composition.partyShares.independent,
        // Conservative MVP ranges are enforced by the UI; missing values stay neutral.
        democratic_voteview_mean: ideologyValue(form.democraticIdeologyMean),
        democratic_voteview_median: ideologyValue(form.democraticIdeologyMedian),
        republican_voteview_mean: ideologyValue(form.republicanIdeologyMean),
        republican_voteview_median: ideologyValue(form.republicanIdeologyMedian),
        polarization_index: derivePolarizationIndex(form),
      }
    : undefined;

  if (!values) {
    return { ok: false, errors };
  }

  const inputs: ModelInputs = {};
  for (const featureName of artifacts.featureSchema.ordered_features) {
    if (!(featureName in values)) {
      errors.push(`Unsupported model feature: ${featureName}`);
      continue;
    }
    inputs[featureName] = values[featureName as keyof FeatureValues];
  }

  if (errors.length > 0) {
    return { ok: false, errors };
  }

  return { ok: true, inputs };
}
