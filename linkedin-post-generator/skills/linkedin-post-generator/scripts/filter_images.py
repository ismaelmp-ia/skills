#!/usr/bin/env python3
"""
Filtro mecánico de candidatos de imagen: dimensión mínima + contenido
real (magic bytes) + descarte de screenshots/UI + orden por
confiabilidad de fuente + marcado (no descarte) de posibles duplicados
de color para que Claude decida en runtime.

El filtro de CALIDAD VISUAL (relevancia, nitidez, watermarks, UI de
reproductor, nitidez facial si hay persona) NO se hace acá — eso lo
resuelve Claude directamente mirando las imágenes descargadas con su
visión, durante la ejecución del Skill. Lo mismo aplica a decidir si dos
candidatos con similar_color_to alto son la misma foto o no (ver nota de
calibración junto a DUPLICATE_SIMILARITY_THRESHOLD): ningún método
mecánico liviano probado resolvió eso de forma confiable.

Si ninguna imagen sobrevive a estos filtros, este script NO inventa una
query más amplia por su cuenta (probado: truncar palabras a ciegas
rompe la sintaxis, ej. "Lionel Messi Copa del Mundo" -> "Lionel Messi
Copa del"). Esa decisión la toma Claude en runtime, con criterio sobre
el tema real, y vuelve a llamar a este script con la query reformulada
o simplemente reintenta la misma query (los resultados de Apify no son
deterministas: la misma query puede traer imágenes distintas en cada
llamada).

Uso:
    python3 filter_images.py "<query>" [max_results]
Imprime JSON: {"query": ..., "candidates": [...], "discarded_by_dimension": N,
               "discarded_invalid_content": N}
"""
import json
import sys
from io import BytesIO

import numpy as np
import requests
from PIL import Image, UnidentifiedImageError

from apify_images import fetch_images, DEFAULT_MAX_RESULTS_PER_QUERY

MIN_IMAGE_DIMENSION = 800

# Fuentes de alto ruido: frecuentemente devuelven HTML de bloqueo anti-bot
# en vez de la imagen, o el contenido no coincide con lo que muestra el
# thumbnail (screenshots ajenos, memes, capturas de otros chats/apps).
# No se descartan de plano -a veces son la única fuente- pero se
# deprioritizan: van al final de la lista de candidatos.
LOW_TRUST_DOMAINS = (
    "reddit.com",
    "instagram.com",
    "facebook.com",
    "fbsbx.com",
    "pinterest.",
    "x.com",
    "twitter.com",
    "tiktok.com",
)


def passes_dimension(img: dict, min_dim: int = MIN_IMAGE_DIMENSION) -> bool:
    return min(img.get("imageWidth", 0), img.get("imageHeight", 0)) >= min_dim


def is_low_trust(origin: str) -> bool:
    origin = (origin or "").lower()
    return any(domain in origin for domain in LOW_TRUST_DOMAINS)


# Umbrales calibrados a mano contra fase2_candidates/messi (fotos reales)
# vs. fase2_candidates/claudecode + messi/wc_0 (screenshots/UI). Ver notas
# de calibración en el historial del skill: unique_color_ratio separó
# limpio 0.021-0.033 (fotos) de 0.001-0.007 (screenshots); flat_run_ratio
# separó 0.497-0.796 (fotos, salvo casos límite) de 0.796-0.915 (screenshots).
UNIQUE_COLOR_RATIO_THRESHOLD = 0.012
FLAT_RUN_RATIO_THRESHOLD = 0.75

