import type { FeatureSchemaArtifact } from './modelArtifacts';
import type { ModelInputs, ModelInputValue } from './modelInputBuilder';

export type PassageLabel = 'Likely to pass' | 'Unlikely to pass';

export type InferenceArtifacts = {
	featureSchema: FeatureSchemaArtifact;
};

export type InferenceTensorLike = {
	data?: ArrayLike<number>;
};

export type InferenceOutputs = Record<string, InferenceTensorLike | ArrayLike<number> | unknown>;

export type InferenceSession = {
	run(feeds: Record<string, unknown>): Promise<InferenceOutputs>;
};

export type TensorConstructor = new (
	type: 'float32' | 'string',
	data: Float32Array | string[],
	dims: number[]
) => unknown;

export type InferenceRuntime = {
	createSession(modelPath: string): Promise<InferenceSession>;
	Tensor?: TensorConstructor;
};

type DefaultRuntimeState = {
	runtime: InferenceRuntime;
	sessionPromises: Map<string, Promise<InferenceSession>>;
};

export type InferenceResult = {
	probability: number;
	label: PassageLabel;
};

export type InferenceAdapterErrorKind = 'loading' | 'execution' | 'output';

export class InferenceAdapterError extends Error {
	constructor(
		message: string,
		readonly kind: InferenceAdapterErrorKind
	) {
		super(message);
		this.name = 'InferenceAdapterError';
	}
}

export type RunOnnxInferenceOptions = {
	artifacts: InferenceArtifacts;
	inputs: ModelInputs;
	session?: InferenceSession;
	runtime?: InferenceRuntime;
};

class PlainInferenceTensor {
	constructor(
		readonly type: 'float32' | 'string',
		readonly data: Float32Array | string[],
		readonly dims: number[]
	) {}
}

export const modelPath = '/model/model.onnx';

let defaultRuntimeStatePromise: Promise<DefaultRuntimeState> | undefined;

async function createModelSession(runtime: InferenceRuntime): Promise<InferenceSession> {
	try {
		return await runtime.createSession(modelPath);
	} catch {
		throw new InferenceAdapterError('Unable to load ONNX model session.', 'loading');
	}
}

async function resolveSession(options: RunOnnxInferenceOptions): Promise<InferenceSession> {
	if (options.session) return options.session;
	if (!options.runtime) {
		throw new InferenceAdapterError('Unable to load ONNX model: no runtime or session was provided.', 'loading');
	}

	return createModelSession(options.runtime);
}

async function resolveDefaultRuntimeState(): Promise<DefaultRuntimeState> {
	defaultRuntimeStatePromise ??= createOnnxRuntime()
		.then((runtime) => ({
			runtime,
			sessionPromises: new Map<string, Promise<InferenceSession>>()
		}))
		.catch((error) => {
			defaultRuntimeStatePromise = undefined;
			throw error;
		});

	return defaultRuntimeStatePromise;
}

async function resolveDefaultSession(): Promise<{
	runtime: InferenceRuntime;
	session: InferenceSession;
}> {
	const state = await resolveDefaultRuntimeState();
	let sessionPromise = state.sessionPromises.get(modelPath);

	if (!sessionPromise) {
		sessionPromise = createModelSession(state.runtime).catch((error) => {
			state.sessionPromises.delete(modelPath);
			throw error;
		});
		state.sessionPromises.set(modelPath, sessionPromise);
	}

	return { runtime: state.runtime, session: await sessionPromise };
}

function buildTensor(Tensor: TensorConstructor, value: ModelInputValue): unknown {
	if (typeof value === 'string') {
		return new Tensor('string', [value], [1, 1]);
	}

	return new Tensor('float32', new Float32Array([value]), [1, 1]);
}

function buildFeeds(
	featureSchema: FeatureSchemaArtifact,
	inputs: ModelInputs,
	Tensor: TensorConstructor
): Record<string, unknown> {
	return Object.fromEntries(
		featureSchema.ordered_features.map((featureName) => [
			featureName,
			buildTensor(Tensor, inputs[featureName] as ModelInputValue)
		])
	);
}

function numericData(output: unknown): number[] | undefined {
	if (Array.isArray(output)) return output.filter((value): value is number => typeof value === 'number');
	if (output && typeof output === 'object' && 'data' in output) {
		const data = (output as InferenceTensorLike).data;
		if (data) return Array.from(data).filter((value): value is number => typeof value === 'number');
	}
	return undefined;
}

export function parsePassageProbability(outputs: InferenceOutputs): number {
	const probabilities = numericData(outputs.probabilities);
	const passageProbability = probabilities?.length === 1 ? probabilities[0] : probabilities?.[1];

	if (typeof passageProbability !== 'number' || !Number.isFinite(passageProbability)) {
		throw new InferenceAdapterError(
			'Unable to parse roll-call passage probability from ONNX outputs.',
			'output'
		);
	}

	return passageProbability;
}

export function labelForPassageProbability(probability: number): PassageLabel {
	return probability >= 0.5 ? 'Likely to pass' : 'Unlikely to pass';
}

export async function createOnnxRuntime(): Promise<InferenceRuntime> {
	const ort = await import('onnxruntime-web/wasm');

	ort.env.wasm.numThreads = 1;

	return {
		createSession: (modelPath) => ort.InferenceSession.create(modelPath),
		Tensor: ort.Tensor as TensorConstructor
	};
}

export async function runOnnxInference(options: RunOnnxInferenceOptions): Promise<InferenceResult> {
	const resolved = options.session
		? { runtime: options.runtime, session: options.session }
		: options.runtime
			? { runtime: options.runtime, session: await resolveSession(options) }
			: await resolveDefaultSession();
	const Tensor = resolved.runtime?.Tensor ?? PlainInferenceTensor;
	let outputs: InferenceOutputs;

	try {
		outputs = await resolved.session.run(
			buildFeeds(options.artifacts.featureSchema, options.inputs, Tensor)
		);
	} catch {
		throw new InferenceAdapterError('Unable to execute ONNX model inference.', 'execution');
	}

	const probability = parsePassageProbability(outputs);

	return {
		probability,
		label: labelForPassageProbability(probability)
	};
}
