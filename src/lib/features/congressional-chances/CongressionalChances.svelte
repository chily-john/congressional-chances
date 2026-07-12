<script lang="ts">
    import { onMount, untrack } from "svelte";
    import ChamberChart from "./ChamberChart.svelte";
    import ChamberCompositionControls from "./controls/ChamberCompositionControls.svelte";
    import PartyIdeologyControls from "./controls/PartyIdeologyControls.svelte";
    import RollCallContextControls from "./controls/RollCallContextControls.svelte";
    import ProbabilitySpectrum from "./probability-spectrum/ProbabilitySpectrum.svelte";
    import {
        runOnnxInference,
        type InferenceResult,
        type ModelArtifacts,
    } from "$lib/model-runtime";
    import {
        applyManualChamberEdit,
        applyManualIdeologyEdit,
        applyManualSeatEdit,
        createDefaultPredictionFormState,
        derivePolarizationIndex,
        createPredictionUiState,
        getIdeologyFieldRange,
        getManualSeatFieldMax,
        runLatestValidPrediction,
        type PredictionFormState,
        type PredictionReadinessState,
        type PredictionRunner,
        type SeatCountField,
        type IdeologyField,
    } from "./prediction/predictionForm";

    type Props = {
        artifacts: ModelArtifacts;
        runPrediction?: PredictionRunner;
    };
    let { artifacts, runPrediction = runBrowserPrediction }: Props = $props();

    let form = $state<PredictionFormState>(
        untrack(() => createDefaultPredictionFormState(artifacts)),
    );
    let readiness = $state<PredictionReadinessState>("loading");
    let prediction: InferenceResult | undefined = $state();
    let predictionError = $state("");
    let predictionRequestId = 0;
    let debounceTimer: ReturnType<typeof setTimeout> | undefined;

    const uiState = $derived(
        createPredictionUiState(
            readiness,
            prediction,
            predictionError,
            artifacts.modelMetrics.generated_by,
        ),
    );
    const polarizationIndex = $derived(derivePolarizationIndex(form));
    const polarizationCategory = $derived(
        describePolarizationCategory(polarizationIndex),
    );

    $effect(() => {
        form.chamber;
        form.policyArea;
        form.voteQuestionType;
        form.democraticSeats;
        form.republicanSeats;
        form.independentSeats;
        form.democraticIdeologyMean;
        form.democraticIdeologyMedian;
        form.republicanIdeologyMean;
        form.republicanIdeologyMedian;
        if (readiness !== "ready") return;
        schedulePrediction();
    });

    onMount(async () => {
        try {
            if (!artifacts.modelMetrics.model_available)
                throw new Error("Model artifact is not available.");
            await runPredictionForForm();
            readiness = "ready";
        } catch (error) {
            handlePredictionFailure(error);
        }
    });

    async function runBrowserPrediction(
        inputs: Record<string, string | number>,
    ): Promise<InferenceResult> {
        return runOnnxInference({ artifacts, inputs });
    }

    const seatFields = [
        "democraticSeats",
        "republicanSeats",
        "independentSeats",
    ] as const satisfies readonly SeatCountField[];

    const seatLabels: Record<SeatCountField, string> = {
        democraticSeats: "Democratic",
        republicanSeats: "Republican",
        independentSeats: "Independent",
    };

    const democraticIdeologyFields = [
        { field: "democraticIdeologyMean", label: "Mean" },
        { field: "democraticIdeologyMedian", label: "Median" },
    ] as const satisfies readonly { field: IdeologyField; label: string }[];

    const republicanIdeologyFields = [
        { field: "republicanIdeologyMean", label: "Mean" },
        { field: "republicanIdeologyMedian", label: "Median" },
    ] as const satisfies readonly { field: IdeologyField; label: string }[];

    function editChamber(chamber: string): void {
        form = applyManualChamberEdit(form, chamber);
    }

    function editSeat(field: SeatCountField, input: HTMLInputElement): void {
        const nextForm = applyManualSeatEdit(form, field, input.valueAsNumber);
        form = nextForm;
        input.value = String(nextForm[field]);
    }

    function editIdeology(field: IdeologyField, input: HTMLInputElement): void {
        const nextForm = applyManualIdeologyEdit(
            form,
            field,
            input.valueAsNumber,
        );
        form = nextForm;
        input.value = String(nextForm[field]);
    }

    function editVoteQuestionType(voteQuestionType: string): void {
        form = { ...form, voteQuestionType };
    }

    function editPolicyArea(policyArea: string): void {
        form = { ...form, policyArea };
    }

    function ideologyMin(field: IdeologyField): number {
        return getIdeologyFieldRange(field).min;
    }

    function ideologyMax(field: IdeologyField): number {
        return getIdeologyFieldRange(field).max;
    }

    function describePolarizationCategory(value: number): string {
        const distribution =
            artifacts.modelMetrics.polarization_index_distribution;
        if (!distribution) {
            if (value >= 0.75) return "High polarization";
            if (value >= 0.4) return "Moderate polarization";
            return "Low polarization";
        }

        if (value < distribution.thresholds.moderate_min)
            return distribution.labels.low;
        if (value < distribution.thresholds.high_min)
            return distribution.labels.moderate;
        return distribution.labels.high;
    }

    function seatFieldMax(field: SeatCountField): number {
        return getManualSeatFieldMax(form, field);
    }

    function schedulePrediction(): void {
        if (debounceTimer) clearTimeout(debounceTimer);
        debounceTimer = setTimeout(
            () => void runPredictionForForm().catch(handlePredictionFailure),
            250,
        );
    }

    function handlePredictionFailure(error: unknown): void {
        readiness = "failed";
        prediction = undefined;
        predictionError =
            error instanceof Error
                ? error.message
                : "Prediction failed to load.";
    }

    async function runPredictionForForm(): Promise<void> {
        predictionError = "";
        const requestId = ++predictionRequestId;
        const result = await runLatestValidPrediction({
            artifacts,
            form,
            runPrediction,
            requestId,
            latestRequestId: () => predictionRequestId,
        });
        if (result.stale) return;
        if (!result.build.ok) {
            prediction = undefined;
            predictionError = result.build.errors.join(" ");
            return;
        }
        prediction = result.prediction;
    }
