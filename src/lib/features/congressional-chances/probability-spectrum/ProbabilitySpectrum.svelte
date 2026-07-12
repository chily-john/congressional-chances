<script lang="ts">
    import type { InferenceResult } from "$lib/model-runtime";
    import {
        getProbabilitySpectrumValue,
        type PredictionReadinessState,
    } from "../prediction/predictionForm";

    type Props = {
        prediction?: InferenceResult;
        readiness: PredictionReadinessState;
        predictionError: string;
        fallbackText: string;
    };

    let { prediction, readiness, predictionError, fallbackText }: Props = $props();

    const spectrum = $derived(
        prediction ? getProbabilitySpectrumValue(prediction) : undefined,
    );
    const hasPrediction = $derived(readiness === "ready" && Boolean(spectrum));
    const placeholderText = $derived(
        readiness === "failed"
            ? `Prediction unavailable${predictionError ? `: ${predictionError}` : ""}`
            : readiness === "loading"
              ? "Loading model before showing the probability spectrum."
              : predictionError || fallbackText || "Adjust valid inputs to show a probability spectrum.",
    );
</script>

<section
    class="w-full rounded-[2rem] border border-white/70 bg-white/75 p-5 shadow-xl shadow-warm-brown-700/10 transition-opacity motion-reduce:transition-none"
    class:opacity-70={!hasPrediction}
    aria-label="Passage probability spectrum"
    aria-live="polite"
>
    <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
            <p class="text-sm font-bold uppercase tracking-[0.2em] text-warm-brown-700">
                Passage probability
            </p>
            <h2 class="text-2xl font-black tracking-[-0.04em] text-parchment-900">
                {#if hasPrediction && spectrum}
                    {spectrum.displayText} roll-call passage probability
                {:else}
                    Spectrum pending
                {/if}
            </h2>
        </div>
        <p class="text-sm font-bold text-parchment-700">
            {#if hasPrediction && spectrum}
                {spectrum.label}
            {:else}
                {placeholderText}
            {/if}
        </p>
    </div>

    <div class="mt-7" aria-hidden={!hasPrediction}>
        <div class="mb-2 flex justify-between text-xs font-black uppercase tracking-[0.18em] text-parchment-600">
            <span>0%</span>
            <span>100%</span>
        </div>
        <div class="relative h-5 rounded-full bg-linear-to-r from-parchment-200 via-warm-brown-200 to-warm-brown-500 shadow-inner">
            {#if hasPrediction && spectrum}
                <div
                    class="absolute top-1/2 h-9 w-9 -translate-x-1/2 -translate-y-1/2 rounded-full border-4 border-white bg-parchment-900 shadow-lg shadow-warm-brown-700/25 transition-[left] duration-500 ease-out motion-reduce:transition-none"
                    style={`left: ${spectrum.markerPercent}%`}
                    aria-label={`${spectrum.displayText} passage probability`}
                ></div>
            {/if}
        </div>
        <div class="mt-3 grid grid-cols-3 text-sm font-black text-parchment-700">
            <span>Unlikely</span>
            <span class="text-center">Toss-up</span>
            <span class="text-right">Likely</span>
        </div>
    </div>
</section>
