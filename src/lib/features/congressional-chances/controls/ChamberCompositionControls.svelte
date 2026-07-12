<script lang="ts">
    import type { ModelArtifacts } from "$lib/model-runtime";
    import type {
        PredictionFormState,
        SeatCountField,
    } from "../prediction/predictionForm";

    type Props = {
        artifacts: ModelArtifacts;
        form: PredictionFormState;
        seatFields: readonly SeatCountField[];
        seatLabels: Record<SeatCountField, string>;
        getSeatFieldMax: (field: SeatCountField) => number;
        onChamberChange: (chamber: string) => void;
        onSeatEdit: (field: SeatCountField, input: HTMLInputElement) => void;
    };

    let {
        artifacts,
        form,
        seatFields,
        seatLabels,
        getSeatFieldMax,
        onChamberChange,
        onSeatEdit,
    }: Props = $props();
</script>

<section
    class="rounded-2xl bg-parchment-100/70 p-4"
    aria-labelledby="chamber-composition-controls"
>
    <h2
        id="chamber-composition-controls"
        class="text-base font-black text-warm-brown-700"
    >
        Chamber composition
    </h2>
    <div class="mt-4 grid gap-4 sm:grid-cols-2">
        <label class="grid gap-2 text-sm font-bold text-parchment-700">
            <span>Chamber</span>
            <select
                class="rounded-2xl border border-warm-brown-500/20 bg-parchment-50 px-4 py-3 text-parchment-900 outline-warm-brown-500"
                value={form.chamber}
                onchange={(event) => onChamberChange(event.currentTarget.value)}
            >
                {#each artifacts.categoryMaps.categories.chamber ?? [] as chamber}<option
                        value={chamber}>{chamber}</option
                    >{/each}
            </select>
        </label>
        {#each seatFields as field}
            <label class="grid gap-2 text-sm font-bold text-parchment-700">
                <span>{seatLabels[field]} seats</span>
                <input
                    class="rounded-2xl border border-warm-brown-500/20 bg-parchment-50 px-4 py-3 text-parchment-900 outline-warm-brown-500"
                    type="number"
                    min="0"
                    max={getSeatFieldMax(field)}
                    value={form[field]}
                    oninput={(event) => onSeatEdit(field, event.currentTarget)}
                />
            </label>
        {/each}
    </div>
</section>
