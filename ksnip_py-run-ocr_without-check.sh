#!/bin/sh

# Ir siempre a la carpeta donde está este script (la raíz del proyecto)
cd "$(dirname -- "$0")" || exit 1

# Lanzar ksnip directamente con el Python del entorno virtual
exec ".venv/bin/python" -m ksnip_py "$@"
