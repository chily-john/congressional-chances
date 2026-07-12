<script lang="ts">
    import { browser } from "$app/environment";
    import { onDestroy } from "svelte";
    import type Highcharts from "highcharts";
    import type { ConfusionMatrixCounts } from "$lib/model-runtime";
    import {
        buildConfusionMatrixAriaLabel,
        buildConfusionMatrixChartData,
        buildConfusionMatrixHighchartsOptions,
        buildConfusionMatrixSummary,
        formatCount,
        formatPercent,
    } from "./modelValidation";

    type Props = {
        matrix: ConfusionMatrixCounts;
    };

    let { matrix }: Props = $props();

    const summary = $derived(buildConfusionMatrixSummary(matrix));
    const cells = $derived(buildConfusionMatrixChartData(matrix));
    const ariaLabel = $derived(buildConfusionMatrixAriaLabel(matrix));

    let chartContainer: HTMLDivElement | undefined;
    let chart: Highcharts.Chart | undefined;
    let loadToken = 0;

    $effect(() => {
        const container = chartContainer;
        const options = buildConfusionMatrixHighchartsOptions(matrix);

        if (!browser || !container) return;

        const currentToken = ++loadToken;

        void (async () => {
            const Highcharts = (await import("highcharts")).default;
            await import("highcharts/modules/heatmap");

            if (currentToken !== loadToken) return;

            if (chart) {
                chart.update(options, true, true);
            } else {
                chart = Highcharts.chart(container, options);
            }
        })();
    });

    onDestroy(() => {
        loadToken += 1;
        chart?.destroy();
        chart = undefined;
    });
</script>

<section
    class="rounded-[2rem] border border-white/70 bg-white/75 p-5 shadow-xl shadow-warm-brown-700/10"
    aria-label={ariaLabel}
>
    <div class="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
            <p class="text-xs font-black uppercase tracking-[0.24em] text-warm-brown-700">
                Model validation
            </p>
            <h2 class="mt-1 text-2xl font-black tracking-[-0.04em] text-parchment-900">
                Confusion matrix
            </h2>
            <p class="mt-2 max-w-2xl text-sm leading-6 text-parchment-700">
                Holdout roll calls grouped by actual passage outcome and the model's predicted class.
            </p>
        </div>
        <div class="grid gap-1 rounded-2xl bg-parchment-100 px-4 py-3 text-sm font-black text-parchment-700">
            <span>{formatCount(summary.correct)} correct</span>
            <span>{formatPercent(summary.accuracy)} accuracy</span>
        </div>
    </div>

    <div
        class="mt-4 overflow-hidden rounded-3xl bg-parchment-50 px-2 py-4"
        role="img"
        aria-label={ariaLabel}
    >
        <div class="h-80" bind:this={chartContainer} aria-hidden="true"></div>
    </div>

    <div class="mt-4 grid gap-3 lg:grid-cols-[1fr_14rem]">
        <div class="overflow-hidden rounded-2xl border border-warm-brown-500/20 bg-white/70">
            <table class="w-full border-collapse text-left text-sm text-parchment-700">
                <caption class="sr-only">{ariaLabel}</caption>
                <thead class="bg-parchment-100/80 text-xs uppercase tracking-[0.16em] text-warm-brown-700">
                    <tr>
                        <th class="px-4 py-3 font-black" scope="col">Outcome</th>
                        <th class="px-4 py-3 font-black" scope="col">Actual</th>
                        <th class="px-4 py-3 font-black" scope="col">Predicted</th>
                        <th class="px-4 py-3 text-right font-black" scope="col">Count</th>
                        <th class="px-4 py-3 text-right font-black" scope="col">Share</th>
                    </tr>
                </thead>
                <tbody>
                    {#each cells as cell}
                        <tr class="border-t border-warm-brown-500/10">
                            <th class="px-4 py-3 font-black text-parchment-900" scope="row">{cell.label}</th>
                            <td class="px-4 py-3 capitalize">{cell.actual}</td>
                            <td class="px-4 py-3 capitalize">{cell.predicted}</td>
                            <td class="px-4 py-3 text-right font-bold">{formatCount(cell.count)}</td>
                            <td class="px-4 py-3 text-right font-bold">{formatPercent(cell.rate)}</td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>

        <dl class="grid gap-3 text-sm">
            <div class="rounded-2xl bg-parchment-100/80 px-4 py-3">
                <dt class="font-black text-warm-brown-700">Validation rows</dt>
                <dd class="mt-1 text-2xl font-black text-parchment-900">{formatCount(summary.total)}</dd>
            </div>
            <div class="rounded-2xl bg-parchment-100/80 px-4 py-3">
                <dt class="font-black text-warm-brown-700">Errors</dt>
                <dd class="mt-1 text-2xl font-black text-parchment-900">{formatCount(summary.incorrect)}</dd>
            </div>
        </dl>
    </div>
</section>
