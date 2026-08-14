# Cómo conservar correctamente marcadores con tildes en los diálogos de archivos de PyQt6

Cuando desarrollamos una aplicación con PyQt6, normalmente abrimos archivos
con `QFileDialog.getOpenFileName()` y los guardamos con
`QFileDialog.getSaveFileName()`. Es una API cómoda, pero el diálogo que aparece
no siempre pertenece al mismo componente: puede ser el selector nativo del
escritorio o el diálogo construido con Qt Widgets.

Esta diferencia se vuelve importante cuando el usuario arrastra carpetas a la
barra lateral para crear lugares favoritos. Un marcador como:

```text
/home/usuario/Imágenes
/home/usuario/Música
/home/usuario/Documentación
```

puede funcionar mientras la aplicación permanece abierta y fallar después de
cerrarla y volverla a iniciar. En este artículo veremos cómo investigar el
problema sin culpar inmediatamente a UTF-8, sin convertir manualmente cadenas
a bytes y sin desactivar los diálogos nativos de forma indiscriminada.

## No empieces forzando `DontUseNativeDialog`

Esta opción obliga a Qt a construir su propio diálogo:

```python
QFileDialog.Option.DontUseNativeDialog
```

Puede ser útil para una prueba comparativa, pero no debe ser la primera ni la
última solución sin diagnóstico. Al forzarla podemos perder integración con
GTK, KDE, Windows o macOS, accesos especiales del sistema, portales y el estilo
del escritorio.

