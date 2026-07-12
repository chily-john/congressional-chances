<script lang="ts">
	import type { Snippet } from 'svelte';

	let { className = '', ariaLabel = undefined, children }: { className?: string; ariaLabel?: string; children?: Snippet } = $props();
</script>

<div class={`card ${className}`} aria-label={ariaLabel}>
	{@render children?.()}
</div>

<style>
	.card {
		margin-top: 18px;
		border: 1px solid rgb(148 163 184 / 0.2);
		border-radius: 24px;
		background: rgb(15 23 42 / 0.72);
		box-shadow: 0 24px 80px rgb(2 6 23 / 0.28);
		padding: 24px;
	}
</style>
