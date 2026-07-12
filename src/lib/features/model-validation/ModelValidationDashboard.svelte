<script lang="ts">
    import ConfusionMatrixChart from "./ConfusionMatrixChart.svelte";
    import type { ModelArtifacts } from "$lib/model-runtime";
    import {
        formatCount,
        formatMetricPercent,
        getConfusionMatrixFromMetrics,
    } from "./modelValidation";

    type Props = {
        artifacts: ModelArtifacts;
    };

    let { artifacts }: Props = $props();

    const matrix = $derived(getConfusionMatrixFromMetrics(artifacts.modelMetrics));
    const metrics = $derived(artifacts.modelMetrics.metrics);
    const metricCards = $derived([
        { label: "Accuracy", value: formatMetricPercent(metrics.accuracy) },
        { label: "Precision", value: formatMetricPercent(metrics.precision) },
        { label: "Recall", value: formatMetricPercent(metrics.recall) },
        { label: "F1 score", value: formatMetricPercent(metrics.f1) },
        { label: "ROC AUC", value: formatMetricPercent(metrics.roc_auc) },
    ]);

    const trainingRows = $derived(
        typeof artifacts.modelMetrics.training_rows === "number"
            ? formatCount(artifacts.modelMetrics.training_rows)
            : "—",
    );
    const validationRows = $derived(
        typeof artifacts.modelMetrics.test_rows === "number"
            ? formatCount(artifacts.modelMetrics.test_rows)
            : "—",
    );
</script>

<svelte:head>
    <title>Model Validation · Congressional Chances</title>
    <meta
        name="description"
        content="Validation dashboard for the Congressional Chances roll-call passage model."
    />
</svelte:head>

<main
    class="min-h-screen bg-linear-to-br from-parchment-50 via-parchment-100 to-parchment-200 px-4 py-6 text-parchment-900 sm:px-6 lg:px-8"
>
    <section class="mx-auto grid max-w-6xl gap-5">
        <header
            class="rounded-[2rem] border border-white/70 bg-white/65 p-5 shadow-xl shadow-warm-brown-700/10 backdrop-blur"
        >
            <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                    <p class="text-xs font-black uppercase tracking-[0.28em] text-warm-brown-700">
                        Congressional Chances
                    </p>
                    <h1 class="mt-2 text-4xl font-black tracking-[-0.06em] sm:text-5xl">
                        Model validation
                    </h1>
                    <p class="mt-2 max-w-3xl text-sm leading-6 text-parchment-700">
                        Review the trained roll-call passage model on held-out validation data. The confusion matrix compares actual passage outcomes with predicted outcomes.
                    </p>
                </div>
                <a
                    class="w-fit rounded-full border border-warm-brown-500/25 bg-parchment-50 px-4 py-2 text-sm font-bold text-warm-brown-700 transition hover:bg-white"
                    href="/"
                >
                    Back to predictor
                </a>
            </div>
        </header>

        <section class="grid gap-3 sm:grid-cols-2 lg:grid-cols-7" aria-label="Validation scorecards">
            {#each metricCards as card}
                <article class="rounded-2xl border border-white/70 bg-white/75 px-4 py-3 shadow-lg shadow-warm-brown-700/5 lg:col-span-1">
                    <p class="text-xs font-black uppercase tracking-[0.16em] text-warm-brown-700">{card.label}</p>
                    <p class="mt-2 text-2xl font-black tracking-[-0.04em] text-parchment-900">{card.value}</p>
                </article>
            {/each}
            <article class="rounded-2xl border border-white/70 bg-white/75 px-4 py-3 shadow-lg shadow-warm-brown-700/5">
                <p class="text-xs font-black uppercase tracking-[0.16em] text-warm-brown-700">Training rows</p>
                <p class="mt-2 text-2xl font-black tracking-[-0.04em] text-parchment-900">{trainingRows}</p>
            </article>
            <article class="rounded-2xl border border-white/70 bg-white/75 px-4 py-3 shadow-lg shadow-warm-brown-700/5">
                <p class="text-xs font-black uppercase tracking-[0.16em] text-warm-brown-700">Validation rows</p>
                <p class="mt-2 text-2xl font-black tracking-[-0.04em] text-parchment-900">{validationRows}</p>
            </article>
        </section>

        {#if matrix}
            <ConfusionMatrixChart {matrix} />
        {:else}
            <section
                class="rounded-2xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900"
                role="alert"
            >
                This model artifact does not include confusion-matrix validation counts yet.
            </section>
        {/if}

    </section>
</main>