Según la documentación oficial de
[`QFileDialog`](https://doc.qt.io/qt-6/qfiledialog.html), Qt usa el diálogo
nativo cuando la plataforma ofrece uno. Cuando se utiliza un helper nativo,
algunas APIs propias de widgets, como `layout()`, pueden devolver `None`.

Una prueba útil es abrir temporalmente ambos diálogos y comprobar sus widgets
internos:

```python
from PyQt6.QtWidgets import QApplication, QFileDialog, QListView, QTreeView

app = QApplication([])

for force_qt_widgets in (False, True):
    dialog = QFileDialog()
    dialog.setOption(
        QFileDialog.Option.DontUseNativeDialog,
        force_qt_widgets,
    )
    dialog.show()
    app.processEvents()

    views = len(dialog.findChildren(QListView)) + len(
        dialog.findChildren(QTreeView)
    )
    print(
        "forzado=" if force_qt_widgets else "predeterminado=",
        "layout:", bool(dialog.layout()),
        "vistas internas:", views,
    )
    dialog.close()
```

Conviene ejecutar esta prueba con un directorio de configuración temporal para
no modificar los marcadores reales:

```bash
XDG_CONFIG_HOME="$(mktemp -d)" python3 prueba_dialogo.py
```

En el caso que dio origen a este artículo, Debian 13 con AV Linux MXe, Qt 6.8
y el tema de plataforma `qt6ct` mostró el diálogo Qt Widgets tanto en el caso
predeterminado como al activar `DontUseNativeDialog`. Por tanto, forzar esa
opción no solucionaba nada: el diálogo ya era el de Qt.

## Averigua quién guarda los marcadores

Los diálogos nativos administran sus lugares favoritos mediante mecanismos de
la plataforma. Por ejemplo, GTK puede utilizar:

```text
~/.config/gtk-3.0/bookmarks
```

Una entrada Unicode correcta puede verse así:

```text
file:///home/usuario/Im%C3%A1genes
file:///home/usuario/M%C3%BAsica
```

El diálogo Qt Widgets usa otra persistencia. El código fuente de Qt6 muestra
que `QFileDialogPrivate::saveSettings()` crea:

```cpp
QSettings settings(QSettings::UserScope, u"QtProject"_s);
settings.beginGroup("FileDialog");
```

y guarda allí `shortcuts`, `history` y `lastVisited`. En Linux, normalmente
terminan en:

```text
~/.config/QtProject.conf
```

Qt guarda la barra lateral mediante `QUrl::toStringList()` y la reconstruye
con `QUrl::fromStringList()`. Puede consultarse este comportamiento en el
[código fuente de QFileDialog de Qt6](https://codebrowser.dev/qt6/qtbase/src/widgets/dialogs/qfiledialog.cpp.html).

Esto explica por qué no debemos modificar a ciegas el archivo de marcadores
GTK si el diálogo visible pertenece realmente a Qt Widgets.

## El manejo correcto de una ruta Unicode

PyQt6 entrega las rutas locales como `str`. No hay que convertirlas
manualmente a UTF-8 para pasarlas a Qt:

```python
from PyQt6.QtCore import QUrl

path = "/home/usuario/Imágenes"
url = QUrl.fromLocalFile(path)

print(url.toString())
# file:///home/usuario/Imágenes

print(url.toString(QUrl.ComponentFormattingOption.FullyEncoded))
# file:///home/usuario/Im%C3%A1genes

print(url.toLocalFile())
# /home/usuario/Imágenes
```

El ciclo correcto es:

```text
str local → QUrl.fromLocalFile() → URL persistida → QUrl.toLocalFile() → str local
```

No se necesitan operaciones como estas:

```python
path.encode("utf-8")
path.decode("utf-8")
urllib.parse.quote(path)
urllib.parse.unquote(path)
```

Mezclar esas conversiones con `QUrl` puede provocar doble codificación, por
ejemplo `%25C3%25A1` en vez de `%C3%A1`.

## Una solución robusta para el diálogo Qt Widgets

La solución utilizada consiste en dejar que Qt seleccione el backend y
normalizar únicamente su propia persistencia `QtProject/FileDialog` antes y
después de cada diálogo. Las URLs se guardan con `FullyEncoded`; el archivo INI
queda limitado a ASCII, pero `toLocalFile()` recupera la ruta Unicode original.

Podemos centralizar todos los diálogos en un módulo:

```python
from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import QSettings, QUrl
from PyQt6.QtWidgets import QFileDialog


URL_LIST_KEYS = ("shortcuts", "history")
URL_KEYS = ("lastVisited",)


def qt_file_dialog_settings() -> QSettings:
    # Es el mismo almacén que usa internamente QFileDialog Qt Widgets.
    return QSettings(QSettings.Scope.UserScope, "QtProject")


def fully_encoded_url(value: object) -> str:
    text = str(value)
    url = QUrl.fromLocalFile(text) if text.startswith("/") else QUrl(text)

    if not url.isValid() or url.isEmpty():
        return text
    if not url.scheme() and not text.startswith("/"):
        return text

    if url.isLocalFile():
        local_path = url.toLocalFile()
        if local_path:
            url = QUrl.fromLocalFile(local_path)

    return url.toString(QUrl.ComponentFormattingOption.FullyEncoded)


def normalize_file_dialog_urls(settings: QSettings | None = None) -> None:
    store = settings or qt_file_dialog_settings()
    store.beginGroup("FileDialog")
    try:
        for key in URL_LIST_KEYS:
            if not store.contains(key):
                continue
            value = store.value(key, [])
            values = value if isinstance(value, list) else [value]
            store.setValue(key, [fully_encoded_url(item) for item in values])

        for key in URL_KEYS:
            if store.contains(key):
                store.setValue(key, fully_encoded_url(store.value(key)))
    finally:
        store.endGroup()

    store.sync()


def run_dialog(method: Callable[..., Any], *args, **kwargs):
    normalize_file_dialog_urls()
    try:
        return method(*args, **kwargs)
    finally:
        # El helper estático ya destruyó su QFileDialog y Qt ya guardó el estado.
        normalize_file_dialog_urls()


def get_open_file_name(*args, **kwargs) -> tuple[str, str]:
    return run_dialog(QFileDialog.getOpenFileName, *args, **kwargs)


def get_open_file_names(*args, **kwargs) -> tuple[list[str], str]:
    return run_dialog(QFileDialog.getOpenFileNames, *args, **kwargs)


def get_save_file_name(*args, **kwargs) -> tuple[str, str]:
    return run_dialog(QFileDialog.getSaveFileName, *args, **kwargs)
```

El resto de la aplicación ya no llama directamente a `QFileDialog`:

```python
from .file_dialogs import get_open_file_name

path, selected_filter = get_open_file_name(
    parent,
    parent.tr("Open image"),
    initial_directory,
    parent.tr("Images (*.png *.jpg *.jpeg *.webp)"),
)
```

Esta técnica no cambia los marcadores nativos de GTK, KDE, Windows o macOS.
Cuando el backend es Qt Widgets, estabiliza la representación que Qt guarda.

## Prueba de regresión con un reinicio simulado

Una prueba útil debe cerrar y volver a abrir el almacén, no comprobar solamente
el valor que sigue en memoria:

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from PyQt6.QtCore import QSettings, QUrl


def test_unicode_bookmarks_survive_restart():
    with TemporaryDirectory() as directory:
        filename = str(Path(directory) / "QtProject.ini")
        settings = QSettings(filename, QSettings.Format.IniFormat)
        settings.beginGroup("FileDialog")
        settings.setValue("shortcuts", [
            "file:///home/usuario/Imágenes",
            "file:///home/usuario/Música",
        ])
        settings.endGroup()

        normalize_file_dialog_urls(settings)
        settings.sync()
        del settings

        restored = QSettings(filename, QSettings.Format.IniFormat)
        restored.beginGroup("FileDialog")
        urls = restored.value("shortcuts")
        restored.endGroup()

        assert urls[0] == "file:///home/usuario/Im%C3%A1genes"
        assert QUrl(urls[0]).toLocalFile() == "/home/usuario/Imágenes"
        assert QUrl(urls[1]).toLocalFile() == "/home/usuario/Música"
```

La prueba manual final debe reproducir la experiencia del usuario:

1. Abrir la aplicación.
2. Abrir el diálogo de archivos.
3. Arrastrar `Imágenes` o `Música` a la barra lateral.
4. Cerrar completamente la aplicación.
5. Iniciarla otra vez.
6. Abrir el diálogo y entrar mediante el marcador.

## Prompt preventivo para un agente de IA

Este prompt puede entregarse antes de crear una aplicación PyQt6 o antes de
iniciar un port desde C++/Qt:

```text
Estoy creando una aplicación de escritorio con Python y PyQt6 [o portando una
aplicación C++/Qt a PyQt6]. Diseña desde el inicio una capa centralizada para
todos los diálogos Abrir, Abrir varios, Guardar y Guardar como.

Requisitos obligatorios:

1. No fuerces globalmente QFileDialog.Option.DontUseNativeDialog. Permite que
   Qt use el diálogo nativo cuando la plataforma lo proporcione.
2. Distingue explícitamente entre diálogo nativo y QFileDialog Qt Widgets.
3. Las rutas deben permanecer como str/QString. Para convertir rutas locales
   a URLs usa QUrl.fromLocalFile(), y para recuperarlas usa QUrl.toLocalFile().
4. No uses encode(), decode(), urllib.parse.quote() ni unquote() para rutas.
5. Garantiza que los marcadores de la barra lateral con caracteres Unicode,
   por ejemplo Imágenes, Música o Documentación, sobrevivan al cierre completo
   y reinicio de la aplicación.
6. Si el backend Qt Widgets persiste sidebarUrls() mediante
   QtProject/FileDialog, normaliza shortcuts, history y lastVisited usando
   QUrl.ComponentFormattingOption.FullyEncoded antes y después del diálogo.
7. No alteres los almacenes nativos de marcadores de GTK, KDE, Windows o macOS.
8. Centraliza getOpenFileName(), getOpenFileNames() y getSaveFileName() en un
   módulo reutilizable; no dejes llamadas directas dispersas por el proyecto.
9. Añade pruebas automatizadas con QSettings temporal que simulen un reinicio
   real y verifiquen el round-trip exacto de rutas Unicode.
10. Documenta el backend probado, las variables de entorno relevantes,
    QUrl, percent encoding y cualquier diferencia entre Linux, Windows y macOS.

Antes de implementar, inspecciona todo el proyecto y explica con evidencia qué
backend se usa. No presentes DontUseNativeDialog como solución sin comparar
ambos comportamientos.
```

## Prompt para corregir una aplicación ya creada

```text
Audita esta aplicación PyQt6 porque los marcadores de la barra lateral de sus
diálogos de archivos funcionan durante la ejecución, pero después de reiniciar
fallan cuando la ruta contiene Unicode, por ejemplo Imágenes o Música.

Localiza todas las llamadas a QFileDialog y determina si el fallo ocurre con
el diálogo nativo, con Qt Widgets usando DontUseNativeDialog, o con ambos.
Inspecciona sidebarUrls(), QUrl, QSettings(UserScope, "QtProject"), el grupo
FileDialog, los marcadores del escritorio, locale y variables QT/XDG.

No fuerces DontUseNativeDialog como arreglo general. No hagas conversiones
manuales encode/decode ni quote/unquote. Usa QUrl.fromLocalFile(),
QUrl.toLocalFile() y FullyEncoded cuando la evidencia indique que debe
estabilizarse la persistencia de Qt Widgets.

Implementa una capa común para Abrir/Guardar, migra todas las llamadas del
proyecto, conserva la integración nativa y añade pruebas de proceso/reinicio
con Imágenes, Música y Documentación. Documenta la causa encontrada y ejecuta
la suite completa antes de terminar.
```

## Conclusión

Una ruta con tilde no es un conjunto de bytes que la aplicación deba reparar.
Es una cadena Unicode que Qt sabe manejar. El trabajo correcto consiste en
identificar qué diálogo y qué almacén persisten el marcador, mantener la
conversión dentro de `QUrl` y probar el límite que realmente fallaba: el cierre
y posterior reinicio del proceso.
