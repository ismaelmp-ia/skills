---
name: linkedin-post-generator
description: Genera posts de LinkedIn con tu identidad visual — imagen única y/o carrusel en PDF — a partir de un tema o noticia. Investiga y verifica los datos, elige un ángulo propio, busca fotos reales en alta resolución (Apify) y confirma quién aparece, arma las placas (HTML → imagen), revisa el render a tamaño real y redacta el texto con reglas de gancho, estructura y fuentes. Usar cuando pidan "hacé un post de LinkedIn", "armá un carrusel sobre X", "post sobre esta noticia", "/linkedin-post-generator".
---

# LinkedIn Post Generator

LinkedIn premia contenido que se detiene a leer: una idea clara, datos verificables y un diseño que se reconoce en el feed. Cada post que sale de acá tiene que poder publicarse sin retoques. Si algo no alcanza ese nivel (foto chica, dato sin fuente, gancho flojo), se corrige antes de entregar, no después.

**Ruta del skill:** la carpeta que contiene este archivo. Los `scripts/...` son relativos a ella.

**Python:** usar SIEMPRE `.venv/bin/python` (el entorno que crea `preparar.sh`). Trae numpy, requests y Pillow; el Python del sistema puede no tenerlos.

---

## PASO 0 — PRIMERA VEZ (configuración)

Si NO existe `mi-marca.json` en la carpeta del skill, antes de cualquier otra cosa:

1. Comprobar que se corrió el instalador: si no existe `.venv/`, decirle al usuario que ejecute `bash preparar.sh` desde la carpeta del skill.
2. Preguntarle, de a una pregunta por vez:
   - Nombre de la marca (va en el pie de cada placa).
   - Logo: ruta a un PNG, o nada. Sin logo, las placas salen solo con el nombre.
   - Colores: aceptar los del ejemplo o pedir los suyos (fondo, color de acento, texto, gris, rojo de alerta).
   - Frase de cierre: la que aparece en la última placa.
   - Voz: idioma y tratamiento (neutro, tú, vos, usted) para el texto del post.
   - Carpeta donde guardar los posts terminados.
3. Escribir todo en `mi-marca.json`, copiando la estructura de `marca.ejemplo.json` y agregando `"carpeta_salida"`.
4. Confirmar en una línea y seguir con el pedido del usuario.

`mi-marca.json` es del usuario: nunca se sube al repositorio ni se pisa al actualizar.

---

## DÓNDE SE GUARDA

En la `carpeta_salida` de `mi-marca.json`, una carpeta por post:

```
AAAA-MM-DD Título legible/
   imagen.jpg      (si hay formato imagen)
   carrusel.pdf    (si hay formato carrusel)
   copy.md         (texto de cada formato + fuentes + crédito de foto)
```

- Fecha adelante, título en palabras, nombres de archivo genéricos.
- **Nada más en la carpeta.** Guiones, descargas y vistas de revisión van a temporales y ahí se quedan.
- Nunca guardar nada dentro de la carpeta del skill ni de `~/.claude/`: son carpetas ocultas y el usuario no las encuentra.
- Al terminar: decir la ruta completa y abrirla (`open` en Mac, `xdg-open` en Linux).

---

## PASO 1 — INVESTIGAR Y VERIFICAR (antes de pensar en diseño)

Con WebSearch/WebFetch, armar la línea de tiempo del hecho con **fuente por dato**:

- Cada cifra, cita y fecha tiene al menos una URL. Si dos medios dan cifras distintas (típico en bolsa), usar la conservadora y anotarlo.
- **Día de la semana: calcularlo, nunca suponerlo** (`cal 9 2026`). Error real: un post decía "el martes 9" y era miércoles.
- Citas: textuales de la fuente original. Si solo hay paráfrasis en la prensa, escribirla como paráfrasis, sin comillas.
- Cargos completos en la primera mención ("Evan Hubinger, líder de Ciencia de Alineación de Anthropic").

## PASO 2 — ELEGIR EL ÁNGULO

El resumen plano (anuncio + cifras + cierre) no se publica: cualquiera lo arma en minutos. Orden de preferencia:

1. **Tensión real en las fuentes**: algo que no calza con el relato oficial (piden frenar y la bolsa reacciona en 48 h; dicen X y hacen Y).
2. **Consecuencia práctica** para quien construye o dirige un negocio.
3. **Resumen informativo** — solo si 1 y 2 no existen de verdad. Nunca inventar tensión.

El ángulo se formula en **una frase de dos tiempos**: hecho + remate ("Pidieron frenar la IA. La bolsa ya eligió ganadores."). Esa frase es el titular de la portada y el gancho del texto.

## PASO 3 — ELEGIR FORMATO

| Formato | Cuándo |
|---|---|
| Imagen | Una sola idea fuerte: una tensión, una cifra, una cita |
| Carrusel (PDF) | Hay secuencia o desarrollo: línea de tiempo, 3+ puntos, comparación, explicación paso a paso |
| Ambos | Si el usuario lo pide. Se publican en días distintos, nunca juntos |

