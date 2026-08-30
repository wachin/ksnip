#!/bin/sh

set -eu

# Como el script ahora está en la raíz, el directorio del proyecto es el mismo directorio donde está este script
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VENV_DIR=${KSNIP_PADDLEOCR_VENV:-"$PROJECT_DIR/.venv"}
VENV_PYTHON="$VENV_DIR/bin/python"

show_install_instructions()
{
    printf '%s\n' \
        "PaddleOCR is not ready in: $VENV_DIR" \
        "" \
        "Create and prepare the virtual environment once with:" \
        "" \
        "  cd \"$PROJECT_DIR\"" \
        "  python3 -m venv .venv" \
        "  . .venv/bin/activate" \
        "  python -m pip install --upgrade pip setuptools wheel" \
        "  python -m pip install -e ." \
        "  python -m pip install -r requirements-ocr.txt" \
        "" \
        "Then run this launcher again."
}

if [ ! -x "$VENV_PYTHON" ]; then
    show_install_instructions >&2
    exit 2
fi

if ! "$VENV_PYTHON" -c 'from paddleocr import PaddleOCR; import paddle.base.proto.distributed_strategy_pb2' >/dev/null 2>&1; then
    show_install_instructions >&2
    exit 3
fi

cd "$PROJECT_DIR"
exec "$VENV_PYTHON" -m ksnip_py "$@"
