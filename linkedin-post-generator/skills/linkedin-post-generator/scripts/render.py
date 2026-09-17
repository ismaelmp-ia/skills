#!/usr/bin/env python3
"""
Renderiza un post de LinkedIn (imagen única o carrusel) a partir de un
guion JSON, con la identidad visual de mi-marca.json. Cada placa se
arma como HTML con plantillas/estilos.css y se fotografía con un
navegador Chromium sin ventana (Chrome, Brave, Edge o Chromium).

Reemplaza al compositor en PIL (compose_post.py), validado como amateur
el 15/09/2026: Arial blanco sobre franja negra, sin jerarquía ni marca,
una palabra sola en la última línea y fotos agrandadas hasta pixelarse.

Uso:
    /usr/bin/python3 render.py <guion.json> <carpeta_entrega>

Deja en <carpeta_entrega> SOLO lo publicable:
    imagen.jpg      (formato "imagen")
    carrusel.pdf    (formato "carrusel": el que se sube como documento)
Los HTML intermedios viven en una carpeta temporal. Las vistas de
revisión (hoja de placas + recortes de la foto a tamaño real) se dejan en
una carpeta temporal cuya ruta sale en el JSON impreso: se miran y listo.

Errores bloqueantes (no se genera nada): foto demasiado chica para el
uso elegido, o texto que no entra ni reducido. La salida es acortar el
texto o conseguir otra foto, no forzar.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

SKILL_DIR = Path(__file__).resolve().parent.parent
CSS_PATH = SKILL_DIR / "plantillas" / "estilos.css"
MARCA_PATH = SKILL_DIR / "mi-marca.json"
MARCA_EJEMPLO = SKILL_DIR / "marca.ejemplo.json"

W, H = 1080, 1350
ESCALA_RENDER = 2             # se renderiza a 2160x2700: texto nítido en pantallas densas
FOTO_MEDIA_RATIO = 0.60
ESCALA_MAX_FOTO = 1.15        # mismo umbral que fotos_hd.py
MIN_ESCALA_TEXTO = 0.62

CANDIDATOS_NAVEGADOR = [
    os.environ.get("NAVEGADOR_RENDER", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
]

AJUSTE_JS = """
<script>
(async () => {
  await document.fonts.ready;
  const cuerpo = document.querySelector('.cuerpo');
  const els = [...document.querySelectorAll('[data-fit]')];
  const desborda = () => cuerpo.scrollHeight > cuerpo.clientHeight + 1 ||
    els.some(e => e.scrollWidth > e.clientWidth + 1);
  let escala = 1;
  const aplicar = () => els.forEach(e => e.style.fontSize = (parseFloat(e.dataset.fit) * escala) + 'px');
  aplicar();
  while (desborda() && escala > %MIN%) { escala -= 0.02; aplicar(); }
  document.body.dataset.escala = escala.toFixed(2);
  document.body.dataset.desborde = desborda() ? '1' : '0';
})();
</script>
""".replace("%MIN%", str(MIN_ESCALA_TEXTO))


class Bloqueante(Exception):
    pass


# ---------------------------------------------------------------- utilidades

def navegador() -> str:
    for ruta in CANDIDATOS_NAVEGADOR:
        if ruta and os.path.exists(ruta):
            return ruta
    raise RuntimeError("No hay navegador Chromium instalado (Chrome, Brave, Edge o Chromium). "
                       "Instalar uno o definir NAVEGADOR_RENDER con la ruta al ejecutable.")


def txt(valor: str | None) -> str:
    """Escapa HTML. *texto* = cyan (remate), ~texto~ = rojo (caída/peligro)."""
    if not valor:
        return ""
    seguro = html.escape(valor)
    seguro = re.sub(r"\*(.+?)\*", r"<em>\1</em>", seguro)
    seguro = re.sub(r"~(.+?)~", r'<span class="rojo">\1</span>', seguro)
    return seguro.replace("\n", "<br>")


def fit(px: int) -> str:
    return f'data-fit="{px}" style="font-size:{px}px"'


def preparar_emblema(marca: dict, tmp: Path) -> str:
    if not marca.get("logo"):
        return None
    logo = Path(marca["logo"]).expanduser()
    if not logo.exists():
        print(f"AVISO: no encontré el logo en {logo}; las placas salen sin emblema.", file=sys.stderr)
        return ""
    destino = tmp / "emblema.png"
    with Image.open(logo) as im:
        recorte = marca.get("logo_recorte_emblema")
        im = im.convert("RGB")
        (im.crop(tuple(recorte)) if recorte else im).save(destino)
    return destino.as_uri()


def modo_foto(p: dict) -> str:
    """sangre (foto completa) o media (foto en el 60% superior), según los
    píxeles reales. Si no alcanza para ninguno, se bloquea: una foto
    pixelada arruina el post entero (caso real 15/09/2026)."""
    with Image.open(p["foto"]) as im:
        w, h = im.size
    e_sangre = max(W / w, H / h)
    e_media = max(W / w, H * FOTO_MEDIA_RATIO / h)
    pedido = p.get("modo_foto", "auto")
    if pedido in ("auto", "sangre") and e_sangre <= ESCALA_MAX_FOTO:
        return "sangre"
    if pedido == "sangre":
        raise Bloqueante(f"La foto {w}x{h} se agrandaría {e_sangre:.2f}x a sangre completa. Usar modo media u otra foto.")
    if e_media <= ESCALA_MAX_FOTO:
        return "media"
    raise Bloqueante(f"La foto {w}x{h} es chica: se agrandaría {e_media:.2f}x incluso al 60%. Conseguir otra (fotos_hd.py).")


# ---------------------------------------------------------------- placas

def cabecera(p: dict, i: int, n: int, carrusel: bool) -> str:
    etiqueta = f'<div class="etiqueta">{txt(p.get("etiqueta"))}</div>' if p.get("etiqueta") else "<div></div>"
    pagina = f'<div class="pagina">{i:02d} / {n:02d}</div>' if carrusel else ""
    return f'<div class="cabecera">{etiqueta}{pagina}</div>'


def pie(marca: dict, emblema: str, i: int, n: int, carrusel: bool) -> str:
    img = f'<img src="{emblema}" alt="">' if emblema else ""
    etiqueta_deslizar = html.escape(marca.get("texto_deslizar", "Deslizar →"))
    derecha = f'<div class="deslizar">{etiqueta_deslizar}</div>' if carrusel and i == 1 else ""
    barra = f'<div class="progreso"><span style="width:{i / n * 100:.1f}%"></span></div>' if carrusel else ""
    return f'<div class="pie"><div class="firma-marca">{img}<span>{html.escape(marca["nombre"])}</span></div>{derecha}</div>{barra}'


def placa_portada(p: dict, ctx: dict) -> tuple[str, str]:
    bajada = f'<p class="texto bajada" {fit(38)}>{txt(p.get("bajada"))}</p>' if p.get("bajada") else ""
    if not p.get("foto"):
        return "", f'<div class="cuerpo"><div class="barra"></div><h1 class="titular" {fit(170)}>{txt(p["titular"])}</h1>{bajada}</div>'
    modo = modo_foto(p)
    ctx["modo_foto"] = modo
    fx, fy = p.get("foco", [0.5, 0.3])
    fondo = (f'<div class="foto" style="background-image:url(\'{Path(p["foto"]).resolve().as_uri()}\');'
             f'background-position:{fx * 100:.0f}% {fy * 100:.0f}%"></div>')
    credito = f'<div class="credito">{txt(p["credito"])}</div>' if p.get("credito") else ""
    return f"portada-{modo}", (
        f'{fondo}{credito}<div class="cuerpo"><div class="barra"></div>'
        f'<h1 class="titular" {fit(124)}>{txt(p["titular"])}</h1>{bajada}</div>'
    )


def placa_cifra(p: dict, ctx: dict) -> tuple[str, str]:
    fuente = f'<p class="fuente">{txt(p.get("fuente"))}</p>' if p.get("fuente") else ""
    return "", (f'<div class="cuerpo"><div class="cifra" {fit(360)}>{txt(p["cifra"])}</div>'
                f'<p class="texto" {fit(50)}>{txt(p["texto"])}</p>{fuente}</div>')


def placa_punto(p: dict, ctx: dict) -> tuple[str, str]:
    numero = f'<div class="numero">{txt(p.get("numero"))}</div>' if p.get("numero") else '<div class="barra"></div>'
    texto = f'<p class="texto" {fit(48)}>{txt(p.get("texto"))}</p>' if p.get("texto") else ""
    fuente = f'<p class="fuente">{txt(p.get("fuente"))}</p>' if p.get("fuente") else ""
    return "punto", f'<div class="cuerpo">{numero}<h2 class="titular" {fit(108)}>{txt(p["titulo"])}</h2>{texto}{fuente}</div>'


def placa_lista(p: dict, ctx: dict) -> tuple[str, str]:
    filas = []
    for it in p["items"]:
        clase = "item panel destacado" if it.get("destacado") else "item panel"
        nota = f'<span class="nota">{txt(it.get("nota"))}</span>' if it.get("nota") else ""
        filas.append(f'<div class="{clase}"><div class="marca-item" {fit(30)}>{txt(it.get("marca", ""))}</div>'
                     f'<div class="texto-item" {fit(44)}>{txt(it["texto"])}{nota}</div></div>')
    return "", (f'<div class="cuerpo"><div class="barra"></div><h2 class="titular" {fit(92)}>{txt(p["titulo"])}</h2>'
                f'<div class="lista">{"".join(filas)}</div></div>')


def placa_comparacion(p: dict, ctx: dict) -> tuple[str, str]:
    def bloque(b: dict, clase: str) -> str:
        filas = "".join(f'<div class="fila" {fit(40)}><span>{txt(f[0])}</span><span class="valor">{txt(f[1])}</span></div>'
                        for f in b["filas"])
        return f'<div class="bloque panel {clase}"><h3>{txt(b["titulo"])}</h3>{filas}</div>'

    fuente = f'<p class="fuente">{txt(p.get("fuente"))}</p>' if p.get("fuente") else ""
    return "", (f'<div class="cuerpo"><div class="barra"></div><h2 class="titular" {fit(88)}>{txt(p["titulo"])}</h2>'
                f'<div class="comparacion">{bloque(p["pierde"], "pierde")}{bloque(p["gana"], "gana")}</div>{fuente}</div>')


def placa_cita(p: dict, ctx: dict) -> tuple[str, str]:
    return "", (f'<div class="cuerpo"><div class="comillas">“</div>'
                f'<blockquote class="cita" {fit(90)}>{txt(p["cita"])}</blockquote>'
                f'<div class="autor"><strong>{txt(p["autor"])}</strong><span>{txt(p.get("cargo"))}</span></div></div>')


def placa_cierre(p: dict, ctx: dict) -> tuple[str, str]:
    firma = p.get("firma") or ctx["marca"].get("firma_cierre", "")
    fondo = f'<img class="emblema-fondo" src="{ctx["emblema"]}" alt="">' if ctx["emblema"] else ""
    return "cierre", (f'{fondo}<div class="cuerpo"><div class="barra"></div><h2 class="titular" {fit(120)}>{txt(p["titular"])}</h2>'
                      f'<p class="pregunta panel" {fit(42)}>{txt(p["pregunta"])}</p><p class="firma">{txt(firma)}</p></div>')


TIPOS = {
    "portada": placa_portada, "cifra": placa_cifra, "punto": placa_punto, "lista": placa_lista,
    "comparacion": placa_comparacion, "cita": placa_cita, "cierre": placa_cierre,
}


def armar_html(p: dict, i: int, n: int, carrusel: bool, ctx: dict) -> str:
    if p["tipo"] not in TIPOS:
        raise ValueError(f"Tipo de placa desconocido: {p['tipo']}. Válidos: {sorted(TIPOS)}")
    clase, cuerpo = TIPOS[p["tipo"]](p, ctx)
    variables = "".join(f"--{k}:{v};" for k, v in ctx["marca"]["colores"].items())
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8">'
            f'<link rel="stylesheet" href="{CSS_PATH.as_uri()}"><style>:root{{{variables}}}</style></head>'
            f'<body><section class="slide {clase}">{cabecera(p, i, n, carrusel)}{cuerpo}'
            f'{pie(ctx["marca"], ctx["emblema"], i, n, carrusel)}</section>{AJUSTE_JS}</body></html>')


# ---------------------------------------------------------------- render

def correr_navegador(nav: str, args: list[str], escala: int = 1) -> subprocess.CompletedProcess:
    base = [nav, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--allow-file-access-from-files", f"--force-device-scale-factor={escala}",
            f"--window-size={W},{H}", "--virtual-time-budget=5000"]
    return subprocess.run(base + args, capture_output=True, text=True, timeout=120)


def render(guion_path: str, destino: str) -> dict:
    guion = json.loads(Path(guion_path).read_text(encoding="utf-8"))
    if not MARCA_PATH.exists():
        print(f"ERROR: falta {MARCA_PATH.name}. Copiá {MARCA_EJEMPLO.name} a {MARCA_PATH.name} "
              f"y completá tu marca (o pedíselo al skill).", file=sys.stderr)
        sys.exit(1)
    marca = json.loads(MARCA_PATH.read_text(encoding="utf-8"))
    formato = guion["formato"]
    if formato not in ("imagen", "carrusel"):
        raise ValueError('formato tiene que ser "imagen" o "carrusel"')
    placas = guion["placas"]
    carrusel = formato == "carrusel"
    if not carrusel and len(placas) != 1:
        raise ValueError("El formato imagen lleva exactamente 1 placa.")
    if carrusel and not 5 <= len(placas) <= 10:
        raise ValueError("Un carrusel lleva entre 5 y 10 placas.")

    tmp = Path(tempfile.mkdtemp(prefix="linkedin-render-"))
    revision = Path(tempfile.mkdtemp(prefix="linkedin-revision-"))
    nav = navegador()
    ctx = {"marca": marca, "emblema": preparar_emblema(marca, tmp)}
    n = len(placas)
    avisos: list[str] = []
    pngs: list[Path] = []

    for i, p in enumerate(placas, start=1):
        ctx.pop("modo_foto", None)
        html_path = tmp / f"{i:02d}.html"
        html_path.write_text(armar_html(p, i, n, carrusel, ctx), encoding="utf-8")

        dom = correr_navegador(nav, ["--dump-dom", html_path.as_uri()]).stdout
        m = re.search(r'data-escala="([\d.]+)"', dom)
        if 'data-desborde="1"' in dom:
            raise Bloqueante(f"Placa {i}: el texto no entra ni reducido al {MIN_ESCALA_TEXTO:.0%}. Acortarlo.")
        if m and float(m.group(1)) < 0.8:
            avisos.append(f"Placa {i}: texto reducido al {float(m.group(1)):.0%} para entrar. Conviene acortarlo.")

        png = tmp / f"{i:02d}.png"
        correr_navegador(nav, [f"--screenshot={png}", html_path.as_uri()], escala=ESCALA_RENDER)
        if not png.exists():
            raise RuntimeError(f"El navegador no generó la placa {i}.")
        pngs.append(png)

        # recorte de la foto a tamaño real: la pixelación NO se ve en miniatura
        if ctx.get("modo_foto"):
            with Image.open(png) as im:
                alto_foto = im.height if ctx["modo_foto"] == "sangre" else int(im.height * FOTO_MEDIA_RATIO)
                cx, cy = im.width // 2, alto_foto // 3
                im.crop((cx - 500, max(0, cy - 500), cx + 500, max(0, cy - 500) + 1000)).save(revision / f"zoom-foto-placa-{i:02d}.png")
            avisos.append(f"Placa {i}: foto en modo {ctx['modo_foto']}.")

    imagenes = [Image.open(x).convert("RGB") for x in pngs]
    dest = Path(destino)
    dest.mkdir(parents=True, exist_ok=True)
    if carrusel:
        salida = dest / "carrusel.pdf"
        imagenes[0].save(salida, save_all=True, append_images=imagenes[1:], resolution=72 * ESCALA_RENDER, quality=95)
    else:
        salida = dest / "imagen.jpg"
        imagenes[0].save(salida, "JPEG", quality=95, subsampling=0, optimize=True)

    cols = min(5, n)
    filas = (n + cols - 1) // cols
    tw, th = 432, 540
    hoja = Image.new("RGB", (cols * tw + (cols + 1) * 16, filas * th + (filas + 1) * 16), (30, 30, 34))
    for k, im in enumerate(imagenes):
        r, c = divmod(k, cols)
        hoja.paste(im.resize((tw, th), Image.LANCZOS), (16 + c * (tw + 16), 16 + r * (th + 16)))
    hoja.save(revision / f"hoja-{formato}.jpg", quality=90)
    for k, im in enumerate(imagenes, start=1):
        im.resize((W, H), Image.LANCZOS).save(revision / f"placa-{k:02d}.jpg", quality=90)

    shutil.rmtree(tmp, ignore_errors=True)
    return {"salida": str(salida), "revision": str(revision), "avisos": avisos}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: /usr/bin/python3 render.py <guion.json> <carpeta_entrega>", file=sys.stderr)
        sys.exit(1)
    try:
        print(json.dumps(render(sys.argv[1], sys.argv[2]), indent=2, ensure_ascii=False))
    except Bloqueante as e:
        print(f"BLOQUEANTE: {e}", file=sys.stderr)
        sys.exit(2)
