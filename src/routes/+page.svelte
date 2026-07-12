<script lang="ts">
    import CongressionalChances from "$lib/features/congressional-chances/CongressionalChances.svelte";
    import type { PageData } from "./$types";

    let { data }: { data: PageData } = $props();
</script>

<CongressionalChances artifacts={data.artifacts} />
