<script lang="ts">
	type StatusCard = {
		label: string;
		value: string;
		detail: string;
	};

	let { cards }: { cards: StatusCard[] } = $props();
</script>

<div class="status-grid" aria-label="Model artifact status">
	{#each cards as card}
		<article>
			<span>{card.label}</span>
			<strong>{card.value}</strong>
			<p>{card.detail}</p>
		</article>
	{/each}
</div>

<style>
	.status-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 16px;
	}

	article {
		border: 1px solid rgb(148 163 184 / 0.2);
		border-radius: 24px;
		background: rgb(15 23 42 / 0.72);
		box-shadow: 0 24px 80px rgb(2 6 23 / 0.28);
		padding: 24px;
	}

	span {
		color: #94a3b8;
		font-size: 0.82rem;
	}

	strong {
		display: block;
		margin: 8px 0;
		font-size: 1.18rem;
	}

	p {
		margin: 0;
		color: #64748b;
	}
</style>
