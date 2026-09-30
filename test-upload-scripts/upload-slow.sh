#!/bin/sh

# Script de prueba: simula una subida lenta (30 s) para verificar que la GUI
# no se congela y que Cancelar mata el proceso. No forma parte de la app.

IMAGE_PATH=$1

if [ ! -f "$IMAGE_PATH" ]; then
    echo "La imagen temporal no existe: $IMAGE_PATH" >&2
    exit 1
fi

echo "Imagen recibida: $IMAGE_PATH"
sleep 30
echo "https://example.com/uploads/subida-lenta.png"
