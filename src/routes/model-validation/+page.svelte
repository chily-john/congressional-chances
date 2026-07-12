<script lang="ts">
    import { ModelValidationDashboard } from "$lib/features/model-validation";
    import type { PageData } from "./$types";

    let { data }: { data: PageData } = $props();
</script>

<ModelValidationDashboard artifacts={data.artifacts} />
