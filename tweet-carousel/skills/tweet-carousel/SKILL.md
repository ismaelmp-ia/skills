---
name: tweet-carousel
description: Pipeline completo Tweet → Carrusel de Instagram con tu marca. Se activa con una URL de tweet o el comando /tweet-carousel. Scraping del tweet, Claude escribe los slides, Kie AI genera imágenes cinematográficas con pools de variación (cada carrusel tiene metáforas visuales distintas).
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
---

# Tweet → Carrusel de Instagram

Pipeline completo para convertir cualquier tweet en un carrusel de Instagram cinematográfico con tu identidad visual.

## Activación

Se activa cuando el usuario:
- Pega una URL de tweet: `https://x.com/...` o `https://twitter.com/...`
- Usa el comando: `/tweet-carousel [url]`

---

## Flujo Obligatorio (4 pasos)

### PASO 0 — Scraping del tweet

```bash
PYTHONUNBUFFERED=1 py scripts/scrape-tweet.py --url "URL_DEL_TWEET"
```

Si falla por autenticación:
> "Necesitas actualizar tus cookies de Twitter en `.env` — `TWITTER_AUTH_TOKEN` y `TWITTER_CT0`."

---

### PASO 1 — Propuesta de carrusel

Con el contenido del tweet, proponer:

1. **Tema central** (1 línea)
2. **Ángulo narrativo**: educativo, polémico, datos, how-to, inspiracional
3. **Estructura de slides** en tabla:

| Slide | Tipo | Texto propuesto |
|-------|------|-----------------|
| 1 | Hook | ... |
| 2 | Intro | ... |
| 3 | Problema/Dato 1 | ... |
| 4 | Dato clave/Dato 2 | ... |
| 5 | Contrapunto/Dato 3 | ... |
| 6 | Micro-recompensa | ... |
| 7 | CTA | ... |

4. **bundle_id sugerido** (formato: `YYYY-MM-DD-tema-corto`)

**ESPERAR CONFIRMACIÓN antes de continuar.**

---

### PASO 2 — Crear repurpose-pack.md

Una vez aprobada la estructura, crear `outputs/bundles/[bundle_id]/repurpose-pack.md` con este formato exacto:

```markdown
# [TÍTULO DEL CARRUSEL]

**Fuente:** [URL del tweet]
**Fecha:** [fecha actual YYYY-MM-DD]
**bundle_id:** [bundle_id]

---

## Carrusel Instagram

### SLIDE 1 - Hook
```
[texto del slide — puede usar markup {bl:texto} azul, {or:texto} naranja, {sm:texto} gris]
```

### SLIDE 2 - Intro
```
[texto]
```

### SLIDE 3 - [Tipo]
```
[texto]
```

### SLIDE 4 - [Tipo]
```
[texto]
```

### SLIDE 5 - [Tipo]
```
[texto]
```

### SLIDE 6 - [Tipo]
```
[texto]
```

### SLIDE 7 - CTA
```
[texto]
```
```

**Reglas de contenido:**
- Texto corto y directo por slide (máximo 4 líneas)
- Slide 1 (Hook): título que pare el scroll en 1 segundo
- Slide 7 (CTA): pregunta que invite a comentar

**Guía de colores (markup):**
- `{or:palabra}` → **NARANJA** — para nombres de marca (Claude, ChatGPT, OpenAI, Google, Anthropic, etc.) y palabras de alto impacto emocional
- `{bl:palabra}` → **AZUL** — para conceptos técnicos, acciones clave, datos
- `{sm:palabra}` → **GRIS** — para texto secundario, aclaraciones, info de apoyo
- Regla de oro: nombres propios de empresa/producto siempre en naranja, nunca en azul

Mostrar el archivo al usuario para revisión.

**ESPERAR CONFIRMACIÓN antes del PASO 3.**

---

### PASO 3 — Generación de imágenes con Kie AI

⚠️ **OBLIGATORIO: Confirmar costo con el usuario antes de ejecutar.**
Mostrar: "¿Genero los [N] slides? Costo estimado: $[N×0.10]"
Esperar "sí", "hazlo" o confirmación explícita.

