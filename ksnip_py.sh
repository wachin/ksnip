#!/bin/bash
# Lanzador de ksnip_py
# Da doble clic para ejecutar
# Abre una terminal, ejecuta el programa y la mantiene abierta si hay errores

cd /home/wachin/Dev/ksnip-dev/ksnip || exit 1

python3 -m ksnip_py

EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ El programa terminó con errores (código: $EXIT_CODE)."
    echo "Presiona Enter para cerrar..."
    read
fi
