#!/bin/sh

set -eu

IMAGE_PATH=$1

if [ ! -f "$IMAGE_PATH" ]; then
    echo "La imagen temporal no existe: $IMAGE_PATH" >&2
    exit 1
fi

echo "Imagen recibida: $IMAGE_PATH"
echo "https://example.com/uploads/captura-prueba.png"