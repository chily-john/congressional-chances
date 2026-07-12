from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RAW_DATA_DIR = ROOT / "ml" / "pipeline" / "generated-data" / "raw"

DOWNLOADS = {
    "HSall_rollcalls.json": "https://voteview.com/static/data/out/rollcalls/HSall_rollcalls.json",
    "HSall_parties.csv": "https://voteview.com/static/data/out/parties/HSall_parties.csv",
}

def download_file(url: str, destination: Path, timeout: int) -> None:
    """Download url to destination, replacing any existing file atomically."""
    import requests

    temporary_destination = destination.with_suffix(f"{destination.suffix}.tmp")

    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        with temporary_destination.open("wb") as output_file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output_file.write(chunk)

    temporary_destination.replace(destination)

def main() -> int:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    for filename, url in DOWNLOADS.items():
        destination = RAW_DATA_DIR / filename
        print(f"Downloading {url} -> {destination}")
        download_file(url, destination, 60)

    print(f"Downloaded {len(DOWNLOADS)} raw Voteview files to {RAW_DATA_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
