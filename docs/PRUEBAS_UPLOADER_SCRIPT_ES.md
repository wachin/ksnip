# Pruebas del uploader por script de ksnip_py

Esta guía permite probar el uploader sin enviar imágenes a Internet. Los
scripts locales comprueban por separado la entrega del PNG temporal, la salida
estándar, los errores, el filtro mediante expresiones regulares, las rutas
Unicode y el comportamiento de la interfaz durante una subida lenta.

Ejecute los comandos desde la raíz del proyecto:

```bash
cd /home/wachin/Dev/ksnip-dev/ksnip
mkdir -p test-upload-scripts
```

## 1. Crear un script de subida exitosa

Cree `test-upload-scripts/upload-success.sh`:

```bash
#!/bin/sh

set -eu

IMAGE_PATH=$1

if [ ! -f "$IMAGE_PATH" ]; then
    echo "La imagen temporal no existe: $IMAGE_PATH" >&2
    exit 1
fi

echo "Imagen recibida: $IMAGE_PATH"
echo "https://example.com/uploads/captura-prueba.png"
```

Concédale permiso de ejecución:

```bash
chmod +x test-upload-scripts/upload-success.sh
```

Compruébelo manualmente:

```bash
test-upload-scripts/upload-success.sh artwork-sources/TuxBaby/TuxBaby.png
```

La salida esperada es similar a:

```text
Imagen recibida: artwork-sources/TuxBaby/TuxBaby.png
https://example.com/uploads/captura-prueba.png
```

## 2. Configurar ksnip_py

Inicie el programa:

```bash
python3 -m ksnip_py
```

Después:

1. Abra `Opciones > Configuración`.
2. Entre en `Uploader > Script Uploader`.
3. En `Script`, seleccione:

   ```text
   /home/wachin/Dev/ksnip-dev/ksnip/test-upload-scripts/upload-success.sh
   ```

4. Active `Copiar salida del script al portapapeles`.
5. En el filtro escriba:

   ```regex
   https?://[^\s]+
   ```

6. Para la primera prueba, desactive `Detener cuando el script escriba en StdErr`.
7. Guarde la configuración.

## 3. Probar una subida correcta

1. Abra o capture una imagen.
2. Seleccione `Archivo > Subir`, o pulse el botón `Subir`.
3. Si aparece la confirmación, acéptela.

Resultado esperado:

- El script recibe la ruta de una imagen PNG temporal.
- ksnip_py informa que la subida terminó correctamente.
- El portapapeles contiene solamente:

  ```text
  https://example.com/uploads/captura-prueba.png
  ```

Puede pegarlo en un editor o, si dispone de `xclip`, comprobarlo con:

```bash
xclip -selection clipboard -o
```

## 4. Probar sin expresión regular

Regrese a la configuración y borre el filtro. Suba nuevamente la imagen.

El portapapeles debería contener toda la salida:

```text
Imagen recibida: /tmp/archivo-temporal.png
https://example.com/uploads/captura-prueba.png
```

Esto verifica que el filtro determina qué parte de `stdout` se copia.

## 5. Comprobar que la imagen temporal es válida

Cree `test-upload-scripts/upload-inspect.sh`:

```bash
#!/bin/sh

set -eu

IMAGE_PATH=$1

echo "Ruta: $IMAGE_PATH"
file "$IMAGE_PATH"

if [ ! -s "$IMAGE_PATH" ]; then
    echo "La imagen está vacía" >&2
    exit 1
fi

echo "https://example.com/image-ok.png"
```

Concédale permiso y selecciónelo en la configuración:

```bash
chmod +x test-upload-scripts/upload-inspect.sh
```

La operación debe reconocer el archivo temporal como una imagen PNG válida y
finalizar correctamente.

## 6. Probar un error devuelto por el script

Cree `test-upload-scripts/upload-error.sh`:

```bash
#!/bin/sh

echo "El servidor rechazó la imagen" >&2
exit 7
```

```bash
chmod +x test-upload-scripts/upload-error.sh
```

Selecciónelo e intente subir una imagen.

Resultado esperado:

- ksnip_py indica que la subida falló.
- No informa que terminó correctamente.
- No copia una URL al portapapeles.
- El error menciona `El servidor rechazó la imagen`.

## 7. Probar la opción de detener ante StdErr

Cree `test-upload-scripts/upload-warning.sh`:

