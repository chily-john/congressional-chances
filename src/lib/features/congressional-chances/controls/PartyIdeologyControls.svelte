<script lang="ts">
    import type {
        IdeologyField,
        PredictionFormState,
    } from "../prediction/predictionForm";

    type IdeologyControlField = {
        field: IdeologyField;
        label: string;
    };

    type Props = {
        title: string;
        titleId: string;
        titleClass: string;
        inputClass: string;
        fields: readonly IdeologyControlField[];
        form: PredictionFormState;
        disabled: boolean;
        getMin: (field: IdeologyField) => number;
        getMax: (field: IdeologyField) => number;
        onEdit: (field: IdeologyField, input: HTMLInputElement) => void;
    };

    let {
        title,
        titleId,
        titleClass,
        inputClass,
        fields,
        form,
        disabled,
        getMin,
        getMax,
        onEdit,
    }: Props = $props();
</script>

<section
    class="rounded-3xl border border-warm-brown-500/15 bg-white/70 p-4 shadow-sm"
    class:opacity-60={disabled}
    aria-labelledby={titleId}
>
    <h3 id={titleId} class={titleClass}>
        {title}
    </h3>
    <div class="mt-3 grid gap-3">
        {#each fields as control}
            <label class="grid gap-2 text-sm font-bold text-parchment-700">
                <span>{control.label}</span>
                <input
                    class={inputClass}
                    type="number"
                    min={getMin(control.field)}
                    max={getMax(control.field)}
                    step="0.05"
                    value={form[control.field]}
                    {disabled}
                    oninput={(event) => onEdit(control.field, event.currentTarget)}
                />
            </label>
        {/each}
    </div>
</section>
