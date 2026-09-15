#!/usr/bin/env bash
# Compila Tailwind con el binario standalone (sin Node/npm). El CSS
# resultante (static/css/app.css) SÍ se versiona — es lo que se
# sirve en producción, no se recompila en las PCs de los usuarios.
#
# Uso:
#   scripts/build_css.sh          # build normal (legible, para revisar diffs)
#   scripts/build_css.sh --watch  # recompila solo mientras se edita una plantilla
#   scripts/build_css.sh --minify # build final antes de empaquetar con PyInstaller
set -euo pipefail
cd "$(dirname "$0")/.."

BIN=".tools/tailwindcss"
if [ ! -x "$BIN" ]; then
  echo "Descargando el binario standalone de Tailwind (una sola vez, ~40MB)..."
  mkdir -p .tools
  URL="https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64"
  case "$(uname -s)" in
    Darwin) URL="https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-arm64" ;;
    MINGW*|MSYS*|CYGWIN*) URL="https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-windows-x64.exe"; BIN=".tools/tailwindcss.exe" ;;
  esac
  curl -sL -o "$BIN" "$URL"
  chmod +x "$BIN"
fi

"$BIN" -i static/css/input.css -o static/css/app.css "$@"
