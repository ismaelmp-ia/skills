#!/usr/bin/env python3
"""
generate-carousel-kieai.py — Generador de carruseles con Kie AI (nano-banana-pro)
Genera slides cinematográficos con pools de variación: cada bundle_id elige
automáticamente un set distinto de metáforas visuales, evitando repetición
entre carruseles.

Uso:
    py scripts/generate-carousel-kieai.py <bundle_id>
    py scripts/generate-carousel-kieai.py <bundle_id> --regenerate-slides "2,4"
"""

import os, sys, re, json, time, argparse, hashlib, requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

PROJECT_ROOT = Path(__file__).parent.parent

def _leer_marca() -> dict:
    """Marca del usuario: mi-marca.json junto al skill. Si no existe, avisa."""
    ruta = PROJECT_ROOT / "mi-marca.json"
    if not ruta.exists():
        print("ERROR: falta mi-marca.json. Copiá marca.ejemplo.json a mi-marca.json "
              "y poné el nombre de tu marca (o pedíselo al skill).", file=sys.stderr)
        sys.exit(1)
    return json.loads(ruta.read_text(encoding="utf-8"))

MARCA = _leer_marca().get("nombre", "TU MARCA")
OUTPUTS_DIR  = PROJECT_ROOT / "outputs" / "bundles"

KIE_API_BASE    = "https://api.kie.ai/api/v1/jobs"
KIE_CREATE_TASK = f"{KIE_API_BASE}/createTask"
KIE_RECORD_INFO = f"{KIE_API_BASE}/recordInfo"

ASPECT_RATIO      = "4:5"
RESOLUTION        = "2K"
FORMAT            = "png"
MAX_POLL_ATTEMPTS = 80
POLL_INTERVAL     = 6

# ══════════════════════════════════════════════════════════════════════════════
# PALETAS DE COLOR POR CARRUSEL
# El color es el diferenciador más visible entre carruseles.
# Cada bundle_id recibe UNA paleta que se aplica a TODOS sus slides.
# Así el carrusel completo tiene un tono distinto al anterior.
# ══════════════════════════════════════════════════════════════════════════════
COLOR_PALETTES = [
    {   # Paleta 0 — AZUL ELÉCTRICO
        "name": "Azul eléctrico",
        "background": "Deep space black (#030214) with VIVID ELECTRIC BLUE nebula — blue dominates 70% of the atmosphere. Purple depth layers at edges. Dense star field.",
        "primary": "Electric blue #00AAFF",
        "secondary": "Neon cyan #00E8FF",
        "accent": "Orange #FF8723 for impact words only",
        "glow": "Strong electric blue glow on protagonist. Blue halos. Blue volumetric light beams.",
        "forbidden_colors": "NO green, NO red, NO pink — only blue, cyan, orange, white",
    },
    {   # Paleta 1 — PÚRPURA PROFUNDO (misterioso, poderoso)
        "name": "Púrpura profundo",
        "background": "Deep space black with VIVID PURPLE and VIOLET nebula — purple dominates 70% of the atmosphere. Deep magenta at edges. Bright white stars scattered densely.",
        "primary": "Electric purple #9B00FF",
        "secondary": "Neon violet #CC44FF",
        "accent": "Bright white and orange #FF8723 for impact words",
        "glow": "Strong purple-violet glow on protagonist. Magenta halos. Purple volumetric rays.",
        "forbidden_colors": "NO blue, NO teal — only purple, violet, magenta, orange, white",
    },
    {   # Paleta 2 — VERDE TEAL / HACKER (futurista, técnico, peligroso)
        "name": "Verde teal hacker",
        "background": "Deep space black with VIVID TEAL and EMERALD GREEN nebula — teal-green dominates 70% of the atmosphere. Dark edges fading to pure black. Matrix-like feel.",
        "primary": "Neon teal #00FFD0",
        "secondary": "Electric green #00FF88",
        "accent": "Orange #FF8723 for strong contrast on impact words",
        "glow": "Strong teal-green glow on protagonist. Green halos. Teal volumetric light.",
        "forbidden_colors": "NO blue, NO purple — only teal, green, orange, white",
    },
    {   # Paleta 3 — NARANJA CÓSMICO (urgente, caliente, energético)
        "name": "Naranja cósmico",
        "background": "Deep space black with INTENSE ORANGE and AMBER nebula — warm orange dominates 70% of the atmosphere. Deep red at edges. Glowing ember-like stars.",
        "primary": "Neon orange #FF8723",
        "secondary": "Electric amber #FFCC00",
        "accent": "Pure white for headline text, electric blue #00AAFF for secondary accents",
        "glow": "Strong orange glow on protagonist. Amber halos. Warm volumetric fire-light.",
        "forbidden_colors": "NO purple, NO green — only orange, amber, red, white, small blue accents",
    },
]


def pick_color_palette(bundle_id: str) -> dict:
    """Elige la paleta de color del carrusel completo basada en bundle_id."""
    h = int(hashlib.md5(f"palette:{bundle_id}".encode()).hexdigest(), 16)
    return COLOR_PALETTES[h % len(COLOR_PALETTES)]

# ══════════════════════════════════════════════════════════════════════════════
# POOLS DE VARIACIÓN — 4 metáforas distintas por tipo de slide
# El índice (0-3) se elige con hash(bundle_id) para garantizar variedad
# entre carruseles y consistencia dentro del mismo carrusel.
# ══════════════════════════════════════════════════════════════════════════════

