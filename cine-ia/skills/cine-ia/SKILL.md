---
name: cine-ia
description: >
  Skill para crear cortometrajes cinematográficos profesionales con IA, desde cero hasta
  listos para YouTube. Activar siempre que el usuario mencione: "cortometraje", "corto",
  "quiero hacer un video", "historia para video IA", "crear contenido audiovisual", "Veo 3",
  "Veo 3.1", "Nano Banana video", "quiero hacer un corto de [cualquier género]", o cuando
  pida producir contenido audiovisual con herramientas IA independientemente del género
  (terror, romance, aventura, infantil, acción, drama, ciencia ficción, comedia, documental, etc.).
  Cubre el pipeline completo en 9 pasos: ideación → guión → personajes consistentes → imágenes
  (Nano Banana 2) → video (Veo 3.1 Flow, clips 8 seg con diálogos lip-sync) → audio
  (ElevenLabs solo narración) → montaje (CapCut) → thumbnail.
  Canal tipo DARK: sin mostrar rostro, voz sintética, 100% IA.
  TAMBIÉN activar cuando el usuario pida prompts para Veo 3.1, prompts para Nano Banana,
  o cuando quiera animar imágenes con IA.
---

# 🎬 Cine IA — Pipeline de Producción Cinematográfica Completa

## Stack de producción
| Herramienta | Función | Nota |
|---|---|---|
| **Nano Banana 2** | Imágenes de referencia por escena | Guardar seed para consistencia de personajes |
| **Veo 3.1 (Flow)** | Video con audio nativo — **8 seg por clip** | Image-to-Video + diálogos con lip-sync |
| **ElevenLabs** | **Solo narración en off** | Los diálogos se generan en Veo 3.1 |
| **CapCut** | Montaje, sincronía audio-video, exportación | Se usa en Paso 8 y revisión final |
| **Suno.AI / YT Audio Library** | Banda sonora | YouTube Audio Library = segura para monetizar |

---

## REGLA CRÍTICA — Cálculo de clips Veo 3.1

**Cada clip de Veo 3.1 = exactamente 8 segundos. Nunca más, nunca menos.**

```
Duración de escena (seg) ÷ 8 = clips necesarios
Redondear SIEMPRE hacia arriba.

Ejemplos:
  Escena de 16 seg  →  2 clips
  Escena de 20 seg  →  3 clips (recortar en CapCut)
  Video de 8 min    →  480 seg ÷ 8 = 60 clips mínimos
```

**Estructura estándar de un cortometraje para YouTube:**
- Duración: **8–10 minutos** (480–600 segundos)
- División: Inicio 3 min / Desarrollo 3 min / Final 2–4 min
- Total clips: **60–75 clips**
- Escenas: **8–12 escenas**

---

## LO QUE NO DEBES HACER

- No usar personajes famosos reales ni celebridades
- No usar música sin licencia
- No generar audio en ElevenLabs hasta guión 100% cerrado
- No mostrar el rostro del creador (canal DARK)
- **No describir menores de edad en contextos oscuros/horror** → filtros de Gemini lo bloquean. Solución: personajes de 19+ años
- **No usar efectos de fantasía en prompts** (humo, niebla mágica, ojos brillantes, disoluciones sobrenaturales) → genera estética de videojuego. Usar siempre acciones que se puedan filmar con cámara real

---

## PIPELINE COMPLETO — 9 PASOS

---

### PASO 1 — DEFINIR EL MODELO DEL VIDEO

**¿Qué género?**

| Género | Tono visual | Ritmo | Música |
|---|---|---|---|
| Terror | Oscuro, frío, desaturado | Lento con cortes bruscos | Drones, stingers, silencio |
| Romance | Cálido, dorado, luminoso | Suave y fluido | Instrumental emocional |
| Aventura / Acción | Contrastado, saturado | Rápido, dinámico | Épica orquestal |
| Infantil | Brillante, colorido | Pausado y claro | Alegre, melodías simples |
| Drama | Natural, desaturado suave | Moderado, contemplativo | Piano, cuerdas |
| Ciencia Ficción | Frío, azul/neón, futurista | Variado | Electrónica ambiental |
| Comedia | Colorido, saturado | Rápido con pausas cómicas | Ligera, percusión |
| Suspenso / Thriller | Gris, verde, bajo contraste | Lento con picos | Tensión orquestal |

