#!/usr/bin/env bash

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "$PROJECT_ROOT/scripts/install_linux.sh"