VARIATION_POOLS = {

    # ── HOOK (slide 1) ────────────────────────────────────────────────────────
    "hook": [
        # Variante 0: Tipografía masiva + rayo de luz
        {
            "protagonist": "A single razor-thin vertical beam of pure white light cutting through center-right, from top to bottom. Electric blue halo glowing around it. Minimal. Powerful. Nothing else competes.",
            "composition": "TYPOGRAPHY-DOMINANT: Text fills 70% of the slide. LEFT-aligned, stacked vertically — each keyword on its own line, ultra-bold condensed font, massive scale. The light beam sits quietly on the right third, supporting rather than competing.",
            "typography": "ULTRA BOLD condensed display typeface. Main words: white. One keyword: electric blue. Subtitle: small, gray, bottom-left. Headline should feel like a movie title card.",
            "mood": "Magazine cover meets blockbuster title. Pure typographic impact.",
            "accent": "Electric blue #00AAFF on white",
        },
        # Variante 1: Monolito colosal
        {
            "protagonist": "A colossal glowing electric-blue monolith/obelisk standing tall against deep space. Intricate circuit-like patterns etched into its surface, glowing cyan from within. Energy streams rise from its peak. Small dim structures far below — dwarfed and insignificant.",
            "composition": "Monolith occupies RIGHT half of slide (rule of thirds). Text on LEFT side, upper-left quadrant. Bold, left-aligned headline. Subtitle smaller below. The monolith's glow spills light into the text zone.",
            "typography": "Bold sans-serif. White headline, one word in electric blue. Small supporting text below. Slight neon glow on headline.",
            "mood": "Absolute dominance. One entity above all others. Awe-inspiring scale.",
            "accent": "Electric blue #00AAFF dominant",
        },
        # Variante 2: Hyperspeed — perspectiva de salto
        {
            "protagonist": "First-person perspective of a hyperspeed jump through stars — star trails becoming long white streaks converging to a central vanishing point. Electric blue energy field at the edges of the frame. The viewer is being launched FORWARD through space.",
            "composition": "Full-bleed hyperspeed visual takes 60% of slide. Text overlaid on top third where stars are sparse — headline bold and centered. Subtitle below. The converging star trails draw the eye to center.",
            "typography": "Bold condensed white font. One key word in cyan/neon. Large scale. Feels like speed.",
            "mood": "Launch. Velocity. Something big is happening RIGHT NOW.",
            "accent": "Neon cyan #00E8FF and pure white",
        },
        # Variante 3: Ojo cósmico
        {
            "protagonist": "An enormous cosmic eye formed from a galaxy or nebula — the iris made of swirling blue and purple nebula gases, the pupil a dark void with a single point of intense white light. Staring directly at the viewer. Otherworldly and intense.",
            "composition": "The cosmic eye occupies the lower 60% of the slide, centered. Text sits in the upper 40% — headline bold, white, centered above the eye. The eye seems to look up at the text.",
            "typography": "Centered bold white type. Key word in electric blue. Feels like the eye is reading the headline.",
            "mood": "Something is watching. Awareness. Intelligence awakening. Unsettling power.",
            "accent": "Deep purple and electric blue",
        },
    ],

    # ── INTRO (slide 2) ───────────────────────────────────────────────────────
    "intro": [
        # Variante 0: Figura humana de circuitos — split layout
        {
            "protagonist": "A glowing human silhouette — upper half of a figure made entirely of electric blue circuit lines, neurons, and data connections. Like a human made of pure light and data. Faces slightly LEFT. Radiates cyan-blue energy. Particle trails around it.",
            "composition": "SPLIT PANEL: LEFT 55% dark zone with text. RIGHT 45% occupied by the glowing figure. A subtle vertical electric blue line divides the zones. Headline upper-left, bold. Supporting text below headline, smaller.",
            "typography": "Bold sans-serif. White headline. 1-2 keywords in neon cyan. Clean. Readable. Left-aligned.",
            "mood": "Human meets AI. Intelligence amplified. Editorial tech magazine feel.",
            "accent": "Neon cyan #00E8FF",
        },
        # Variante 1: Cerebro con anillos orbitales
        {
            "protagonist": "A glowing human brain made of electric blue light and energy circuits. Neurons firing as bright neon blue lightning arcs. The brain floats in space, radiating intelligence. Orbital rings of light circle it like a planet's rings.",
            "composition": "Brain centered in lower 50% of slide, large (40% height). Text in upper portion — headline upper-left, bold. Supporting facts below. The brain's glow illuminates the bottom of the text.",
            "typography": "Bold white headline upper section. Key terms in electric blue. Supporting text muted white, smaller.",
            "mood": "Intelligence. Limitless potential. The power of mind and machine.",
            "accent": "Electric blue #00AAFF",
        },
        # Variante 2: Red neuronal como constelación
        {
            "protagonist": "A neural network visualization spread across the slide like a star constellation — nodes as bright blue-white stars, connections as glowing electric blue lines between them. Some nodes pulse orange. The network extends across 60% of the slide.",
            "composition": "Network constellation fills the background but stays semi-transparent/dark so text reads clearly. Headline at top, large and bold. Subtext centered below. The network feels like it surrounds the text.",
            "typography": "Bold centered white type. Key concept in electric blue. Large scale. The network feels like it's connecting to the words.",
            "mood": "Connection. Everything linked. The new intelligence grid.",
            "accent": "Electric blue nodes and orange pulse points",
        },
        # Variante 3: Hélice de ADN de luz
        {
            "protagonist": "A DNA double helix made entirely of neon blue and cyan light — glowing, twisting upward through the right side of the slide. Each base pair glows with electric blue energy. It suggests evolution, code, fundamental change.",
            "composition": "DNA helix on the RIGHT third, running from bottom to top. Text on the LEFT two thirds — headline upper-left, bold. Supporting text below. The helix glows brightest where it meets the center of the slide.",
            "typography": "Bold left-aligned white type. One key word in orange (for contrast against all the blue). Clean and direct.",
            "mood": "Something fundamental is changing. Evolution. Rewriting the code.",
            "accent": "Neon cyan helix, orange accent word",
        },
    ],

    # ── PROBLEMA (slide 3) ────────────────────────────────────────────────────
    "problema": [
        # Variante 0: Muro agrietado con brillo interno
        {
            "protagonist": "A cracked, fractured wall of dark stone or ice running diagonally across the lower-right third. The crack glows orange-red from within — like lava or fire pushing through from the other side. Above the crack: darkness. Below: the glow.",
            "composition": "Diagonal crack runs lower-left to upper-right at ~30 degrees. Text occupies UPPER-LEFT two thirds — clean dark space. Headline top-left, bold. Problem statements listed below. Orange glow particles float upward from crack.",
            "typography": "Heavy bold white headline. Problem keywords in muted orange. Body text small and gray. Heavy contrasts.",
            "mood": "Tension. Weight. Something is broken. Dark editorial. No solution yet.",
            "accent": "Orange #FF8723 and dark red — NO blue on this slide",
        },
        # Variante 1: Torre azul dominante vs estructuras pequeñas
        {
            "protagonist": "One massive glowing BLUE tower of light soaring high in space — energy streams flowing upward, intense crown glow at peak. Three tiny, dim, nearly invisible small cubes far to the right — they look irrelevant beside it. The contrast is extreme.",
            "composition": "Blue tower slightly left of center, large (45% of slide height). Tiny structures to the far right. Headline at top. Problem statements below the headline. The scale difference makes the problem visceral.",
            "typography": "Bold white headline at top. Key contrast words in electric blue. Scale of text mirrors scale of visual.",
            "mood": "The gap is not a race — it's a different dimension. Overwhelming difference.",
            "accent": "Electric blue dominant, tiny gray accents for the small elements",
        },
        # Variante 2: Laberinto desde arriba
        {
            "protagonist": "An aerial view of a complex dark maze — walls made of dark stone with faint blue bioluminescence. One single path glows bright electric blue through the maze, winding but visible. All other paths are dead ends and darkness.",
            "composition": "Maze fills the lower 55% of the slide. Text in upper 45% — headline bold and clear. The single glowing blue path feels like a metaphor for the solution being revealed later.",
            "typography": "Bold white text upper section. Problem keywords in muted orange. Clean and readable against dark sky above maze.",
            "mood": "Lost. Confused. There's a way out but it's hard to find. The problem as a maze.",
            "accent": "Electric blue path against dark gray maze",
        },
        # Variante 3: Reloj de arena casi vacío
        {
            "protagonist": "An elegant hourglass made of pure blue-white light — almost empty, last grains of luminous sand falling. The bottom bulb glows intensely where the sand accumulates. The glass itself is transparent, ethereal. Floats in dark space.",
            "composition": "Hourglass centered, large (40% of slide). Text above — headline top-left or top-center, bold. Supporting text below headline. The urgency of nearly-empty time dominates the feel.",
            "typography": "Bold white headline. Urgency words in orange. Small gray supporting text. Sparse — the visual does the heavy lifting.",
            "mood": "Time is running out. Urgency. If you don't act now, it will be too late.",
            "accent": "Cyan-white hourglass, orange accent",
        },
    ],

    # ── DATO (slide 4) ────────────────────────────────────────────────────────
    "dato": [
        # Variante 0: Terminal flotante en spotlight
        {
            "protagonist": "A terminal/command prompt window floating in a circular blue spotlight — dark background inside showing bright electric blue monospace text with a command or code snippet. Window slightly rotated 3-5 degrees. Blue drop shadow. Code fragments float nearby.",
            "composition": "STAGE SPOTLIGHT: Terminal window center-stage (center-slightly-left) in spotlight. Circular blue glow behind it. Headline above in upper third. 1-2 bullet stats below the terminal. Empty dark space on sides.",
            "typography": "Monospace/code-style font inside terminal. Bold sans-serif white headline above. Tech-forward. Precise.",
            "mood": "Technical reveal. Here is the proof. Precision and power.",
            "accent": "Electric blue #00AAFF terminal glow",
        },
        # Variante 1: Número gigante flotante
        {
            "protagonist": "An enormous glowing NUMBER or PERCENTAGE (e.g., '90%' or '10X') sculpted from pure electric blue light — 3D, with depth and glow. It floats in the center of the slide, casting blue light around it. The number IS the visual.",
            "composition": "Giant number occupies center 50% of slide. Headline text at top, smaller but bold. Context text below the number. The number commands attention — everything else supports it.",
            "typography": "The number itself is the largest typographic element. Supporting headline bold white above. Context text small below. The hierarchy is clear: number first.",
            "mood": "The data is undeniable. This number changes everything. Proof.",
            "accent": "Electric blue number, white supporting text",
        },
        # Variante 2: Telescopio apuntando a una estrella
        {
            "protagonist": "A sleek futuristic telescope or targeting reticle — made of glowing blue light — pointed toward a specific bright star in the upper corner. The targeting crosshairs glow electric blue. The specific star glows intensely orange-white, surrounded by other dim stars.",
            "composition": "Telescope/reticle in lower-left, angled upward toward the highlighted star (upper-right). Text in the clear dark space on the left and center. Headline bold, left-aligned. Data points or facts listed below.",
            "typography": "Bold white headline. Data numbers in electric blue. The precision of the telescope mirrors the precision of the data.",
            "mood": "Pinpoint focus. We found the signal in the noise. This specific thing matters.",
            "accent": "Electric blue targeting, orange-white star",
        },
        # Variante 3: Plano técnico de luz
        {
            "protagonist": "A technical blueprint or schematic made entirely of glowing electric blue light lines on a near-black background — like an architect's drawing but futuristic and beautiful. Clean geometric lines form shapes suggesting a system, a product, or a structure.",
            "composition": "Blueprint fills the right 55% of slide. Text on the left 45% — headline bold left-aligned, data points stacked below. The precision of the blueprint reinforces the precision of the data.",
            "typography": "Bold white headline on left. Key data in electric blue. Secondary info in muted white. Technical and clean.",
            "mood": "Designed. Deliberate. This was engineered, not accidental. The data is the plan.",
            "accent": "Electric blue blueprint lines",
        },
    ],

    # ── CONTRAPUNTO (slide 5) ─────────────────────────────────────────────────
    "contrapunto": [
        # Variante 0: Ola azul vs ola naranja — división central
        {
            "protagonist": "Two abstract energy waves facing each other across a central vertical seam: LEFT side — a rising pillar of structured electric blue energy, controlled and upward. RIGHT side — a chaotic burst of orange-red energy, wild and questioning. At the seam: thin white collision line.",
            "composition": "Vertical white seam divides slide into two zones. LEFT: blue energy + pro-text stack. RIGHT: orange energy + counter-text. BOTTOM CENTER spanning full width: the key question/counterpoint statement.",
            "typography": "Bold white for both sides. Blue-tinted left text, orange-tinted right text. Center bottom: largest text, white, centered. Visual debate.",
            "mood": "Tension between two valid forces. The hard question. Both sides matter.",
            "accent": "Blue #00AAFF left / Orange #FF8723 right",
        },
        # Variante 1: Dos planetas en oposición
        {
            "protagonist": "Two planets facing each other in space — LEFT: a cool electric blue planet, structured, with visible tech-like surface details and a faint orbital ring. RIGHT: a warm orange-red planet, chaotic, with swirling storm clouds. They orbit near each other, a gravitational tension between them.",
            "composition": "Blue planet in left-center, orange planet in right-center. A faint gravitational distortion line between them. Text above both planets — headline spanning full width. Below: two contrasting statements aligned under each planet.",
            "typography": "Full-width bold white headline at top. Two smaller contrasting statements below — one per planet zone. The planets visualize the textual contrast.",
            "mood": "Two worlds. Two realities. Which one do you live in?",
            "accent": "Blue planet left, orange planet right",
        },
        # Variante 2: Balanza de energía
        {
            "protagonist": "An elegant scale/balance made of glowing blue light — two sides, one visibly heavier (tilted down), loaded with glowing electric blue energy orbs. The other side is lighter, with dim gray orbs. The scale itself is geometric and futuristic.",
            "composition": "Scale centered in lower 50% of slide. Text above — headline bold and centered. The heavy/light contrast of the scale mirrors the content's counterpoint. Below scale: two brief contrasting facts.",
            "typography": "Bold white centered headline. Two contrasting facts: one in electric blue (heavy side), one in muted gray (light side). The visual weight matches.",
            "mood": "Not everything is equal. The balance has shifted. This changes the equation.",
            "accent": "Electric blue heavy side, gray light side",
        },
        # Variante 3: Rey de ajedrez azul vs rey naranja
        {
            "protagonist": "Two chess king pieces facing each other on an infinite dark board — LEFT: a tall glowing BLUE king, made of light, elegant and powerful. RIGHT: a smaller, dimmer ORANGE king, still standing but clearly at a disadvantage. The electric blue king radiates dominance.",
            "composition": "The two kings face each other at center of slide, in lower 40%. Text above — headline bold and centered. The size difference between kings makes the contrast visual. Supporting text below.",
            "typography": "Bold centered white headline. Key contrasting words: one in electric blue, one in muted orange. Clean and direct.",
            "mood": "Strategy. Dominance. One move changes everything. Choose your side.",
            "accent": "Electric blue dominant king, muted orange smaller king",
        },
    ],

    # ── RECOMPENSA (slide 6) ──────────────────────────────────────────────────
    "recompensa": [
        # Variante 0: Camino de luz — perspectiva ascendente
        {
            "protagonist": "A perspective view of a path/road made of light particles extending from the bottom-center of the slide upward toward a radiant glowing light source at the upper center. The path is a trail of luminous particles — like a meteor trail going forward. Strong vanishing point composition.",
            "composition": "VANISHING POINT: Path starts bottom-center, extends to upper-center (the light). Text floats LEFT and RIGHT of the path. Headline in upper portion, centered above the light. Benefits listed on LEFT side of path, stacked.",
            "typography": "Clean white type. Slightly lighter weight — more hopeful, less heavy. Key benefit in electric blue. No orange. Open and inviting.",
            "mood": "Relief. Possibility. The way forward is clear. Aspirational and grounded.",
            "accent": "Warm white light source, electric blue highlights",
        },
        # Variante 1: Portal de luz abriéndose
        {
            "protagonist": "A radiant PORTAL OF LIGHT opening in space — a circular gateway filled with blinding white-blue light. Energy rays burst outward from the portal like a star. The opening reveals infinite bright space beyond. Neon blue rings of energy surround the portal, floating particles.",
            "composition": "Portal centered in lower-center, large (40%). Title text upper-left. Benefits or insights listed on the left side. The portal feels like the culmination of the whole carousel — the answer revealed.",
            "typography": "Bold white headline upper-left. Key benefit phrases in electric blue. Clean and direct.",
            "mood": "Opportunity revealed. The moment to act. Your future opening up.",
            "accent": "White-blue portal light, electric blue rings",
        },
        # Variante 2: Cima de montaña al amanecer
        {
            "protagonist": "A dramatic mountain peak silhouetted against a stunning dawn sky — the horizon glows electric blue and warm white, the sky transitions from deep space black at top to the glowing sunrise at the horizon. A lone figure stands at the summit (optional, very small). Inspiring and earned.",
            "composition": "Mountain fills lower 40% as dark silhouette. The glowing horizon sits at the 60% mark. Text in the sky zone — headline bold and centered against the dark upper sky. Benefit statements below, spaced.",
            "typography": "Bold white centered headline against dark sky. Key words in electric blue. Feels earned and aspirational.",
            "mood": "Achievement. You made it. The hard part is behind you. The view is worth it.",
            "accent": "Electric blue horizon glow, white dawn light",
        },
        # Variante 3: Llave de luz
        {
            "protagonist": "An elegant oversized KEY made of pure electric blue light — 3D, geometric, glowing. It floats in space, oriented horizontally, as if about to unlock something. On its right side: a faint glowing keyhole in a dark surface, about to open. Light pours through the keyhole.",
            "composition": "Key centered in slide, large (35-40%). Text above — headline bold. Text below key — the benefits or payoff. The key and keyhole together tell the story: this is the unlock.",
            "typography": "Bold white headline above. Key benefits listed below in white. One key word in electric blue. Precise and clear.",
            "mood": "This is the unlock. You now have the key. The door is about to open.",
            "accent": "Electric blue key, warm white keyhole light",
        },
    ],

    # ── CTA (slide 7) ─────────────────────────────────────────────────────────
    "cta": [
        # Variante 0: Signo ? en 3D naranja + glow cálido
        {
            "protagonist": "An enormous 3D QUESTION MARK sculpted from solid neon orange light — tilted slightly forward (perspective), leaning toward the viewer. Bold, with depth and a strong orange-to-white gradient glow. It casts an orange glow on surrounding space. Speech bubble icons float faintly below it.",
            "composition": f"Question mark occupies RIGHT half, large and forward-leaning. LEFT half: CTA question text, stacked and large. Below text: downward arrow chevron in orange. Bottom strip: {MARCA} branding centered, white. Warm orange glow unifies both halves.",
            "typography": f"Conversational bold white type. One key word in orange. Downward arrow. {MARCA} in clean white at very bottom.",
            "mood": "Warmth. Direct. Personal. I am talking to YOU. What do you think?",
            "accent": "Orange #FF8723 dominant — warmest slide of the carousel",
        },
        # Variante 1: Mano abierta hacia la cámara
        {
            "protagonist": "An open human hand reaching TOWARD the camera — made of electric blue light and energy, ethereal and non-realistic. The palm glows brightest, as if offering something. Energy particles drift from the fingertips. Inviting, not threatening.",
            "composition": f"The glowing hand occupies the RIGHT-CENTER of the slide. CTA question text on the LEFT. Below: interaction cue (arrow or comment icons). {MARCA} branding at very bottom, centered.",
            "typography": f"Bold white left-aligned question text. Key invitation word in electric blue. {MARCA} clean at bottom.",
            "mood": "An invitation. Come closer. Your answer matters. We want to hear you.",
            "accent": "Electric blue hand, warm white palm glow",
        },
        # Variante 2: Puerta entreabierta con luz cálida
        {
            "protagonist": "A large dark door — slightly ajar — with warm orange-white light pouring through the gap from the other side. The door itself is dark, almost black. The light from within creates a dramatic glow on the floor and walls around it. The gap invites you in.",
            "composition": f"Door in RIGHT half, large. The light gap is the focal point. CTA question text on LEFT. Bottom: {MARCA} branding centered. The door metaphor: something is open, but you have to choose to enter.",
            "typography": f"Bold white question text on left. Key word in orange (matching the warm light). {MARCA} at bottom.",
            "mood": "Opportunity. Invitation. A door is open — are you going through? Your move.",
            "accent": "Warm orange-white door light",
        },
        # Variante 3: Multitud de siluetas con globos de diálogo
        {
            "protagonist": "A crowd of small glowing silhouettes — people made of dim electric blue light — spread across the lower half. Above them: multiple speech bubble icons glowing electric blue and orange, floating upward. The scene suggests conversation, community, engagement.",
            "composition": f"Crowd fills lower 35% of slide. Speech bubbles float in the middle zone. CTA question text sits in the upper 40% — bold, centered. {MARCA} branding at very bottom.",
            "typography": f"Bold centered white CTA question. Key question words in orange. {MARCA} at bottom. Centered layout for community feel.",
            "mood": "Community. Everyone is part of this. Your voice adds to the conversation.",
            "accent": "Electric blue silhouettes, orange speech bubbles",
        },
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
# SELECCIÓN DE VARIANTE POR BUNDLE_ID
# Usa hash del bundle_id para elegir variantes de forma determinista
# Cada slide position usa un offset distinto para maximizar diversidad visual
# ══════════════════════════════════════════════════════════════════════════════

def pick_variant_index(bundle_id: str, slide_number: int, pool_size: int = 4) -> int:
    """
    Elige el índice de variante de forma determinista basado en bundle_id y slide_number.
    - Mismo bundle_id + mismo slide → mismo índice (reproducible)
    - Distinto bundle_id → índices distintos (variedad entre carruseles)
    - Cada slide usa un offset único para evitar que todos escojan la misma variante
    """
    seed = f"{bundle_id}:slide{slide_number}"
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    return h % pool_size


# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISIS DE CONTENIDO — extrae el visual más icónico del texto del slide
# Esto hace que cada imagen refleje lo que el slide DICE, no solo su tipo.
# ══════════════════════════════════════════════════════════════════════════════

CONTENT_VISUAL_RULES = [
    # Seguridad / hacking / ciberseguridad
    (["hack", "exploit", "vulnerab", "breach", "kernel", "openbsd", "freebsd", "linux", "root", "cifrado", "malware", "zero-day", "bug", "grieta"],
     "A cracked glowing shield or broken digital padlock made of neon light — the crack pulses with electric energy escaping through it. OR a dark terminal screen floating in space showing breach code in green/teal text. Cybersecurity and digital intrusion are the visual theme."),

    # Precio / coste / dinero
    (["$50", "$1,000", "$2,000", "$100m", "costó", "costo", "coste", "precio", "millones", "€", "dollars"],
     "An enormous glowing price tag or currency symbol ($) sculpted from neon light floats in dark space. The number itself is the protagonist — large, 3D, radiating energy. The cheapness of the price vs the magnitude of the action creates the visual tension."),

    # Empresas tecnológicas / gigantes corporativos
    (["apple", "google", "microsoft", "amazon", "nvidia", "meta", "openai", "anthropic", "glasswing"],
     "Multiple corporate skyscrapers or monolithic towers of light rising from a dark planet surface — some towers glow bright blue (dominant), others are dim and small (scared, losing). A skyline of tech giants in space, power dynamics visible through scale and brightness."),

    # Velocidad / tiempo / urgencia
    (["una noche", "antes del desayuno", "minutos", "segundos", "semanas", "instantáneo", "ya empezó"],
     "A dramatic hourglass made of glowing light — almost empty, the last grains of luminous sand falling. OR a clock face made of electric blue energy, hands spinning. Time urgency is the protagonist."),

    # Autonomía / IA tomando decisiones
    (["autónomo", "autonomo", "decide", "ejecuta", "sin supervisión", "solo", "por su cuenta", "toma decisiones"],
     "A glowing robotic hand or AI arm made of electric light reaching forward — independent, no human hand guiding it. It acts alone. The hand is the protagonist, floating in dark space, purposeful and self-directed."),

    # Control / acceso total / dominio
    (["acceso root", "acceso total", "control total", "domina", "lidera", "aplasta"],
     "An enormous glowing KEY made of electric light unlocking a massive dark door or vault — light pours through the unlocking gap. The key IS the protagonist, large and powerful, filling the right half of the slide."),

    # Escondido / secreto / oculto
    (["escondió", "escondido", "oculto", "secreto", "nadie sabía", "nadie vio", "sin que nadie"],
     "A dark curtain or veil made of deep space fabric being torn open — bright electric light bursts through the tear. Something was hidden and is now being revealed. The tear/reveal IS the protagonist."),

    # Miedo / pánico / asustado
    (["asustados", "pánico", "panic", "preocupados", "preocupación", "alerta", "emergencia"],
     "Warning signals or alarm beacons made of red-orange neon light scattered across dark space — multiple flashing alerts, urgent and intense. OR a single massive red warning icon pulsing in dark space. Fear and urgency are the visual."),

    # Código / programación / software
    (["código", "code", "comando", "script", "programa", "software", "algoritmo", "función"],
     "A floating terminal or code editor window in space — dark background, bright neon syntax-highlighted code visible inside. The window floats at an angle, casting light. Code IS the visual protagonist."),

    # Red / internet / conectividad
    (["internet", "remoto", "red ", "network", "conectado", "desde cualquier punto", "global"],
     "A glowing web of connections — nodes of light spread across a dark sphere (representing the globe) with electric blue connection lines linking them. The network IS the protagonist, pulsing with live data."),

    # Datos / estadísticas / números grandes
    (["27 años", "100m", "10x", "%", "1,000", "2,000", "millones", "miles", "billones"],
     "A massive glowing NUMBER sculpted from electric 3D light dominates the center of the slide. The number radiates neon energy and is so large it demands attention. The statistic IS the image."),
]


def extract_content_visual(content: str, title: str) -> str:
    """
    Analiza el contenido del slide y devuelve una descripción visual
    específica al tema. Retorna cadena vacía si no encuentra match.
    """
    text = (content + " " + title).lower()
    for keywords, visual in CONTENT_VISUAL_RULES:
        if any(k in text for k in keywords):
            return visual
    return ""


def get_slide_pool_key(slide_title: str, slide_type: str, slide_number: int, total: int) -> str:
    """Mapea título y tipo de slide a la clave del pool de variación."""
    t = slide_title.lower()
    if slide_type == "hook":  return "hook"
    if slide_type == "cta":   return "cta"
    if any(k in t for k in ("intro", "contexto", "qué es", "que es", "presentación")): return "intro"
    if any(k in t for k in ("problema", "error", "brecha", "reto", "pero", "mal")):    return "problema"
    if any(k in t for k in ("dato", "clave", "cifra", "número", "stat", "dominio", "disponible", "ya")): return "dato"
    if any(k in t for k in ("contrapunto", "debate", "versus", "riesgo", "control", "pregunta")): return "contrapunto"
    if any(k in t for k in ("recompensa", "micro", "beneficio", "oportunidad", "lo que", "cambia", "cambia")): return "recompensa"
    # Fallback por posición relativa
    position_ratio = slide_number / total
    if position_ratio <= 0.25:  return "intro"
    if position_ratio <= 0.50:  return "problema"
    if position_ratio <= 0.65:  return "dato"
    if position_ratio <= 0.80:  return "contrapunto"
    return "recompensa"


def build_prompt(slide: dict, slide_type: str, total: int, bundle_id: str) -> str:
    """
    Construye el prompt completo para Kie AI.
    - Paleta de color: elegida por bundle_id (diferenciador principal entre carruseles)
    - Variante visual: elegida por bundle_id + slide_number (diferenciador secundario)
    """
    title        = slide["title"]
    content      = slide["content"]
    slide_number = slide["number"]

    # Limpiar markup de color {bl:texto} → texto
    content_clean = re.sub(r'\{[a-z]+:([^}]+)\}', r'\1', content)

    # Paleta del carrusel completo
    palette = pick_color_palette(bundle_id)

    # Variante visual del slide
    pool_key    = get_slide_pool_key(title, slide_type, slide_number, total)
    pool        = VARIATION_POOLS[pool_key]
    variant_idx = pick_variant_index(bundle_id, slide_number, len(pool))
    variant     = pool[variant_idx]

    # Visual específico al contenido (prioridad sobre el genérico)
    content_visual = extract_content_visual(content_clean, title)
    if content_visual:
        protagonist_block = f"""CONTENT-SPECIFIC VISUAL (USE THIS — it reflects what the slide talks about):
{content_visual}

Composition reference (adapt to the content visual above):
{variant["composition"]}"""
    else:
        protagonist_block = f"""PROTAGONIST VISUAL:
{variant["protagonist"]}

COMPOSITION:
{variant["composition"]}"""

    # Branding en el último slide
    genesis_branding = ""
    if slide_number == total:
        genesis_branding = 'BRAND SIGNATURE: At the very bottom-center of the slide, place the word f"{MARCA}" in small clean white bold letters. Just the word — nothing else.\n\n'

    return f"""You are generating a premium cinematic Instagram carousel slide.
Format: 1080x1350px vertical (4:5 ratio). Style: sci-fi movie poster. Dark. Powerful. NOT watercolor. NOT corporate. NOT flat design.

══ COLOR ATMOSPHERE — {palette["name"].upper()} ══
The ENTIRE slide must use this color scheme — it defines the mood of this carousel:
- Background: {palette["background"]}
- Primary color: {palette["primary"]}
- Secondary color: {palette["secondary"]}
- Accent: {palette["accent"]}
- Glow style: {palette["glow"]}
- FORBIDDEN colors: {palette["forbidden_colors"]}

══ VISUAL ELEMENT ══
{protagonist_block}

══ TYPOGRAPHY ══
{variant["typography"]}
- Brand/company names (Claude, ChatGPT, OpenAI, Google, Apple, Anthropic, etc.): render in ORANGE
- Key power words and concepts: render in the primary palette color
- All other text: pure white

══ MOOD ══
{variant["mood"]}

{genesis_branding}══ TEXT TO SHOW IN THE IMAGE (ONLY these words — nothing else) ══
{content_clean}

══ ABSOLUTE RULES ══
- Maximum 3 visual elements total. Lots of dark breathing room. NOT cluttered.
- Text zones must NOT overlap the protagonist visual.
- NO watercolor, NO hand-drawn, NO stock photos, NO clipart, NO charts.
- Stop the scroll in 1 second. Dark. Cinematic. Premium.
- DO NOT write any instructions, labels, or metadata as text in the image.
- ONLY render the exact words from "TEXT TO SHOW IN THE IMAGE" above.
"""


# ══════════════════════════════════════════════════════════════════════════════
# PARSING DEL REPURPOSE-PACK.MD
# ══════════════════════════════════════════════════════════════════════════════

def parse_pack(bundle_path: Path):
    md = bundle_path / "repurpose-pack.md"
    if not md.exists():
        print(f"❌ No se encontró {md}"); return None
    content = md.read_text(encoding="utf-8")
    m = re.search(
        r'##\s*[^\n]*?(?:Carrusel|Instagram|📱)[^\n]*?\n+(.*?)(?=\n##\s+[^#]|\Z)',
        content, re.DOTALL | re.IGNORECASE)
    if not m:
        print("❌ Sin sección Carrusel Instagram"); return None
    pattern = r'###\s+SLIDE\s+(\d+)\s*-\s*([^\n]+)\s*\n```\s*\n(.*?)\n```'
    slides  = []
    for mt in re.finditer(pattern, m.group(1).strip(), re.DOTALL):
        slides.append({"number": int(mt.group(1)),
                       "title":  mt.group(2).strip(),
                       "content":mt.group(3).strip()})
    print(f"   ✅ {len(slides)} slides"); return slides


def slide_type(slide: dict, total: int) -> str:
    t, n = slide["title"].lower(), slide["number"]
    if n == 1 or any(k in t for k in ("hook", "portada")): return "hook"
    if n == total or any(k in t for k in ("cta", "cierre")): return "cta"
    return "content"


# ══════════════════════════════════════════════════════════════════════════════
# KIE AI API
# ══════════════════════════════════════════════════════════════════════════════

def create_task(api_key: str, prompt: str) -> str | None:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "nano-banana-pro",
        "input": {
            "prompt": prompt,
            "aspect_ratio": ASPECT_RATIO,
            "resolution": RESOLUTION,
            "output_format": FORMAT
        }
    }
    try:
        r = requests.post(KIE_CREATE_TASK, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        if data.get("code") == 200:
            return data.get("data", {}).get("taskId")
        print(f"   ❌ API error: {data}")
        return None
    except Exception as e:
        print(f"   ❌ Error creando tarea: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   📋 {e.response.text}")
        return None


def poll_task(api_key: str, task_id: str) -> str | None:
    headers = {"Authorization": f"Bearer {api_key}"}
    for attempt in range(MAX_POLL_ATTEMPTS):
        try:
            r = requests.get(KIE_RECORD_INFO, headers=headers,
                             params={"taskId": task_id}, timeout=30)
            r.raise_for_status()
            data  = r.json().get("data") or {}
            state = data.get("state", "")
            if state == "success":
                urls = json.loads(data.get("resultJson", "{}")).get("resultUrls", [])
                return urls[0] if urls else None
            elif state == "fail":
                print(f"   ❌ Falló: {data.get('failMsg', '?')}")
                return None
            else:
                print(f"   ⏳ {state}... ({attempt+1}/{MAX_POLL_ATTEMPTS})")
                time.sleep(POLL_INTERVAL)
        except Exception as e:
            print(f"   ❌ Polling error: {e}")
            time.sleep(POLL_INTERVAL)
    print("   ❌ Timeout"); return None


def download_image(url: str, path: Path) -> bool:
    try:
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"   ❌ Error descargando: {e}"); return False


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_id")
    parser.add_argument("--regenerate-slides", type=str, default=None)
    args = parser.parse_args()

    api_key = os.environ.get("KIE_AI_API_KEY")
    if not api_key:
        print("❌ KIE_AI_API_KEY no configurada en .env"); sys.exit(1)

    bundle_path = OUTPUTS_DIR / args.bundle_id
    out_dir     = bundle_path / "carousel"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"CAROUSEL GENERATOR — {MARCA} × Kie AI")
    print(f"{'='*60}")
    print(f"📦 {args.bundle_id}\n")

    slides = parse_pack(bundle_path)
    if not slides: sys.exit(1)

    total   = len(slides)
    targets = (set(int(x.strip()) for x in args.regenerate_slides.split(","))
               if args.regenerate_slides else set(s["number"] for s in slides))

    # Mostrar paleta y variantes seleccionadas
    palette = pick_color_palette(args.bundle_id)
    print(f"\n{'─'*60}")
    print(f"🎨 PALETA DE COLOR: {palette['name'].upper()}")
    print(f"   Primary: {palette['primary']} | Secondary: {palette['secondary']}")
    print(f"{'─'*60}")
    print("VARIANTES VISUALES POR SLIDE:")
    for slide in slides:
        n = slide["number"]
        stype = slide_type(slide, total)
        pool_key = get_slide_pool_key(slide["title"], stype, n, total)
        v_idx = pick_variant_index(args.bundle_id, n, len(VARIATION_POOLS[pool_key]))
        print(f"  Slide {n:02d} [{pool_key}]: variante {v_idx+1}/4")
    print(f"{'─'*60}\n")

    cost_per_slide = 0.10
    print(f"GENERANDO {len(targets)} SLIDES — estimado ${cost_per_slide*len(targets):.2f}")
    print(f"{'='*60}\n")

    manifest = []
    for slide in slides:
        n = slide["number"]
        if n not in targets: continue

        stype = slide_type(slide, total)
        print(f"🎨 Slide {n:02d} [{stype}]: {slide['title']}")

        prompt = build_prompt(slide, stype, total, args.bundle_id)

        print(f"   📤 Enviando a Kie AI...")
        task_id = create_task(api_key, prompt)
        if not task_id:
            print(f"   ❌ No se pudo crear tarea. Saltando slide {n}.")
            continue

        print(f"   🔄 Task ID: {task_id}")
        img_url = poll_task(api_key, task_id)
        if not img_url:
            print(f"   ❌ No se obtuvo imagen. Saltando slide {n}.")
            continue

        fname = out_dir / f"carousel-{n:02d}.png"
        if download_image(img_url, fname):
            print(f"   ✅ {fname.name}")
            manifest.append({"slide": n, "title": slide["title"],
                             "type": stype, "file": fname.name,
                             "pool": get_slide_pool_key(slide["title"], stype, n, total),
                             "variant": pick_variant_index(args.bundle_id, n) + 1,
                             "source": "kie-ai"})
        else:
            print(f"   ❌ Error descargando slide {n}")

    (bundle_path / "manifest.json").write_text(
        json.dumps({"bundle_id": args.bundle_id,
                    "generated": datetime.now().isoformat(),
                    "generator": "genesis-kieai-v2-variation-pools",
                    "total_slides": total,
                    "slides": manifest},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"✅  {len(manifest)} slides generados")
    print(f"💰  ~${cost_per_slide*len(manifest):.2f} USD")
    print(f"📁  {out_dir}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
