<script lang="ts">
    import { browser } from "$app/environment";
    import { onDestroy, type Snippet } from "svelte";
    import type Highcharts from "highcharts";
    import {
        buildChamberChartAriaLabel,
        buildChamberChartSeriesData,
        buildChamberChartSummary,
        buildChamberHighchartsOptions,
        chamberChartColors,
        type ChamberSeatParty,
    } from "./chamberChart";
    import { chamberSeatLimits } from "$lib/domain/congress";

    type Props = {
        chamber: keyof typeof chamberSeatLimits;
        democraticSeats: number;
        republicanSeats: number;
        independentSeats?: number;
        democraticIdeologyMean?: number;
        democraticIdeologyMedian?: number;
        republicanIdeologyMean?: number;
        republicanIdeologyMedian?: number;
        polarizationLabel?: string;
        leftControls?: Snippet;
        rightControls?: Snippet;
    };

    let {
        chamber,
        democraticSeats,
        republicanSeats,
        independentSeats = 0,
        democraticIdeologyMean = 0,
        democraticIdeologyMedian = 0,
        republicanIdeologyMean = 0,
        republicanIdeologyMedian = 0,
        polarizationLabel,
        leftControls,
        rightControls,
    }: Props = $props();

    const seriesData = $derived(
        buildChamberChartSeriesData({
            chamber,
            democraticSeats,
            republicanSeats,
            independentSeats,
            democraticIdeologyMean,
            democraticIdeologyMedian,
            republicanIdeologyMean,
            republicanIdeologyMedian,
        }),
    );
    const summary = $derived(
        buildChamberChartSummary({
            chamber,
            democraticSeats,
            republicanSeats,
            independentSeats,
        }),
    );
    const chamberLabel = $derived(chamber === "house" ? "House" : "Senate");
    const ariaLabel = $derived(buildChamberChartAriaLabel(chamberLabel, summary));

    const legendItems: { party: Exclude<ChamberSeatParty, "gap">; label: string }[] = [
        { party: "democratic", label: "Democratic" },
        { party: "independent", label: "Independent" },
        { party: "republican", label: "Republican" },
        { party: "vacancy", label: "Vacancy/unknown" },
    ];

    const colorByParty = $derived({
        ...chamberChartColors,
        ...(Object.fromEntries(
            seriesData
                .filter((row) => row.party !== "gap")
                .map((row) => [row.party, row.color]),
        ) as Partial<Record<Exclude<ChamberSeatParty, "gap">, string>>),
    });

    let chartContainer: HTMLDivElement | undefined;
    let chart: Highcharts.Chart | undefined;
    let loadToken = 0;

    $effect(() => {
        const container = chartContainer;
        const options = buildChamberHighchartsOptions(seriesData);

        if (!browser || !container) return;

        const currentToken = ++loadToken;

        void (async () => {
            const Highcharts = (await import("highcharts")).default;
            await import("highcharts/modules/item-series");

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
    <div
        class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"
    >
        <div>
            <p
                class="text-xs font-black uppercase tracking-[0.24em] text-warm-brown-700"
            >
                Chamber balance
            </p>
            <h2
                class="mt-1 text-2xl font-black tracking-[-0.04em] text-parchment-900"
            >
                {chamberLabel} chamber view
            </h2>
        </div>
        <div class="flex flex-wrap gap-2 sm:justify-end">
            {#if polarizationLabel}
                <p
                    class="rounded-full bg-parchment-100 px-4 py-2 text-sm font-black text-parchment-700"
                >
                    {polarizationLabel}
                </p>
            {/if}
            <p
                class="rounded-full bg-parchment-100 px-4 py-2 text-sm font-black text-parchment-700"
            >
                {summary.capacity} seats
            </p>
        </div>
    </div>

    <div
        class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-[minmax(10rem,12rem)_minmax(0,1fr)_minmax(10rem,12rem)] lg:items-center"
    >
        {#if leftControls}
            <div class="order-2 sm:col-span-1 lg:order-1 lg:col-span-1">
                {@render leftControls()}
            </div>
        {/if}

        <div
            class="order-1 flex h-48 items-end justify-center overflow-hidden rounded-3xl bg-parchment-50 px-1 py-3 sm:col-span-2 sm:block sm:h-auto sm:px-2 lg:order-2 lg:col-span-1"
            role="img"
            aria-label={ariaLabel}
        >
            <div
                class="h-60 w-[150%] shrink-0 origin-bottom scale-[0.67] sm:h-64 sm:w-full sm:scale-100"
                bind:this={chartContainer}
                aria-hidden="true"
            ></div>
        </div>

        {#if rightControls}
            <div class="order-3 sm:col-span-1 lg:col-span-1">
                {@render rightControls()}
            </div>
        {/if}
    </div>

    <ul
        class="mt-4 grid gap-2 text-sm font-bold text-parchment-700 sm:grid-cols-4"
    >
        {#each legendItems as item}
            {@const isMajorityParty = summary.majority.party === item.party && summary.majority.margin > 0}
            <li
                class="flex items-center gap-2 rounded-2xl border bg-parchment-100/80 px-3 py-2"
                style={`border-color: ${isMajorityParty ? colorByParty[item.party] : "rgba(127, 77, 34, 0.08)"}`}
            >
                <span
                    class="size-3 rounded-full"
                    style={`background-color: ${colorByParty[item.party]}`}
                    aria-hidden="true"
                ></span>
                <span
                    >{item.label}: {summary.groups[item.party].count} ({summary
                        .groups[item.party].percentageLabel}){#if isMajorityParty}<span
                            class="ml-1 text-xs font-black"
                            style={`color: ${colorByParty[item.party]}`}
                            >+{summary.majority.margin}</span
                        >{/if}</span
                >
            </li>
        {/each}
    </ul>
</section>