**¿Narrado o con diálogos?**
- **Narrado con voz en off** → ElevenLabs. Más fácil.
- **Con diálogos** → Veo 3.1 genera lip-sync directamente.
- **Mixto (recomendado)** → Narración en ElevenLabs + diálogos en Veo 3.1.

---

### PASO 2 — IDEACIÓN: 3 IDEAS DE HISTORIA

Generar siempre **3 ideas**. El usuario elige UNA.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IDEA [N]: [TÍTULO]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GANCHO: [Premisa en 1 línea]
GÉNERO / SUBGÉNERO:
DURACIÓN ESTIMADA: [X min] → CLIPS VEO 3.1: [Y clips]
PERSONAJES: [Nombre — descripción física + emocional, 19+ años]
LOCACIÓN PRINCIPAL:
SINOPSIS: INICIO / DESARROLLO / CLÍMAX / FINAL
TONO DE REFERENCIA: [Película similar]
VIABILIDAD IA: [Alta / Media + desafíos]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### PASO 3 — GUIÓN COMPLETO

Dividido en 3 partes. Cada plano indica 🎭 qué personaje de referencia usar.

```
ESCENA [N] — [NOMBRE] | PARTE [1/2/3]
Duración: [X] seg → [Y] clips Veo 3.1
Locación: [INT/EXT — LUGAR — MOMENTO]

NARRACIÓN EN OFF: "[Texto para ElevenLabs]"
DIÁLOGO: [PERSONAJE]: "[Frase en castellano]"

PLANOS:
  🎭 REF: [PERSONAJE] | Plano [N.1] — 8 seg: [Descripción]
  🎭 SIN REF | Plano [N.2] — 8 seg: [Descripción]

AUDIO AMBIENTE: [sonidos]
MÚSICA: [estado de la música]
```

---

### PASO 4 — PERSONAJES CONSISTENTES

**Este paso es CRÍTICO.** Un personaje que cambia de aspecto destruye la credibilidad.

**REGLA: todos los personajes en contextos oscuros/horror deben tener 19+ años** para evitar bloqueos de filtros de Gemini/Nano Banana.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FICHA DE PERSONAJE: [NOMBRE]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Edad aparente: [19+ para horror]
Cabello: | Ojos: | Piel: | Ropa: | Rasgo distintivo:

FRAGMENTO FIJO (copiar en cada prompt donde aparezca):
"[descripción completa en inglés]"

SEED NANO BANANA: [______]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Consistencia en Nano Banana:**
1. Generar primera imagen → si gusta → **anotar SEED**
2. Siguientes escenas → usar mismo seed + cambiar acción/locación
3. Alternativa: subir primera imagen como **referencia visual**

---

### PASO 5 — PROMPTS DE IMAGEN (Nano Banana 2)

**Formato de prompt:**
```
[FRAGMENTO FIJO del personaje],
[acción o postura],
[locación detallada],
[iluminación — tipo, fuente, color, dirección],
[tipo de plano],
photorealistic, cinematic [género] film still, [paleta de color],
4K, ultra detailed, sharp focus, no text, no watermark
```

**NEGATIVE PROMPT GLOBAL (copiar en TODAS las generaciones):**
```
cartoon, anime, illustration, drawing, blurry, low quality, duplicate,
text, watermark, deformed hands, extra limbs, bright colors, cheerful,
saturated, modern clothing, contemporary
```

**Para escenas hiperrealistas (evitar look de videojuego), agregar al negative:**
```
smoke, fog, mist, tendrils, magical effects, fantasy, video game, CGI,
digital art, glowing eyes, supernatural effects
```

**REGLA: si no se puede filmar con una cámara real, no lo pongas en el prompt.** Nada de humo mágico, disoluciones, ojos brillantes. Usar sombras, oscuridad, retroiluminación y encuadre para generar terror/misterio.

