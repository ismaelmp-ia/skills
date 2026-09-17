#!/bin/bash
# Prepara el skill: entorno de Python, librerías y tipografías.
# Se corre una sola vez. Mac y Linux.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
echo ""
echo "── Preparando LinkedIn Post Generator ──"

# 1. Python 3.10+
echo "→ Buscando Python 3.10 o superior..."
PY=""
for c in /usr/bin/python3 python3 python3.12 python3.11; do
  command -v "$c" >/dev/null 2>&1 || continue
  "$c" -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null && { PY="$c"; break; }
done
[ -z "$PY" ] && { echo "  ❌ No encontré Python 3.10+. Instalalo desde https://python.org"; exit 1; }
echo "  ✅ $($PY --version)"

# 2. Entorno propio del skill, para no tocar el Python del sistema
echo "→ Instalando librerías (numpy, requests, Pillow)..."
"$PY" -m venv "$DIR/.venv" 2>/dev/null || { echo "  ❌ No pude crear el entorno virtual"; exit 1; }
"$DIR/.venv/bin/python" -m pip install --quiet --upgrade pip
"$DIR/.venv/bin/python" -m pip install --quiet numpy requests pillow
echo "  ✅ Librerías listas"

# 3. Tipografías (Google Fonts, licencia SIL OFL)
FONTS="$DIR/assets/fonts"
mkdir -p "$FONTS"
_ok() { [ -f "$1" ] && [ "$(wc -c < "$1")" -gt 50000 ] && ! head -c 1 "$1" | grep -q "<"; }
_baja() {
  _ok "$FONTS/$1" && return 0
  echo "→ Descargando $1..."
  curl -sL "$2" -o "$FONTS/$1"
  _ok "$FONTS/$1" || { echo "  ❌ Falló la descarga de $1 (revisá tu conexión)"; rm -f "$FONTS/$1"; exit 1; }
}
_baja "Anton.ttf"          "https://fonts.gstatic.com/s/anton/v27/1Ptgg87LROyAm0K0.ttf"
_baja "SpaceGrotesk.ttf"   "https://fonts.gstatic.com/s/spacegrotesk/v22/V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj7oUUsj.ttf"
_baja "JetBrainsMono.ttf"  "https://fonts.gstatic.com/s/jetbrainsmono/v24/tDbY2o-flEEny0FZhsfKu5WU4zr3E_BX0PnT8RD8yK1jPQ.ttf"
echo "  ✅ Tipografías listas"

# 4. Navegador
for b in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
         "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
         "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
         "$(command -v chromium 2>/dev/null)" "$(command -v google-chrome 2>/dev/null)"; do
  [ -n "$b" ] && [ -x "$b" ] && { NAV="$b"; break; }
done
[ -z "$NAV" ] && echo "  ⚠️  No encontré Chrome, Brave, Edge ni Chromium. Instalá uno: se usa sin ventana para dibujar las placas." \
             || echo "  ✅ Navegador: $(basename "$NAV")"

# 5. Apify
command -v apify >/dev/null 2>&1 && echo "  ✅ Apify CLI instalado" \
  || echo "  ⚠️  Falta el CLI de Apify (busca las fotos): npm install -g apify-cli && apify login"

echo ""
echo "Listo. Falta tu marca: copiá marca.ejemplo.json a mi-marca.json y editalo,"
echo "o abrí Claude Code y pedile \"configurá mi marca para los posts de LinkedIn\"."
echo ""
