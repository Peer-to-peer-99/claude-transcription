#!/usr/bin/env bash

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT"

echo "======================================"
echo " CLAUDE AUDIÊNCIA - LINUX"
echo "======================================"

# Verifica Python 3.12
if ! command -v python3.12 >/dev/null 2>&1; then

    echo "Python 3.12 não encontrado."

    if ! command -v apt-get >/dev/null 2>&1; then
        echo "Este instalador automático requer Ubuntu/Debian."
        exit 1
    fi

    sudo apt-get update

    sudo apt-get install -y \
        python3.12 \
        python3.12-venv

fi

python3.12 --version

# Executa bootstrap
python3.12 scripts/bootstrap.py

# Instala Claude Code se necessário
if ! command -v claude >/dev/null 2>&1; then

    echo "Instalando Claude Code..."

    curl -fsSL https://claude.ai/install.sh | bash

fi

echo ""
echo "======================================"
echo " INSTALAÇÃO CONCLUÍDA"
echo "======================================"

echo "Execute: claude"