<script lang="ts">
    type Props = {
        voteQuestionTypes: readonly string[];
        policyAreas: readonly string[];
        voteQuestionType: string;
        policyArea: string;
        onVoteQuestionTypeChange: (voteQuestionType: string) => void;
        onPolicyAreaChange: (policyArea: string) => void;
    };

    let {
        voteQuestionTypes,
        policyAreas,
        voteQuestionType,
        policyArea,
        onVoteQuestionTypeChange,
        onPolicyAreaChange,
    }: Props = $props();
</script>

<section
    class="rounded-2xl bg-parchment-100/70 p-4"
    aria-labelledby="roll-call-context-controls"
>
    <h2
        id="roll-call-context-controls"
        class="text-base font-black text-warm-brown-700"
    >
        Bill / roll-call context
    </h2>
    <div class="mt-4 grid gap-4 sm:grid-cols-2">
        <label class="grid gap-2 text-sm font-bold text-parchment-700">
            <span>Vote question type</span>
            <select
                class="rounded-2xl border border-warm-brown-500/20 bg-parchment-50 px-4 py-3 text-parchment-900 outline-warm-brown-500"
                value={voteQuestionType}
                onchange={(event) => onVoteQuestionTypeChange(event.currentTarget.value)}
            >
                {#each voteQuestionTypes as option}<option value={option}>{option}</option>{/each}
            </select>
        </label>
        <label class="grid gap-2 text-sm font-bold text-parchment-700">
            <span>Policy area</span>
            <select
                class="rounded-2xl border border-warm-brown-500/20 bg-parchment-50 px-4 py-3 text-parchment-900 outline-warm-brown-500 w-full"
                value={policyArea}
                onchange={(event) => onPolicyAreaChange(event.currentTarget.value)}
            >
                {#each policyAreas as option}<option value={option}>{option}</option>{/each}
            </select>
        </label>
    </div>
</section>
