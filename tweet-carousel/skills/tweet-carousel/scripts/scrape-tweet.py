#!/usr/bin/env python3
"""
scrape-tweet.py — Scraping de tweet para el pipeline de carruseles.

Uso:
    py scripts/scrape-tweet.py --url "https://x.com/user/status/123456789"

Salida:
    Texto formateado del tweet listo para que Claude escriba los slides.
"""

import os, sys, json, subprocess, argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


def find_xreach() -> str:
    import shutil
    found = shutil.which("xreach")
    if found:
        return found
    npm_path = Path(os.environ.get("APPDATA", "")) / "npm" / "xreach.cmd"
    if npm_path.exists():
        return str(npm_path)
    return "xreach"


def scrape(url: str) -> None:
    auth_token = os.environ.get("TWITTER_AUTH_TOKEN")
    ct0        = os.environ.get("TWITTER_CT0")
    xreach     = find_xreach()

    if not auth_token or not ct0:
        print("❌ Faltan cookies en .env — TWITTER_AUTH_TOKEN y TWITTER_CT0 son requeridos.")
        sys.exit(1)

    # Intentar hilo completo primero
    for mode in ("thread", "tweet"):
        cmd = [xreach, "--auth-token", auth_token, "--ct0", ct0, mode, url]
        print(f"🔍 Intentando scraping ({mode}): {url}", flush=True)
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if r.returncode == 0 and r.stdout.strip():
                print("\n" + "="*60)
                print("CONTENIDO DEL TWEET")
                print("="*60)
                print(r.stdout.strip())
                print("="*60 + "\n")
                return
            else:
                err = r.stderr.strip() or r.stdout.strip()
                print(f"⚠️  Modo {mode} falló: {err}", flush=True)
        except FileNotFoundError:
            print("❌ xreach-cli no encontrado. Instalar con: npm install -g xreach-cli")
            sys.exit(1)
        except subprocess.TimeoutExpired:
            print(f"⚠️  Timeout en modo {mode}. Intentando siguiente...")

    print("❌ No se pudo obtener el tweet.")
    print("   → Verificá que las cookies en .env estén actualizadas (TWITTER_AUTH_TOKEN y TWITTER_CT0)")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Scraping de tweet para el pipeline de carruseles")
    parser.add_argument("--url", required=True, help="URL del tweet a scrapear")
    args = parser.parse_args()
    scrape(args.url)


if __name__ == "__main__":
    main()
