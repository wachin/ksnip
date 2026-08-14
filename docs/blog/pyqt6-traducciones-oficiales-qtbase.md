# Cómo traducir los diálogos estándar de Qt6 en una aplicación PyQt6

Una aplicación PyQt6 puede tener todos sus menús traducidos al español y, aun
así, mostrar en inglés los botones de Abrir, Guardar o Cancelar. Esto no
significa necesariamente que el catálogo de la aplicación esté incompleto.
Qt separa los textos propios del programa de los textos pertenecientes a sus
componentes estándar.

En Debian, Ubuntu y derivados, las traducciones oficiales de Qt6 se distribuyen
en el paquete:

```bash
sudo apt install qt6-translations-l10n
```

Este paquete incluye catálogos como:

```text
qtbase_es.qm
qtbase_fr.qm
qtbase_de.qm
```

Instalarlo no basta si la aplicación nunca carga el catálogo. Veamos cómo
integrarlo correctamente desde el diseño inicial y cómo reparar un proyecto
que ya está construido.

## Dos clases diferentes de traducciones

Supongamos que nuestra aplicación distribuye:

```text
translations/mi_aplicacion_es.qm
```

Ese archivo debe contener textos como:

```text
Nueva captura
Preferencias
Exportar como SVG
Seleccionar marca de agua
```

Los textos de widgets estándar pertenecen a Qt. Entre ellos están muchos
botones, menús y etiquetas de:

- `QFileDialog`;
- `QMessageBox`;
- `QDialogButtonBox`;
- vista previa e impresión;
- menús de edición estándar;
- helpers de plataforma que consultan `QPlatformTheme`.

