export type ScaffoldMetadata = {
	generated_by: 'scaffold' | string;
	is_sample: boolean;
	notes?: string[];
};

export type FeatureSchemaArtifact = ScaffoldMetadata & {
	schema_version: number;
	ordered_features: string[];
};

export type CategoryMapsArtifact = ScaffoldMetadata & {
	categories: Record<string, string[]>;
};

export type PolarizationIndexDistribution = {
	feature: 'polarization_index' | string;
	thresholds: {
		moderate_min: number;
		high_min: number;
	};
	labels: {
		low: string;
		moderate: string;
		high: string;
	};
};

export type ConfusionMatrixCounts = {
	true_negative: number;
	false_positive: number;
	false_negative: number;
	true_positive: number;
};

export type ModelMetricsArtifact = ScaffoldMetadata & {
	model_available: boolean;
	metrics: {
		accuracy?: number;
		precision?: number;
		recall?: number;
		f1?: number;
		roc_auc?: number;
		confusion_matrix?: ConfusionMatrixCounts;
		[key: string]: unknown;
	};
	feature_columns?: string[];
	numeric_features?: string[];
	model_type?: string;
	split_column?: string;
	target_column?: string;
	test_rows?: number;
	training_rows?: number;
	polarization_index_distribution?: PolarizationIndexDistribution;
};

export type ModelArtifacts = {
	featureSchema: FeatureSchemaArtifact;
	categoryMaps: CategoryMapsArtifact;
	modelMetrics: ModelMetricsArtifact;
};

export type ArtifactFetch = (input: string) => Promise<{ ok: boolean; status: number; json: () => Promise<unknown> }>;

const artifactPaths = {
	featureSchema: '/model/feature_schema.json',
	categoryMaps: '/model/category_maps.json',
	modelMetrics: '/model/model_metrics.json'
} as const;

async function fetchJson<T>(fetcher: ArtifactFetch, path: string): Promise<T> {
	const response = await fetcher(path);
	if (!response.ok) {
		throw new Error(`Failed to load ${path}: HTTP ${response.status}`);
	}
	return (await response.json()) as T;
}

export async function loadModelArtifacts(fetcher: ArtifactFetch = fetch): Promise<ModelArtifacts> {
	const [featureSchema, categoryMaps, modelMetrics] = await Promise.all([
		fetchJson<FeatureSchemaArtifact>(fetcher, artifactPaths.featureSchema),
		fetchJson<CategoryMapsArtifact>(fetcher, artifactPaths.categoryMaps),
		fetchJson<ModelMetricsArtifact>(fetcher, artifactPaths.modelMetrics)
	]);

	return { featureSchema, categoryMaps, modelMetrics };
}
