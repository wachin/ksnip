# Uso de PaddleOCR con ksnip_py en Debian y derivados

## Regla recomendada

En Debian 13, MX Linux 25, AV Linux MXe, Ubuntu, Linux Mint y sistemas
derivados, la instalación soportada de PaddleOCR para ksnip_py debe hacerse en
un entorno virtual de Python (`venv`).

Los repositorios configurados de Debian 13 no proporcionan actualmente los
paquetes `python3-paddleocr` y `python3-paddlepaddle`. PaddleOCR y PaddlePaddle
se instalan mediante `pip`, pero no deben instalarse con `sudo pip` ni dentro
del Python administrado por el sistema. El entorno virtual evita reemplazar o
romper paquetes que utiliza Debian.

El OCR es opcional. ksnip_py puede seguir ejecutándose con los paquetes del
sistema cuando no se necesite PaddleOCR.

## Instalación inicial, una sola vez

Instale primero las herramientas de entornos virtuales:

```bash
sudo apt update
sudo apt install python3-venv python3-pip
```

Desde la raíz del proyecto:

```bash
cd /home/wachin/Dev/ksnip-dev/ksnip

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
python -m pip install -r requirements-ocr.txt
```

El archivo `requirements-ocr.txt` fija también la versión compatible de
`protobuf`. No conviene omitirlo e instalar solamente los dos paquetes OCR:
una versión más nueva de Protobuf puede rechazar los descriptores generados de
PaddlePaddle con el mensaje `Couldn't build proto file into descriptor pool`.
Después de ese primer fallo, Python puede mostrar además un error engañoso de
`partially initialized module 'paddle'`; hay que cerrar ksnip_py, corregir las
versiones y volver a iniciarlo.

La instalación de PaddleOCR y PaddlePaddle solamente se realiza una vez, salvo
que se borre o se vuelva a crear `.venv`.

Puede comprobarla así:

```bash
python -c "from paddleocr import PaddleOCR; import paddle.base.proto.distributed_strategy_pb2; print('PaddleOCR disponible')"
```

## Opción 1: activar manualmente el entorno

Cada vez que abra una terminal nueva para utilizar PaddleOCR:

```bash
cd /home/wachin/Dev/ksnip-dev/ksnip
source .venv/bin/activate
python -m ksnip_py
```

También puede utilizar el ejecutable instalado dentro del entorno:

```bash
ksnip-pyqt6
```

La activación modifica temporalmente `PATH` para que `python`, `pip` y
`ksnip-pyqt6` sean los pertenecientes a `.venv`. Para salir del entorno:

```bash
deactivate
```

## Opción 2: utilizar el lanzador incluido

Después de realizar la instalación inicial, no es necesario activar `.venv`
manualmente. Ejecute:

```bash
cd /home/wachin/Dev/ksnip-dev/ksnip
./scripts/run-ksnip-with-paddleocr.sh
```

El lanzador usa directamente `.venv/bin/python`, comprueba tanto la importación
de PaddleOCR como sus descriptores Protobuf y abre ksnip_py. Si falta algo o las
versiones son incompatibles, termina sin tocar el Python del sistema y muestra
las instrucciones de instalación.

El script también transmite argumentos de línea de comandos:

```bash
./scripts/run-ksnip-with-paddleocr.sh --fullscreen
./scripts/run-ksnip-with-paddleocr.sh --rectarea
./scripts/run-ksnip-with-paddleocr.sh imagen.png
```

Si el entorno virtual se encuentra en otro lugar, puede indicarlo sin editar el
script:

```bash
KSNIP_PADDLEOCR_VENV=/ruta/al/entorno \
  ./scripts/run-ksnip-with-paddleocr.sh
```

La ruta indicada debe contener `bin/python` y tener instalados ksnip_py,
PaddlePaddle y PaddleOCR.

## Lo que el lanzador no hace

El lanzador no evita la instalación inicial y no descarga paquetes
automáticamente. Tampoco utiliza `sudo`, `--break-system-packages` ni modifica
el Python de Debian. Su función es sustituir la activación manual cotidiana por
una ejecución directa y comprobable del entorno correcto.

No se recomienda utilizar:

```bash
sudo pip install paddleocr
pip install --break-system-packages paddleocr
```

## Backend OCR mediante script

La opción `Settings > OCR > Script` es distinta de este lanzador. Ese backend
permite que ksnip_py entregue una imagen temporal a un programa OCR externo y
lea el texto que este escriba en la salida estándar. Puede ser útil para aislar
el motor OCR en otro entorno, pero requiere preparar ese programa por separado.

`run-ksnip-with-paddleocr.sh`, en cambio, inicia toda la aplicación dentro del
entorno donde PaddleOCR está instalado y permite seleccionar directamente el
backend PaddleOCR en los ajustes.