## PASO 4 — FOTOS EN ALTA RESOLUCIÓN Y CON IDENTIDAD CONFIRMADA

Solo la portada lleva foto. El resto de las placas es tipografía y datos.

**4.1 Buscar.** Query concreta del hecho real (persona + contexto, empresa real, producto real), no la categoría abstracta ("hacker", "servidores"). Si el tema es un producto, la foto muestra el producto, no el campus de la empresa. Pedir 12–20 resultados:

```
.venv/bin/python scripts/filter_images.py "<query>" 16 > <tmp>/candidatos.json
```

**4.2 Subir a máxima resolución y medir:**

```
.venv/bin/python scripts/fotos_hd.py <tmp>/candidatos.json <tmp>/fotos
```

Intenta la versión original de cada foto (Wikimedia sin miniatura, CDNs sin parámetros de tamaño, WordPress sin sufijo `-1024x683`), mide los píxeles reales y da veredicto: `sirve a sangre completa`, `sirve solo como portada con foto al 60%` o `chica`. **Una foto "chica" no se usa nunca**: pixela el post. Si no hay ninguna que sirva, reformular la query o hacer la portada sin foto.

**4.3 Confirmar quién aparece.** El título de la NOTA no alcanza: una nota sobre alguien incluye fotos de otras personas. Válido: nombre en el pie de foto, en el nombre de archivo o en la ficha de Wikimedia. Si no se puede confirmar, no se usa. Nunca identificar a una persona por su cara.

**4.4 Mirar las candidatas** que pasaron 4.2 y 4.3 (un solo pase): relevancia al tema real, nitidez de la cara, marcas de agua (las URLs `alamy.com/comp/` son siempre preview con marca: descartar sin descargar), UI de video o navegador colada, duplicados (`similar_color_to` es una pista, no un veredicto).

**4.5 Crédito y derechos.** Wikimedia/Creative Commons: anotar autor y licencia y ponerlo en `credito` de la portada. Fotos de prensa sin licencia: preferir otra; si no hay alternativa, avisar al usuario del riesgo antes de publicar.

## PASO 5 — GUION DE PLACAS (JSON)

Se escribe en un temporal. Marcado dentro de cualquier texto: `*remate*` = color de acento, `~caída~` = rojo.

```json
{"formato": "carrusel", "placas": [
  {"tipo": "portada", "etiqueta": "Empresa · sep 2026", "foto": "/tmp/.../foto.jpg",
   "foco": [0.5, 0.45], "modo_foto": "auto", "credito": "Foto: Autora / Medio · CC BY 2.0",
   "titular": "Hecho corto. *Remate.*", "bajada": "Una línea que empuja a deslizar."},
  {"tipo": "cifra", "etiqueta": "Mié 9 sep", "cifra": ">10%", "texto": "Qué significa, con *la parte fuerte*.", "fuente": "Quién · dónde"},
  {"tipo": "cita", "etiqueta": "Sáb 12 sep", "cita": "Texto textual.", "autor": "Nombre", "cargo": "Cargo · dónde lo dijo"},
  {"tipo": "punto", "etiqueta": "...", "numero": "Rótulo corto", "titulo": "Idea. *Remate.*", "texto": "Desarrollo en 1-3 líneas."},
  {"tipo": "lista", "etiqueta": "...", "titulo": "...", "items": [{"marca": "01", "texto": "...", "nota": "...", "destacado": true}]},
  {"tipo": "comparacion", "etiqueta": "...", "titulo": "...", "pierde": {"titulo": "Cayeron", "filas": [["SoftBank", "−10%"]]}, "gana": {"titulo": "Subieron", "filas": [["CrowdStrike", "+12%"]]}, "fuente": "..."},
  {"tipo": "cierre", "titular": "Conclusión accionable. *Remate.*", "pregunta": "Pregunta abierta que invite a opinar con experiencia."}
]}
```

- `formato: "imagen"` → exactamente 1 placa (una portada, o una cifra/cita si la idea es esa).
- `foco` [x, y] de 0 a 1: mueve el encuadre. Subir `y` sube la cara en la placa. La cara nunca debe quedar tapada por el titular.
- `modo_foto`: `auto` elige sangre completa si la foto alcanza; `media` pone la foto en el 60% superior (mejor para retratos cerrados, deja la cara libre).

**Reglas de carrusel:**
- 7–9 placas (el script acepta 5–10). Una idea por placa, legible en 3 segundos.
- Placa 1: gancho (titular ≤ 10 palabras). Placa 2: el dato o hecho que engancha. Placas del medio: la secuencia. Penúltima: qué significa para el lector. Última: `cierre`.
- Titulares ≤ 10 palabras; textos de desarrollo ≤ 35 palabras.
- Alternar tipos de placa (cifra, cita, lista, comparación): tres `punto` seguidos aburren.

## PASO 6 — RENDER

```
.venv/bin/python scripts/render.py <tmp>/guion.json "<carpeta de entrega>"
```

