# Congressional Chances

SvelteKit app with a build-time Python ML pipeline for **roll-call passage prediction**. It predicts whether a roll call passes, not whether a bill becomes law.

## Prerequisites

Install these before opening the project on a new computer:

- **Git**
- **Node.js** `20.19+` or `22.12+`
- **pnpm** `11.0.8`
  - If pnpm is not available after installing Node, run:
    ```sh
    corepack enable
    corepack prepare pnpm@11.0.8 --activate
    ```
- **Python 3** with `pip`
  - The project scripts expect Python to be available as `python` from the terminal.
  - On Windows, check **Add Python to PATH** during Python installation.

## One-command local start

From the project root:

```sh
pnpm run run:dev
```

This command:

1. installs JavaScript dependencies,
2. installs Python dependencies from `requirements.txt`,
3. downloads/prepares Voteview data,
4. trains and exports the model artifacts,
5. builds the SvelteKit app, and
6. starts the local dev server.

The dev server will print the local URL, usually `http://localhost:5173`.

## Useful commands

```sh
pnpm setup       # install JavaScript and Python dependencies
pnpm setup:py    # install only Python dependencies
pnpm build:ml    # install Python dependencies, then rebuild ML artifacts
pnpm build       # build frontend only
pnpm build:prod  # rebuild ML artifacts, then build frontend
pnpm check       # run Svelte/TypeScript validation
pnpm dev         # start dev server without rebuilding ML artifacts
```

`pnpm build:ml` performs real Voteview downloads and may take longer than a normal frontend build.

## Project notes

- ML feature contract: `ml/config/features.yaml`
- Python pipeline stages: `ml/pipeline/stages/`
- Canonical browser model artifacts: `ml/browser-artifacts/`
- Browser-served model artifacts: `static/model/`
- Main Svelte source: `src/`

## Deployment

The app is configured for SSR on Vercel with `@sveltejs/adapter-vercel` and `vercel.json`.
Routine deployments serve the committed browser model artifacts from `static/model/`.