Los módulos Qt Core, GUI, Network, Print Support y Widgets usan el catálogo
`qtbase`. La [documentación oficial de localización de
Qt6](https://doc.qt.io/qt-6/localization.html) recomienda localizarlo mediante
`QLibraryInfo` e instalarlo con `QTranslator`.

Por tanto, una aplicación necesita normalmente este orden:

1. Crear `QApplication`.
2. Resolver el idioma configurado o el idioma del sistema.
3. Cargar `qtbase_<idioma>.qm`.
4. Cargar los catálogos propios.
5. Construir la ventana principal y sus diálogos.

## Nunca presupongas `/usr/share/qt6/translations`

En una instalación Debian con PyQt6 del sistema, la ruta puede ser:

```text
/usr/share/qt6/translations
```

Pero PyQt6 instalado mediante pip puede utilizar otro Qt dentro del entorno
virtual. En Windows o macOS la aplicación puede distribuir su propio runtime.
La ruta correcta debe obtenerse del Qt que está ejecutándose:

```python
from PyQt6.QtCore import QLibraryInfo

translations_path = QLibraryInfo.path(
    QLibraryInfo.LibraryPath.TranslationsPath
)
```

Desde Qt 6.8 también puede haber más de una ruta:

```python
paths = QLibraryInfo.paths(
    QLibraryInfo.LibraryPath.TranslationsPath
)
```

Para conservar compatibilidad con versiones anteriores puede intentarse
`paths()` y volver a `path()` si el binding no lo ofrece.

## Implementación portable

Este módulo carga primero `qtbase` y después los catálogos de la aplicación:

```python
from __future__ import annotations

import os
from pathlib import Path
import sys

from PyQt6.QtCore import QLibraryInfo, QLocale, QTranslator


TRANSLATORS: list[QTranslator] = []


def qt_translation_directories() -> list[Path]:
    translation_path = QLibraryInfo.LibraryPath.TranslationsPath

    try:
        configured = QLibraryInfo.paths(translation_path)
    except AttributeError:
        configured = [QLibraryInfo.path(translation_path)]

    candidates = [Path(path) for path in configured if path]

    # Fallback adicional sólo para distribuciones Linux.
    if sys.platform.startswith("linux"):
        data_roots = os.environ.get(
            "XDG_DATA_DIRS",
            "/usr/local/share:/usr/share",
        )
        for root in data_roots.split(os.pathsep):
            if root:
                candidates.extend((
                    Path(root) / "qt6" / "translations",
                    Path(root) / "qt" / "translations",
                ))

    unique: list[Path] = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    return unique


def install_catalog(
    app,
    locale: QLocale,
    catalog: str,
    directories: list[Path],
) -> bool:
    for directory in directories:
        translator = QTranslator(app)
        if translator.load(locale, catalog, "_", str(directory)):
            app.installTranslator(translator)
            TRANSLATORS.append(translator)
            return True
    return False


def load_translations(app, locale_name: str | None = None) -> str:
    for translator in TRANSLATORS:
        app.removeTranslator(translator)
        translator.deleteLater()
    TRANSLATORS.clear()

    locale = QLocale(locale_name) if locale_name else QLocale.system()

    # Textos estándar: Abrir, Guardar, Cancelar, etc.
    install_catalog(
        app,
        locale,
        "qtbase",
        qt_translation_directories(),
    )

    # Textos propios de la aplicación.
    application_directory = Path(__file__).resolve().parent / "translations"
    for catalog in ("mi_aplicacion",):
        install_catalog(
            app,
            locale,
            catalog,
            [application_directory],
        )

    return locale.name()
```

Es importante conservar referencias a los objetos `QTranslator`. Si se crean
como variables locales y Python los destruye, las traducciones pueden dejar de
estar instaladas.

## Carga durante el arranque

La traducción debe instalarse antes de construir los widgets:

```python
import sys

from PyQt6.QtWidgets import QApplication

from .i18n import load_translations
from .main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    configured_language = "es_EC"  # O leerlo de QSettings.
    load_translations(app, configured_language)

    window = MainWindow()
    window.show()
    return app.exec()
```

Si la ventana y los diálogos se crean antes de instalar el traductor, sus
textos iniciales pueden quedar en inglés. Cambiar el idioma mientras la
aplicación está abierta requiere además manejar eventos `LanguageChange` o
reconstruir los widgets correspondientes.

## Los títulos propios siguen necesitando `tr()`

`qtbase_es.qm` puede traducir el botón `Open` como `Abrir`, pero no conoce un
título inventado por nuestra aplicación como `Open tutorial image`.

Esto sigue siendo responsabilidad del catálogo propio:

```python
path, selected_filter = QFileDialog.getOpenFileName(
    self,
    self.tr("Open image"),
    initial_directory,
    self.tr("Images (*.png *.jpg *.jpeg *.webp)"),
)
```

Después hay que ejecutar el flujo de Qt Linguist (`pylupdate6`, traducción del
`.ts` y `lrelease`) para actualizar el `.qm` de la aplicación.

## Verificación automática

Podemos comprobar el catálogo sin abrir visualmente el diálogo:

```python
from PyQt6.QtCore import QCoreApplication


def test_qtbase_spanish_catalog(app):
    load_translations(app, "es_EC")

    assert QCoreApplication.translate(
        "QFileDialog",
        "Open",
    ) == "Abrir"

    assert QCoreApplication.translate(
        "QPlatformTheme",
        "Open",
    ) == "Abrir"
```

También puede comprobarse el texto real de los botones del diálogo Qt Widgets:

```python
from PyQt6.QtWidgets import QDialogButtonBox, QFileDialog

dialog = QFileDialog()
dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)

button_box = dialog.findChild(QDialogButtonBox)
print([button.text() for button in button_box.buttons()])
# ['&Guardar', 'Cancelar']
```

Aquí `DontUseNativeDialog` sólo se usa para que la prueba automatizada pueda
inspeccionar los botones Qt Widgets. No es una configuración global de la
aplicación.

## Debian y Ubuntu

Para una instalación de desarrollo basada en paquetes del sistema:

```bash
sudo apt update
sudo apt install python3-pyqt6 qt6-translations-l10n
```

En `debian/control`, la aplicación puede declararlo como recomendación:

```text
Package: mi-aplicacion
Architecture: all
Depends:
 ${misc:Depends},
 ${python3:Depends}
Recommends:
 qt6-translations-l10n
```

`Recommends` es apropiado cuando la aplicación puede funcionar sin esos
catálogos, aunque los controles Qt aparecerían en inglés. Los catálogos propios
de la aplicación deben seguir instalándose con el paquete principal; no deben
confundirse con `qt6-translations-l10n`.

## PyQt6 instalado con pip

En un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install PyQt6
```

`QLibraryInfo.TranslationsPath` seguirá al runtime Qt utilizado por ese PyQt6.
Si el wheel incluye los catálogos, la aplicación los encontrará allí. Si no
los incluye, el fallback Linux puede localizar los proporcionados por la
distribución mediante `XDG_DATA_DIRS`, siempre que sean compatibles con el Qt
en ejecución.

No conviene copiar silenciosamente catálogos desde una ruta Debian hacia el
entorno virtual ni codificar `/usr/share/qt6/translations` como única opción.

## Windows y macOS

`qt6-translations-l10n` es el nombre de un paquete Debian; no debe solicitarse
en Windows ni macOS.

En esos sistemas hay que incluir durante el empaquetado los archivos requeridos:

```text
qtbase_es.qm
qtbase_fr.qm
qtbase_de.qm
```

en el directorio de traducciones del Qt distribuido con la aplicación. La
lógica Python no cambia porque pregunta la ubicación a `QLibraryInfo`.

Si se usa PyInstaller, Nuitka u otra herramienta de congelación, la receta de
empaquetado debe copiar esos `.qm` junto al runtime Qt y debe comprobarse el
resultado en una máquina limpia.

## Prompt preventivo para crear o portar una aplicación con un agente de IA

```text
Voy a crear una aplicación con Python/PyQt6 [o portar una aplicación C++/Qt a
PyQt6]. Diseña desde el principio un sistema de internacionalización completo
que traduzca tanto los textos propios como los componentes estándar de Qt6.

Requisitos obligatorios:

1. Instala los QTranslator antes de construir MainWindow o cualquier diálogo.
2. Carga primero el catálogo oficial qtbase para el QLocale seleccionado y
   después los catálogos propios de la aplicación.
3. Obtén la ruta principal exclusivamente con
   QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath), o paths() si
   está disponible. No presupongas /usr/share/qt6/translations.
