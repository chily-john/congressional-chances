<script lang="ts">
	import type { Snippet } from 'svelte';

	let { eyebrow, title, description, children }: { eyebrow: string; title: string; description: string; children?: Snippet } = $props();
</script>

<svelte:head>
	<title>{eyebrow}</title>
	<meta name="description" content={description} />
</svelte:head>

<section class="shell">
	<div class="hero">
		<p class="eyebrow">{eyebrow}</p>
		<h1>{title}</h1>
		<p class="lede">{description}</p>
	</div>
	{@render children?.()}
</section>

<style>
	:global(body) {
		margin: 0;
		font-family:
			Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
		background: #0f172a;
		color: #e2e8f0;
	}

	.shell {
		width: min(1120px, calc(100% - 32px));
		margin: 0 auto;
		padding: 64px 0;
	}

	.hero {
		max-width: 760px;
		margin-bottom: 32px;
	}

	.eyebrow {
		margin: 0 0 8px;
		color: #38bdf8;
		font-size: 0.78rem;
		font-weight: 800;
		letter-spacing: 0.12em;
		text-transform: uppercase;
	}

	h1,
	p {
		margin-top: 0;
	}

	h1 {
		margin-bottom: 16px;
		font-size: clamp(2.5rem, 8vw, 5.75rem);
		line-height: 0.92;
		letter-spacing: -0.07em;
	}

	.lede {
		color: #cbd5e1;
		font-size: 1.15rem;
		line-height: 1.7;
	}
</style>