Ejecutar el generador:

```bash
PYTHONUNBUFFERED=1 py scripts/generate-carousel-kieai.py [bundle_id]
```

Para regenerar slides específicos (también requiere confirmación de costo):
```bash
PYTHONUNBUFFERED=1 py scripts/generate-carousel-kieai.py [bundle_id] --regenerate-slides "2,4"
```

Al finalizar, crear ZIP con Python:
```python
PYTHONUNBUFFERED=1 py -c "
import zipfile, os, glob
slides = sorted(glob.glob('outputs/bundles/[bundle_id]/carousel/*.png'))
with zipfile.ZipFile('outputs/[bundle_id]-carousel.zip', 'w') as z:
    for f in slides:
        z.write(f, os.path.basename(f))
print(f'ZIP creado con {len(slides)} slides')
"
```

El ZIP se guarda en: `outputs/[bundle_id]-carousel.zip`

Mostrar al usuario:
- ✅ Cuántos slides se generaron
- 📦 ZIP listo: `outputs/[bundle_id]-carousel.zip`
- 💰 Costo: $0.10 × N slides

---

## Estilo visual — Sistema de Variación

El generador `generate-carousel-kieai.py` usa **pools de 4 metáforas visuales distintas** por tipo de slide.
La variante elegida se determina automáticamente con `hash(bundle_id + slide_number)` — esto garantiza:
- **Mismo carrusel** → siempre las mismas imágenes (reproducible)
- **Carruseles distintos** → imágenes distintas (sin repetición)

**Identidad de marca en todos los slides:**
- Fondo: espacio negro profundo (`#030214`) con nebulosa azul eléctrico y estrellas
- Paleta: azul `#00AAFF`, cian `#00E8FF`, naranja `#FF8723`, texto blanco
- Estilo: cartel de película sci-fi. Premium. Cinematográfico. NUNCA watercolor ni flat design.
- 1 elemento protagonista por slide (35-50% del espacio)
- **Slide 7 (CTA)**: siempre incluye el nombre de tu marca al pie

**Pools de variación por tipo:**

| Tipo | Variante 1 | Variante 2 | Variante 3 | Variante 4 |
|------|-----------|-----------|-----------|-----------|
| Hook | Tipografía masiva + rayo de luz | Monolito colosal | Hyperspeed jump | Ojo cósmico |
| Intro | Figura humana de circuitos (split) | Cerebro con anillos orbitales | Red neuronal constelación | Hélice ADN de luz |
| Problema | Muro agrietado naranja | Torre azul vs estructuras pequeñas | Laberinto aéreo | Reloj de arena vacío |
| Dato | Terminal flotante en spotlight | Número gigante 3D | Telescopio apuntando | Plano técnico de luz |
| Contrapunto | Ola azul vs ola naranja | Dos planetas en oposición | Balanza de energía | Reyes de ajedrez |
| Recompensa | Camino de luz (vanishing point) | Portal de luz | Cima de montaña al amanecer | Llave de luz |
| CTA | Signo ? 3D naranja | Mano de luz hacia cámara | Puerta entreabierta cálida | Multitud con globos |

---

## Post-generación (opcional)

Ofrecer al usuario:
- Copy para **Instagram**: título + descripción con emojis al inicio de párrafo + CTA
- Copy para **LinkedIn**: versión más profesional y extendida

---

## Notas críticas

- **NUNCA ejecutar generación sin confirmación explícita de costo** — cada run cuesta $0.70 (7 slides × $0.10)
- NUNCA saltar la confirmación del usuario entre pasos
- El bundle_id siempre incluye fecha + slug del tema
- Si Twitter falla, pedir al usuario que actualice las cookies en `.env`
- Si Kie AI devuelve error de créditos, el usuario debe recargar en kie.ai y usar `--regenerate-slides`
- El ZIP se crea con Python (zip no disponible en Windows)
- Scripts activos: `scrape-tweet.py` y `generate-carousel-kieai.py` — no hay otros
