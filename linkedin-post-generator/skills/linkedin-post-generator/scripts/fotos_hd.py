#!/usr/bin/env python3
"""
Paso de calidad de fotos: toma los candidatos que ya pasaron
filter_images.py, intenta conseguir la versión en máxima resolución de
cada uno, la descarga y mide cuánto habría que AGRANDARLA para cada uso.

Por qué existe: el post del 15/09/2026 salió pixelado. La causa no era
el diseño sino la foto: filter_images.py acepta desde 800 px de lado
corto y el recorte a sangre completa 1080x1350 de una foto horizontal
1600x900 deja 720x900 píxeles reales, agrandados 1,5x. Además
`imageWidth/imageHeight` de Apify es lo que declara Google, no siempre
lo que se descarga -acá se mide sobre los píxeles reales.

No toca las funciones validadas de filter_images.py (regla del skill):
es un paso nuevo encima de su salida.

Uso:
    /usr/bin/python3 fotos_hd.py <candidatos.json> <carpeta_descargas>
      (candidatos.json = salida de filter_images.py)

Imprime JSON con, por candidato: archivo local, tamaño real, escala para
sangre completa, escala para portada con foto al 60%, nitidez y veredicto.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from io import BytesIO
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import numpy as np
import requests
from PIL import Image, ImageFilter

W, H = 1080, 1350
FOTO_PORTADA_H = round(H * 0.60)

# Escala máxima aceptable. 1.0 = píxel real por píxel del post.
# Por encima de ~1.15 la piel y los bordes empiezan a verse blandos en
# pantallas de celular de alta densidad, que es donde se mira LinkedIn.
ESCALA_MAX = 1.15

# Parámetros de URL que suelen achicar la imagen servida por CDNs de medios.
PARAMS_TAMANO = {"w", "h", "width", "height", "resize", "fit", "crop", "quality", "q", "dpr", "size", "s", "auto"}

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/126 Safari/537.36"}


def variantes_url(url: str) -> list[str]:
    """Versiones candidatas en mayor resolución de la misma foto, de más
    prometedora a menos. Siempre incluye la original al final."""
    variantes: list[str] = []

    # Wikimedia: /thumb/a/ab/Archivo.jpg/960px-Archivo.jpg -> original completo
    m = re.match(r"(https?://upload\.wikimedia\.org/wikipedia/[^/]+)/thumb/(.+?)/[^/]+$", url)
    if not m:
        m = re.match(r"https?://thumb\.wikimedia\.org/wikipedia/([^/]+)/thumb/(.+?)/[^/]+$", url)
        if m:
            variantes.append(f"https://upload.wikimedia.org/wikipedia/{m.group(1)}/{m.group(2)}")
    else:
        variantes.append(f"{m.group(1)}/{m.group(2)}")

    # CDNs con parámetros de tamaño en la query: probar sin ellos
    p = urlparse(url)
    if p.query:
        limpios = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k.lower() not in PARAMS_TAMANO]
        sin_tamano = urlunparse(p._replace(query=urlencode(limpios)))
        if sin_tamano != url:
            variantes.append(sin_tamano)

    # Sufijos de tamaño en el nombre: foto-1024x683.jpg (WordPress) -> foto.jpg
    sin_sufijo = re.sub(r"-\d{2,4}x\d{2,4}(\.\w{3,4})(\?|$)", r"\1\2", url)
    if sin_sufijo != url:
        variantes.append(sin_sufijo)

    variantes.append(url)
    vistos, unicas = set(), []
    for v in variantes:
        if v not in vistos:
            vistos.add(v)
            unicas.append(v)
    return unicas


def descargar(url: str) -> Image.Image | None:
    try:
        r = requests.get(url, timeout=30, headers=UA)
        r.raise_for_status()
        im = Image.open(BytesIO(r.content))
        im.load()
        return im.convert("RGB")
    except Exception:
        return None


def escala_para(ancho: int, alto: int, area_w: int, area_h: int) -> float:
    """Cuánto hay que agrandar la foto para cubrir el área (cover)."""
    return max(area_w / ancho, area_h / alto)


def nitidez(im: Image.Image) -> float:
    """Varianza del borde (Laplaciano) medida a la escala en que se va a
    ver. Informativa, no veredicto: una foto con fondo desenfocado a
    propósito da bajo aunque la cara esté perfecta. Sirve para ordenar y
    para mirar dos veces las más bajas."""
    t = im.copy()
    t.thumbnail((W, H * 2))
    gris = t.convert("L").filter(ImageFilter.FIND_EDGES)
    return round(float(np.asarray(gris, dtype=np.float32).var()), 1)


def procesar(candidatos: list[dict], carpeta: Path) -> list[dict]:
    carpeta.mkdir(parents=True, exist_ok=True)
    salida = []
    for c in candidatos:
        mejor, mejor_url = None, None
        for v in variantes_url(c["imageUrl"]):
            im = descargar(v)
            if im and (mejor is None or im.width * im.height > mejor.width * mejor.height):
                mejor, mejor_url = im, v
        if mejor is None:
            continue
        nombre = hashlib.md5(mejor_url.encode()).hexdigest()[:10] + ".jpg"
        ruta = carpeta / nombre
        mejor.save(ruta, quality=95)

        e_sangre = escala_para(mejor.width, mejor.height, W, H)
        e_portada = escala_para(mejor.width, mejor.height, W, FOTO_PORTADA_H)
        if e_sangre <= ESCALA_MAX:
            veredicto = "sirve a sangre completa"
        elif e_portada <= ESCALA_MAX:
            veredicto = "sirve solo como portada con foto al 60%"
        else:
            veredicto = "chica: se va a ver pixelada, no usar"

        salida.append({
            "archivo": str(ruta),
            "url_usada": mejor_url,
            "mejorada": mejor_url != c["imageUrl"],
            "tamano_real": [mejor.width, mejor.height],
            "escala_sangre": round(e_sangre, 2),
            "escala_portada": round(e_portada, 2),
            "nitidez": nitidez(mejor),
            "veredicto": veredicto,
            "title": c.get("title"),
            "origin": c.get("origin"),
            "contentUrl": c.get("contentUrl"),
            "low_trust_source": c.get("low_trust_source"),
        })

    orden = {"sirve a sangre completa": 0, "sirve solo como portada con foto al 60%": 1}
    salida.sort(key=lambda x: (orden.get(x["veredicto"], 2), bool(x["low_trust_source"]), -x["tamano_real"][0] * x["tamano_real"][1]))
    return salida


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: /usr/bin/python3 fotos_hd.py <candidatos.json> <carpeta_descargas>", file=sys.stderr)
        sys.exit(1)
    datos = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    candidatos = datos["candidates"] if isinstance(datos, dict) else datos
    print(json.dumps(procesar(candidatos, Path(sys.argv[2])), indent=2, ensure_ascii=False))