```bash
#!/bin/sh

set -eu

IMAGE_PATH=$1

echo "Advertencia de prueba" >&2
echo "https://example.com/upload-with-warning.png"
exit 0
```

```bash
chmod +x test-upload-scripts/upload-warning.sh
```

Realice dos pruebas:

1. Con `Detener cuando el script escriba en StdErr` desactivado, la operación
   debería considerarse exitosa.
2. Con la opción activada, debería considerarse fallida aunque el proceso haya
   devuelto el código cero.

## 8. Probar un filtro que no coincide

Utilice el script exitoso y configure este filtro:

```regex
ftp://[^\s]+
```

La salida contiene una URL HTTPS, no FTP. La implementación actual devuelve
toda la salida original cuando no encuentra coincidencias. Registre si observa
ese comportamiento.

## 9. Probar una expresión regular inválida

Configure deliberadamente este filtro incompleto:

```regex
(
```

Intente subir una imagen y compruebe:

- si aparece una excepción en la terminal;
- si ksnip_py muestra un mensaje de error;
- si la aplicación continúa funcionando o se cierra.

Esta condición debe manejarse sin cerrar la aplicación.

## 10. Probar un script sin permiso de ejecución

Retire temporalmente el permiso:

```bash
chmod -x test-upload-scripts/upload-success.sh
```

Selecciónelo e intente subir. ksnip_py no debe cerrarse y debe informar que no
pudo iniciar el script o que faltan permisos.

Restaure el permiso al terminar:

```bash
chmod +x test-upload-scripts/upload-success.sh
```

## 11. Probar una ruta con espacios y caracteres Unicode

Cree una copia en una ruta con espacios y una tilde:

```bash
mkdir -p "test-upload-scripts/Subidor de imágenes"
cp test-upload-scripts/upload-success.sh \
  "test-upload-scripts/Subidor de imágenes/subir imagen.sh"
chmod +x "test-upload-scripts/Subidor de imágenes/subir imagen.sh"
```

Seleccione en ksnip_py:

```text
/home/wachin/Dev/ksnip-dev/ksnip/test-upload-scripts/Subidor de imágenes/subir imagen.sh
```

Debe funcionar sin escapar manualmente la ruta. ksnip_py entrega la ruta del
script y la imagen como argumentos separados, por lo que los espacios y los
caracteres Unicode deben conservarse correctamente.

## 12. Comprobar si la interfaz se congela

Cree `test-upload-scripts/upload-slow.sh`:

```bash
#!/bin/sh

set -eu

sleep 15
echo "https://example.com/slow-upload.png"
```

```bash
chmod +x test-upload-scripts/upload-slow.sh
```

Selecciónelo y suba una imagen. Durante los 15 segundos intente:

- mover la ventana;
- abrir un menú;
- cambiar de pestaña;
- cancelar o cerrar la operación.

En la implementación actual es probable que la interfaz quede congelada. El
uploader se ejecuta mediante una llamada síncrona y este es un defecto conocido
que debe corregirse con ejecución asíncrona.

## 13. Probar desde la línea de comandos

Con el script exitoso configurado, ejecute:

```bash
python -m ksnip_py --rectarea --upload
```

Seleccione una región. El resultado del uploader debería aparecer en la
terminal.

También puede combinar guardado y subida:

```bash
python -m ksnip_py \
  --rectarea \
  --save ~/Imágenes/captura-uploader.png \
  --upload
```

## 14. Resultados que deben registrarse

Las comprobaciones prioritarias son:

1. Script exitoso con filtro de URL.
2. Script que termina con el código 7.
3. Script que escribe en `stderr` pero devuelve el código 0.
4. Expresión regular inválida.
5. Script lento.
6. Ruta con espacios y caracteres Unicode.

Puede copiar y completar esta plantilla:

```text
Sistema y versión:
Python:
PyQt6:

1. Subida exitosa y filtro:
2. Código de salida 7:
3. StdErr con código 0, opción desactivada:
4. StdErr con código 0, opción activada:
5. Filtro sin coincidencia:
6. Expresión regular inválida:
7. Script sin permiso:
8. Ruta con espacios y Unicode:
9. ¿Se congeló la interfaz con el script lento?:
10. Resultado de la prueba mediante CLI:
11. Mensajes adicionales de la terminal:
```

Estos resultados permiten corregir el manejo de errores, el filtrado, los
permisos, Unicode, el bloqueo de la interfaz y la cancelación sin depender de
un servicio de alojamiento externo.