- Genera `imagen.jpg` o `carrusel.pdf` (2160×2700 por placa, proporción 4:5).
- **Bloquea** (no genera nada) si la foto se agrandaría más de 1,15× o si un texto no entra ni reducido. Solución: otra foto o texto más corto. Nunca bajar los umbrales para que pase.
- Avisa si un texto se redujo por debajo del 80%: acortarlo.
- Imprime `revision`: carpeta temporal con `hoja-*.jpg` (todas las placas), `placa-NN.jpg` y `zoom-foto-placa-NN.png` (recorte de la foto a tamaño real).

Identidad visual: `mi-marca.json` (nombre, logo, colores) + `plantillas/estilos.css` (fondo oscuro con cuadrícula de puntos, un solo color de acento, títulos en Anton, etiquetas en JetBrains Mono, texto en Space Grotesk). Para cambiar el aspecto: los colores, en `mi-marca.json`; la maqueta, en `plantillas/estilos.css`.

## PASO 7 — REVISIÓN VISUAL OBLIGATORIA

Mirar con Read, **no** dar por buena una placa sin verla:

1. `zoom-foto-placa-NN.png` — la pixelación NO se ve en miniatura. Piel y pelo tienen que verse con detalle.
2. Cada `placa-NN.jpg`:
   - titular sin palabra sola en la última línea
   - la cara no queda tapada
   - el crédito se lee
   - nada cortado en los bordes
   - ninguna etiqueta ilegible (en celular la placa se ve a un tercio de su tamaño)
3. `hoja-*.jpg` — ritmo del carrusel: variedad de placas, sin placas vacías ni saturadas.

Si algo falla: ajustar guion (foco, modo, texto) y volver al Paso 6. Recién con todo aprobado se escribe el copy.

## PASO 8 — TEXTO DEL POST

Voz: la de `mi-marca.json`. Primera persona cuando hay opinión.

**Gancho:** las dos primeras líneas son lo único visible antes de "…ver más".
- Línea 1 ≤ 110 caracteres, línea 2 ≤ 110. Es el ángulo del Paso 2, no el anuncio.
- Nunca empezar con fecha, contexto o "Hoy quiero hablar de…".

**Cuerpo:**
- Párrafos de 1–3 líneas separados por línea en blanco.
- Un solo argumento central. Máximo 3 nombres propios en el texto de imagen.
- Todo lo que promete el gancho se cumple abajo: si el gancho menciona la bolsa, las cifras de bolsa están.
- Listas con "→" solo para datos comparables.
- Cerrar con la consecuencia práctica (qué hacer o cómo leerlo).

**Largo:** texto para imagen, 900–1.500 caracteres. Texto para carrusel, 300–700: el carrusel ya cuenta la historia; el texto engancha y dice qué placa importa.

**Cierre:** una pregunta abierta, específica, que se responda con experiencia u opinión (no sí/no genérico ni "¿qué opinás?").

**Hashtags:** 3, específicos del tema. Nunca #IA #Tecnologia #Innovacion sueltos.

**Prohibido:** "en el mundo actual", "llegó para quedarse", "esto lo cambia todo", "no es X, es Y" más de una vez, emojis decorativos, negritas Unicode, afirmaciones sin fuente.

**`copy.md`** lleva: texto de cada formato generado (con indicación de qué archivo va con cuál), título sugerido del documento para el carrusel, tabla de fuentes (dato → URL) y crédito de foto.

## PASO 9 — CONTROL FINAL ANTES DE ENTREGAR

- [ ] Cada cifra y fecha del texto y de las placas coincide con la tabla de fuentes.
- [ ] Días de la semana verificados con calendario.
- [ ] Persona de la foto confirmada por pie/archivo, no por título de nota.
- [ ] Zoom de la foto revisado: sin pixelación.
- [ ] La carpeta tiene solo `imagen.jpg` / `carrusel.pdf` / `copy.md`.
- [ ] Ruta dicha y carpeta abierta.

---

## NOTAS DE DISEÑO (por qué está así)

- **HTML en vez de PIL**: el compositor anterior en PIL daba Arial blanco sobre franja negra y cortaba titulares dejando una palabra sola. HTML permite tipografía real, `text-wrap: balance` y maquetación de verdad. El navegador se detecta solo (Chrome, Brave, Edge o Chromium; o variable `NAVEGADOR_RENDER`).
- **Render a 2×**: el texto queda nítido en pantallas densas. El umbral de foto (1,15×) se mide sobre 1080×1350, que es lo que se ve en un celular.
- **`is_real_image()` e `is_low_trust()`** (en `filter_images.py`) están validados y no se tocan; los ajustes van en funciones o scripts nuevos (por eso `fotos_hd.py` es aparte).
- **Dedupe de color no destructivo**: se probaron umbral fijo, z-score y color+estructura; ninguno separó "misma foto" de "mismo fondo". La decisión es visual (Paso 4.4).
- **Imagen única por portada, nunca collage**: el collage de 2–4 fotos se validó como genérico en 3 casos reales.
