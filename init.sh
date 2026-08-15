#!/usr/bin/env bash
set -eu

# Inicialización segura para validaciones locales. No imprime ni crea secretos.
PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$PROJECT_ROOT"

if ! command -v python >/dev/null 2>&1; then
    printf '%s\n' 'Error: se requiere Python en PATH.' >&2
    exit 1
fi

python -m pytest --collect-only -q >/dev/null
printf '%s\n' 'Inicialización validada: entorno Python y tests disponibles.'
