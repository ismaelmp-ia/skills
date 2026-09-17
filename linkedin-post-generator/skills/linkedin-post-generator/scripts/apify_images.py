#!/usr/bin/env python3
"""
Corre el actor hooli/google-images-scraper via Apify CLI y devuelve
la lista de resultados (JSON) para una query dada.

Requiere: apify-cli instalado y logueado (`apify login`).

Uso:
    python3 apify_images.py "Nvidia logo" [max_results]
"""
import json
import subprocess
import sys

DEFAULT_MAX_RESULTS_PER_QUERY = 8


def fetch_images(query: str, max_results: int = DEFAULT_MAX_RESULTS_PER_QUERY) -> list[dict]:
    payload = json.dumps({"queries": [query], "maxResultsPerQuery": max_results})
    result = subprocess.run(
        ["apify", "call", "hooli/google-images-scraper", "--silent", "--output-dataset"],
        input=payload,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"apify call falló: {result.stderr.strip()}")
    return json.loads(result.stdout)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 apify_images.py \"<query>\" [max_results]", file=sys.stderr)
        sys.exit(1)

    q = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_MAX_RESULTS_PER_QUERY

    images = fetch_images(q, n)
    print(json.dumps(images, indent=2, ensure_ascii=False))