# Histograma de color (intersección) entre candidatos del mismo query.
#
# CALIBRACIÓN Y LIMITACIÓN CONOCIDA (no auto-descartar por esto, ver
# dedupe_near_duplicates): se probaron 3 métodos livianos para decidir
# "misma foto" automáticamente -umbral fijo, umbral relativo (z-score
# dentro del propio query), y color+estructura (correlación sobre grises
# 32x32)- y ninguno separó de forma confiable el duplicado real conocido
# (Messi 1.jpg<->4.jpg, mismo instante/jugada, confirmado a ojo) de falsos
# positivos con fondo/iluminación compartida pero foto distinta (ej. dos
# fotos de Jensen Huang en el mismo keynote, mismo fondo negro, similitud
# de color 0.876 pero pose/prop distintos). El z-score del falso positivo
# (1.94) fue más alto que el del duplicado real (1.89); la correlación
# estructural del duplicado real (0.095) fue más baja que la de pares
# no relacionados (hasta 0.251). Conclusión: un recorte/zoom distinto de
# la MISMA jugada de prensa no es un problema de "mismo archivo" que un
# descriptor mecánico pueda resolver -es juicio semántico, igual que la
# calidad visual (ver docstring del módulo). Por eso este umbral solo se
# usa para ANOTAR candidatos parecidos, nunca para descartar solo.
DUPLICATE_SIMILARITY_THRESHOLD = 0.5


def _screenshot_signals(img: Image.Image) -> dict:
    """Señales mecánicas de contenido no-fotográfico (screenshot/UI),
    calculadas sobre el contenido real de píxeles -nunca sobre metadata
    o extensión de archivo.

    - unique_color_ratio: diversidad de color tras cuantizar a 16 niveles
      por canal. Las fotos tienen ruido de sensor y degradados continuos
      -> muchos colores distintos. Las UI/screenshots usan paletas planas
      repetidas (fondos sólidos, barras, texto) -> pocos colores distintos.
    - flat_run_ratio: fracción de píxeles cuyo vecino horizontal es
      prácticamente idéntico (diferencia de luminancia < 2). El texto y
      los bloques de UI generan grandes zonas planas; las fotos casi
      nunca tienen dos píxeles adyacentes exactamente iguales.
    """
    thumb = img.copy()
    thumb.thumbnail((512, 512))
    arr = np.asarray(thumb.convert("RGB")).astype(np.int16)
    gray = arr.mean(axis=2)

    quantized = (arr >> 4).reshape(-1, 3)
    sample = quantized[::7] if len(quantized) > 7 else quantized
    unique_ratio = len(set(map(tuple, sample))) / len(sample)

    diffs_h = np.abs(np.diff(gray, axis=1))
    flat_ratio = float((diffs_h < 2).mean())

    return {"unique_color_ratio": unique_ratio, "flat_run_ratio": flat_ratio}


def is_screenshot_or_ui(img: Image.Image) -> bool:
    """True si el contenido real de la imagen matchea el patrón mecánico
    de screenshot/UI (texto denso, barras de navegador/reproductor,
    pantallas de error/bloqueo): paleta de color pobre + grandes zonas
    planas. Ambas señales deben coincidir para descartar -reduce falsos
    positivos contra fotos con fondos muy uniformes."""
    signals = _screenshot_signals(img)
    return (
        signals["unique_color_ratio"] < UNIQUE_COLOR_RATIO_THRESHOLD
        and signals["flat_run_ratio"] > FLAT_RUN_RATIO_THRESHOLD
    )


def color_histogram(img: Image.Image, bins: int = 8) -> np.ndarray:
    """Histograma de color 3D normalizado (bins**3 buckets), usado como
    descriptor liviano de similitud entre candidatos del mismo query.
    No depende de extensión/metadata, solo de píxeles reales."""
    thumb = img.copy()
    thumb.thumbnail((256, 256))
    arr = np.asarray(thumb.convert("RGB")).astype(np.float32) / 256.0
    idx = np.clip((arr * bins).astype(np.int32), 0, bins - 1)
    flat_idx = idx[..., 0] * bins * bins + idx[..., 1] * bins + idx[..., 2]
    hist = np.bincount(flat_idx.flatten(), minlength=bins**3).astype(np.float64)
    return hist / hist.sum()