---

### PASO 6 — PROMPTS DE VIDEO (Veo 3.1) ⚡ MASTER PROMPT FRAMEWORK

Veo 3.1 genera video + audio nativo (diálogos con lip-sync, ambiente, SFX).

#### Estructura del prompt — PÁRRAFO ÚNICO FLUIDO

**Nunca usar listas ni etiquetas separadas. Todo en un solo bloque narrativo cinematográfico.**

Orden de elementos dentro del párrafo:
1. Tipo de plano + lente (35mm/50mm/85mm)
2. Movimiento de cámara + PROPÓSITO (to reveal / emphasize / contrast / perspective)
3. Descripción del sujeto (fragmento fijo del personaje)
4. Acción con MICRO-MOVIMIENTOS (parpadeo, respiración, giro de cabeza, movimiento de ojos)
5. Diálogo si aplica: `says in [tono] in Latin American Spanish: "frase en castellano"`
6. Rack focus si aplica
7. Iluminación con temperatura, dirección y sombras
8. Imperfecciones: `subtle handheld breathing motion`
9. SFX + Ambient
10. Cierre técnico: `16:9, 4K, 24fps, ultra-realistic, cinematic [género], HDR, [velocidad], no subtitles, no text overlays, no distortions`

#### Lentes y su uso:
| Lente | Efecto | Mejor para |
|---|---|---|
| **35mm** | Campo amplio, contexto | Planos generales, establecimientos |
| **50mm** | Natural, ojo humano | Planos medios, seguimiento |
| **85mm** | Sujeto aislado, compresión | Close-ups, retratos emocionales |

#### Reglas de diálogo en Veo 3.1:
- **1 personaje hablando por clip** (2 = lip sync falla 60%)
- **Frase corta** (máximo 8 seg)
- **Comillas obligatorias** → `says in [tono]: "frase"` activa lip-sync
- **Idioma** → agregar `in Latin American Spanish` antes de la frase para castellano
- **Siempre cerrar con** `no subtitles, no text overlays, no distortions`

#### Dirección de diálogo (CRÍTICO para realismo):

**Sin estos 3 elementos, Veo 3.1 genera personajes hablando al vacío o mirando a cámara, lo cual rompe la inmersión.**

Cada línea de diálogo DEBE incluir:

1. **TARGET** → ¿A quién le habla? (mira a su madre / clava los ojos en el sacerdote / susurra hacia la ventana)
2. **INTENTION** → ¿Qué quiere lograr? (suplicar oscuridad / exigir a su hija / desafiar públicamente / entregar una advertencia secreta)
3. **PHYSICAL CONNECTION** → ¿Cómo se relaciona el cuerpo con el oyente? (se acerca al oído / apunta el crucifijo / habla sin darse vuelta / se gira lentamente para enfrentarla)

**❌ MAL (sin dirección):**
`she says in a warm voice in Latin American Spanish: "Mara, despertá mi amor."`

**✅ BIEN (con dirección):**
`she looks toward the bedroom door with tender worry, calling her daughter to wake up, she says in a warm maternal voice in Latin American Spanish: "Mara, despertá mi amor. Ya es de día."`

#### Ejemplo CON diálogo:
```
Close-up, 85mm lens, slow push-in to emphasize emotional disconnection. A 19-year-old Eastern European young woman with long straight black hair down to her waist, fair delicate skin, wearing a white cotton nightgown, sitting on a bed in a dark room. She slowly turns her head from a boarded window toward the camera with unnaturally smooth controlled movement, her long hair drags softly across the pillow during the turn, a faint cold smile forms on her lips but her eyes remain completely vacant and distant, she blinks once very slowly, her breathing is barely visible but rhythmically too perfect. She says in a calm flat emotionless young female voice in Latin American Spanish: "Con nadie, mamá." Rack focus shifts from the dark boarded window behind her to her pale face as she completes the turn. Cold blue moonlight from the left filtering through cracks in wooden boards, the light travels across her features as she rotates, deep black shadow on the right side, no warm tones anywhere, subtle handheld breathing motion. SFX: her hair dragging across fabric, then her unnervingly calm voice cutting the silence. Ambient: dead night stillness inside a stone cottage. 16:9, 4K, 24fps, ultra-realistic, cinematic horror, HDR, extreme slow motion, no subtitles, no text overlays, no distortions.
```

