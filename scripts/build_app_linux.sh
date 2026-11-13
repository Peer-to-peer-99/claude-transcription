#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT"

echo "======================================"
echo " CLAUDE AUDIÊNCIA - BUILD LINUX"
echo "======================================"

PYTHON_BUILD="$PROJECT_ROOT/dist/audiencia"
TAURI_RESOURCES="$PROJECT_ROOT/desktop/src-tauri/resources"

if [ ! -f "$PYTHON_BUILD/audiencia" ]; then
    echo "Executável Python não encontrado."
    echo "Gere primeiro o build com PyInstaller."
    exit 1
fi

echo "Preparando mecanismo de transcrição..."

rm -rf "$TAURI_RESOURCES/audiencia"

mkdir -p "$TAURI_RESOURCES"

cp -a "$PYTHON_BUILD" "$TAURI_RESOURCES/audiencia"

echo "Preparando aplicativo Tauri..."

cd "$PROJECT_ROOT/desktop"

npm run tauri build -- --bundles deb,appimage

echo ""
echo "======================================"
echo " BUILD LINUX CONCLUÍDO"
echo "======================================"

echo "Instaladores disponíveis em:"
echo "desktop/src-tauri/target/release/bundle/"