def _histogram_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Intersección de histogramas: 1.0 = idénticos, 0.0 = sin overlap."""
    return float(np.minimum(a, b).sum())


def dedupe_near_duplicates(candidates: list) -> tuple:
    """NO descarta automáticamente -ver la nota de calibración junto a
    DUPLICATE_SIMILARITY_THRESHOLD: ningún método liviano probado separó
    de forma confiable "misma foto" de "mismo tema/fondo/iluminación".

    En cambio anota cada candidato con "similar_color_to": la lista de
    otros candidatos del mismo query con similitud de color alta
    (imageUrl + similarity), para que Claude decida en runtime mirando
    las imágenes -mismo patrón que ya usan para calidad visual.

    Cada dict en `candidates` debe tener la key temporal "_hist" (ver
    color_histogram); se elimina del output. Devuelve (candidates,
    cantidad_de_pares_marcados).
    """
    for c in candidates:
        c["similar_color_to"] = []

    flagged_pairs = 0
    n = len(candidates)
    for i in range(n):
        for j in range(i + 1, n):
            sim = _histogram_similarity(candidates[i]["_hist"], candidates[j]["_hist"])
            if sim < DUPLICATE_SIMILARITY_THRESHOLD:
                continue
            flagged_pairs += 1
            candidates[i]["similar_color_to"].append(
                {"imageUrl": candidates[j]["imageUrl"], "similarity": round(sim, 3)}
            )
            candidates[j]["similar_color_to"].append(
                {"imageUrl": candidates[i]["imageUrl"], "similarity": round(sim, 3)}
            )

    for c in candidates:
        c.pop("_hist", None)
    return candidates, flagged_pairs


def is_real_image(url: str) -> bool:
    """Descarga y verifica que el contenido sea una imagen real (no HTML
    de bloqueo, no página de error) chequeando los magic bytes con PIL."""
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        Image.open(BytesIO(resp.content)).verify()
        return True
    except (requests.RequestException, UnidentifiedImageError, OSError):
        return False


def _fetch_content(url: str):
    """Descarga y abre la imagen para los chequeos de contenido real
    (screenshot/UI + descriptor de dedup). Independiente del fetch que
    hace is_real_image() -no se toca esa función-, así que implica una
    segunda descarga solo para candidatos que ya pasaron ese filtro."""
    resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    return Image.open(BytesIO(resp.content)).convert("RGB")


def fetch_and_filter(query: str, max_results: int = DEFAULT_MAX_RESULTS_PER_QUERY) -> dict:
    images = fetch_images(query, max_results)
    by_dimension = [img for img in images if passes_dimension(img)]

    valid = []
    invalid_count = 0
    discarded_screenshot = 0
    for img in by_dimension:
        if not is_real_image(img["imageUrl"]):
            invalid_count += 1
            continue

        try:
            pil_img = _fetch_content(img["imageUrl"])
        except (requests.RequestException, UnidentifiedImageError, OSError):
            invalid_count += 1
            continue

        if is_screenshot_or_ui(pil_img):
            discarded_screenshot += 1
            continue

        img["low_trust_source"] = is_low_trust(img.get("origin"))
        img["_hist"] = color_histogram(pil_img)
        valid.append(img)

    valid, flagged_similar_color_pairs = dedupe_near_duplicates(valid)

    # confiables primero, de alto ruido al final
    valid.sort(key=lambda img: img["low_trust_source"])

    return {
        "query": query,
        "total_fetched": len(images),
        "candidates": valid,
        "discarded_by_dimension": len(images) - len(by_dimension),
        "discarded_invalid_content": invalid_count,
        "discarded_screenshot_or_ui": discarded_screenshot,
        "flagged_similar_color_pairs": flagged_similar_color_pairs,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 filter_images.py \"<query>\" [max_results]", file=sys.stderr)
        sys.exit(1)

    q = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_MAX_RESULTS_PER_QUERY

    result = fetch_and_filter(q, n)
    print(json.dumps(result, indent=2, ensure_ascii=False))
