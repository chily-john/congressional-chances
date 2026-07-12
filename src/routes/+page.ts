import { loadModelArtifacts } from '$lib/model-runtime';

export const load = async ({ fetch }) => {
	return {
		artifacts: await loadModelArtifacts(fetch)
	};
};