</script>

<svelte:head>
    <title>Congressional Chances</title>
    <meta
        name="description"
        content="Warm dashboard for previewing roll-call passage probability."
    />
</svelte:head>

<main
    class="min-h-screen bg-linear-to-br from-parchment-50 via-parchment-100 to-parchment-200 px-4 py-6 text-parchment-900 sm:px-6 lg:px-8"
>
    <section class="mx-auto grid max-w-6xl gap-5">
        <header
            class="rounded-[2rem] border border-white/70 bg-white/65 p-5 shadow-xl shadow-warm-brown-700/10 backdrop-blur"
        >
            <p
                class="text-xs font-black uppercase tracking-[0.28em] text-warm-brown-700"
            >
                Congressional Chances
            </p>
            <div
                class="mt-2 flex flex-col gap-3 md:flex-row md:items-end md:justify-between"
            >
                <div>
                    <h1
                        class="text-4xl font-black tracking-[-0.06em] sm:text-5xl"
                    >
                        Roll-call passage predictor
                    </h1>
                    <p
                        class="mt-2 max-w-2xl text-sm leading-6 text-parchment-700"
                    >
                        Choose context and vote metadata to preview model-backed
                        passage probability.
                    </p>
                </div>
                <div class="flex flex-col items-end items-center gap-2">
                    <a
                        class="w-fit rounded-full border border-warm-brown-500/25 bg-parchment-50 px-4 py-2 text-sm font-bold text-warm-brown-700 transition hover:bg-white"
                        href="/model-validation"
                    >
                        View model validation
                    </a>
                </div>
            </div>
        </header>

        <ProbabilitySpectrum
            {prediction}
            {readiness}
            {predictionError}
            fallbackText={uiState.resultText || uiState.inferenceStatus}
        />

        <ChamberChart
            chamber={form.chamber}
            democraticSeats={form.democraticSeats}
            republicanSeats={form.republicanSeats}
            independentSeats={form.independentSeats}
            democraticIdeologyMean={form.democraticIdeologyMean}
            democraticIdeologyMedian={form.democraticIdeologyMedian}
            republicanIdeologyMean={form.republicanIdeologyMean}
            republicanIdeologyMedian={form.republicanIdeologyMedian}
            polarizationLabel={`Polarization: ${polarizationIndex.toFixed(3)} · ${polarizationCategory}`}
        >
            {#snippet leftControls()}
                <PartyIdeologyControls
                    title="Democratic ideology"
                    titleId="democratic-ideology-card"
                    titleClass="text-sm font-black text-democratic-moderate"
                    inputClass="w-full rounded-2xl border border-democratic-moderate/35 bg-parchment-50 px-3 py-2 text-parchment-900 outline-democratic-moderate disabled:cursor-not-allowed"
                    fields={democraticIdeologyFields}
                    {form}
                    disabled={uiState.controlsDisabled}
                    getMin={ideologyMin}
                    getMax={ideologyMax}
                    onEdit={editIdeology}
                />
            {/snippet}

            {#snippet rightControls()}
                <PartyIdeologyControls
                    title="Republican ideology"
                    titleId="republican-ideology-card"
                    titleClass="text-sm font-black text-republican-moderate"
                    inputClass="w-full rounded-2xl border border-republican-moderate/35 bg-parchment-50 px-3 py-2 text-parchment-900 outline-republican-moderate disabled:cursor-not-allowed"
                    fields={republicanIdeologyFields}
                    {form}
                    disabled={uiState.controlsDisabled}
                    getMin={ideologyMin}
                    getMax={ideologyMax}
                    onEdit={editIdeology}
                />
            {/snippet}
        </ChamberChart>

        <div class="grid gap-5">
            <form
                class="rounded-[2rem] border border-white/70 bg-white/75 p-5 shadow-xl shadow-warm-brown-700/10"
                aria-label="Roll-call passage prediction controls"
                onsubmit={(event) => event.preventDefault()}
            >
                <fieldset
                    disabled={uiState.controlsDisabled}
                    class="grid gap-4 disabled:opacity-60"
                >
                    <ChamberCompositionControls
                        {artifacts}
                        {form}
                        {seatFields}
                        {seatLabels}
                        getSeatFieldMax={seatFieldMax}
                        onChamberChange={editChamber}
                        onSeatEdit={editSeat}
                    />

                    <RollCallContextControls
                        voteQuestionTypes={artifacts.categoryMaps.categories.vote_question_type ?? []}
                        policyAreas={artifacts.categoryMaps.categories.policy_area ?? []}
                        voteQuestionType={form.voteQuestionType}
                        policyArea={form.policyArea}
                        onVoteQuestionTypeChange={editVoteQuestionType}
                        onPolicyAreaChange={editPolicyArea}
                    />
                </fieldset>
            </form>
        </div>

    </section>
</main>