4. Conserva referencias vivas a todos los QTranslator instalados y elimina
   correctamente los anteriores si se cambia el idioma.
5. En Linux añade, sólo como fallback, búsquedas basadas en XDG_DATA_DIRS para
   qt6/translations y qt/translations.
6. En Debian/Ubuntu documenta sudo apt install qt6-translations-l10n y evalúa
   declararlo como Recommends en debian/control.
7. Explica que ese paquete traduce widgets estándar de Qt y no sustituye los
   catálogos propios de la aplicación.
8. Para pip, Windows y macOS sigue siempre el Qt informado por QLibraryInfo y
   documenta que el paquete final debe incluir qtbase_<locale>.qm.
9. Envuelve todos los títulos, filtros y textos propios visibles en self.tr()
   o QCoreApplication.translate(), y actualiza los catálogos con Qt Linguist.
10. Añade pruebas que verifiquen QFileDialog/Open y QPlatformTheme/Open en
    español, además de los textos propios de la aplicación.
11. Si el catálogo opcional de Qt no está instalado en el entorno de pruebas,
    la prueba de integración puede omitirse explícitamente, pero la lógica de
    búsqueda debe seguir cubierta por pruebas unitarias.

Antes de implementar, inspecciona la estructura del proyecto, el arranque, los
catálogos existentes, el empaquetado Debian y la estrategia para pip. Entrega
la implementación, pruebas, documentación y verificación del wheel o paquete.
```

## Prompt para corregir una aplicación PyQt6 ya terminada

```text
Audita esta aplicación PyQt6: sus menús propios están traducidos, pero los
diálogos estándar de Qt6, incluidos Abrir, Guardar y Cancelar, aparecen en
inglés.

Revisa i18n.py, el orden de creación de QApplication/MainWindow, todos los
QTranslator, QLocale, los catálogos .ts/.qm y el empaquetado. Implementa la
carga de qtbase_<locale>.qm usando como fuente principal
QLibraryInfo.LibraryPath.TranslationsPath. No uses una ruta fija Debian.

Añade un fallback seguro basado en XDG_DATA_DIRS únicamente en Linux. Mantén
compatibilidad con PyQt6 instalado mediante pip y con despliegues Windows y
macOS. Conserva referencias a QTranslator, instala qtbase antes de los
catálogos propios y migra a tr() cualquier título o filtro visible que todavía
sea un literal.

Actualiza Qt Linguist, README y debian/control. Documenta
qt6-translations-l10n como traducción de componentes Qt estándar y no como
sustituto de las traducciones de la aplicación. Añade pruebas para
QFileDialog/Open, QPlatformTheme/Open y al menos un texto propio. Construye el
wheel y ejecuta la suite completa antes de finalizar.
```

## Conclusión

Traducir una aplicación Qt no consiste únicamente en compilar su archivo `.ts`.
La aplicación y el framework poseen catálogos diferentes. Cuando cargamos
`qtbase` desde la ubicación declarada por el propio runtime y después
instalamos nuestros traductores, el mismo código funciona con los paquetes de
Debian, con un entorno virtual, y con distribuciones correctamente preparadas
para Windows o macOS.