#### Ejemplo SIN diálogo:
```
Wide establishing shot, 35mm lens, slow crane descending to reveal isolation and vulnerability. A small rural Transylvanian village at grey dawn, wooden and stone houses with thatched roofs, dirt roads, thick low fog clinging to the streets and shifting slowly, a broken church bell tower in the background, thin smoke curls from chimneys bending in the wind. Cold blue desaturated lighting, overcast grey sky casting flat shadowless light, pale dawn glow on the horizon, subtle handheld breathing motion. SFX: a single rusted church bell tolling once, distant crows cawing, faint wind howling through the valley. Ambient: eerie morning silence of an isolated mountain village. 16:9, 4K, 24fps, ultra-realistic, cinematic horror, HDR, slightly slow motion, no subtitles, no text overlays, no distortions.
```

#### Tipos de clip en producción mixta:
| Tipo | Audio | Herramienta de voz |
|---|---|---|
| Clips CON diálogo | Personaje habla con lip-sync | **Veo 3.1** genera todo |
| Clips SIN diálogo | Solo movimiento y ambiente | **Veo 3.1** visual + SFX |
| Narración en off | Voz invisible del narrador | **ElevenLabs** |

---

### PASO 7 — AUDIO (ElevenLabs)

**⚠️ Con Veo 3.1, ElevenLabs se usa SOLO para narración en off.**

| Género | Voz narrador | Stability | Style Exag. | Velocidad |
|---|---|---|---|---|
| Terror | Grave masculina | 60–70 | 30–50 | Lenta |
| Romance | Cálida, cercana | 70–80 | 40–60 | Normal-lenta |
| Acción | Enérgica, clara | 55–65 | 60–75 | Normal-rápida |
| Drama | Contenida, íntima | 65–75 | 35–55 | Lenta |

---

### PASO 8 — MONTAJE EN CAPCUT

**4 pasadas:**
1. **Video:** clips Veo 3.1 en orden → cortar → transiciones
2. **Música:** banda sonora → ajustar volumen
3. **Narración:** MP3 ElevenLabs → sincronizar
4. **Revisión:** ver completo → exportar **1920×1080 / 24fps / bitrate alto**

**Volumen:** narración > diálogos (ya en video) > efectos > música

---

### PASO 9 — THUMBNAIL

1. Generar en Nano Banana (momento más impactante)
2. Subir a **Canva** → texto bold + contraste
3. Exportar **1280×720 px**

---

## CHECKLIST

```
□ PASO 1  — Género + formato
□ PASO 2  — 3 ideas → usuario elige 1
□ PASO 3  — Guión completo con 🎭 referencias por plano
□ PASO 4  — Fichas personaje (19+) + seeds
□ PASO 5  — Imágenes Nano Banana (hiperrealistas, sin VFX fantasía)
□ PASO 6  — Clips Veo 3.1 (Master Prompt Framework, diálogos castellano)
□ PASO 7  — ElevenLabs: SOLO narración en off
□ PASO 8  — CapCut: montaje → export 1080p 24fps
□ PASO 9  — Thumbnail (Nano Banana + Canva)
□ SUBIR   — YouTube
```

## PALETAS DE COLOR

| Género | Palabras clave |
|---|---|
| Terror | `cold blue tones, deep shadows, pale moonlight, desaturated` |
| Romance | `warm golden light, soft bokeh, warm tones` |
| Acción | `vibrant colors, high contrast, dynamic lighting` |
| Drama | `muted tones, natural lighting, soft shadows` |
| Ciencia Ficción | `neon blue, dark environment, futuristic lighting` |
| Folklore | `dark forest green, earth tones, overcast sky` |
