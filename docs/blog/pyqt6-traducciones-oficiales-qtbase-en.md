# How to Translate Standard Qt6 Dialogs in a PyQt6 Application

A PyQt6 application may have all its menus translated into Spanish while its
Open, Save, and Cancel buttons remain in English. This does not necessarily
mean that the application's translation catalog is incomplete. Qt separates
application-specific text from the text belonging to its standard components.

On Debian, Ubuntu, and derivatives, the official Qt6 translations are provided
by this package:

```bash
sudo apt install qt6-translations-l10n
```

It includes catalogs such as:

```text
qtbase_es.qm
qtbase_fr.qm
qtbase_de.qm
```

Installing the package is not sufficient if the application never loads the
catalog. This article explains how to integrate it at the beginning of a
project and how to repair an application that is already implemented.

## Two different classes of translations

Suppose the application distributes:

```text
translations/my_application_es.qm
```

That file should contain application-specific strings such as:

```text
New capture
Settings
Export as SVG
Select watermark image
```

Standard widget text belongs to Qt. This includes many buttons, labels, and
menus used by:

- `QFileDialog`;
- `QMessageBox`;
- `QDialogButtonBox`;
- print dialogs and print preview;
- standard editing menus;
- platform helpers that consult `QPlatformTheme`.

Qt Core, GUI, Network, Print Support, and Widgets use the `qtbase` catalog. The
[official Qt6 localization documentation](https://doc.qt.io/qt-6/localization.html)
recommends locating it with `QLibraryInfo` and installing it through
`QTranslator`.

The normal startup order is therefore:

1. Create `QApplication`.
2. Resolve the configured language or system locale.
3. Load `qtbase_<locale>.qm`.
4. Load the application's own catalogs.
5. Construct the main window and its dialogs.

## Never assume `/usr/share/qt6/translations`

With Debian's system PyQt6, the path may be:

```text
/usr/share/qt6/translations
```

PyQt6 installed from pip may use a different Qt runtime inside a virtual
environment. Windows and macOS applications may bundle their own Qt runtime.
The correct path must come from the Qt instance that is actually running:

```python
from PyQt6.QtCore import QLibraryInfo

translations_path = QLibraryInfo.path(
    QLibraryInfo.LibraryPath.TranslationsPath
)
```

Qt 6.8 and later may provide more than one path:

```python
paths = QLibraryInfo.paths(
    QLibraryInfo.LibraryPath.TranslationsPath
)
```

For compatibility with older versions, try `paths()` and fall back to `path()`
when that binding is unavailable.

## A portable implementation

The following module loads `qtbase` first and then the application's catalogs:

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

    # An additional fallback for Linux distributions only.
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

    # Standard text: Open, Save, Cancel, and so on.
    install_catalog(
        app,
        locale,
        "qtbase",
        qt_translation_directories(),
    )

    # Application-specific text.
    application_directory = Path(__file__).resolve().parent / "translations"
    for catalog in ("my_application",):
        install_catalog(
            app,
            locale,
            catalog,
            [application_directory],
        )

    return locale.name()
```

References to installed `QTranslator` objects must remain alive. If they are
created only as local variables and Python destroys them, their translations
may stop being available.

## Load translations during startup

Install the translators before constructing widgets:

```python
import sys

from PyQt6.QtWidgets import QApplication

from .i18n import load_translations
from .main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    configured_language = "es_EC"  # Or read it from QSettings.
    load_translations(app, configured_language)

    window = MainWindow()
    window.show()
    return app.exec()
```

If the main window and dialogs are created before installing the translator,
their initial text may remain in English. Changing languages while the
application is running also requires handling `LanguageChange` events or
rebuilding the affected widgets.

## Application titles still require `tr()`

`qtbase_es.qm` can translate the standard `Open` button into `Abrir`, but it
does not know about an application-specific title such as `Open tutorial
image`.

That remains the application's responsibility:

```python
path, selected_filter = QFileDialog.getOpenFileName(
    self,
    self.tr("Open image"),
    initial_directory,
    self.tr("Images (*.png *.jpg *.jpeg *.webp)"),
)
```

The Qt Linguist workflow (`pylupdate6`, translating the `.ts`, and `lrelease`)
must then be run to update the application's `.qm` catalog.

## Automated verification

The catalog can be tested without visually opening a dialog:

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

You can also inspect the real buttons in the Qt Widgets dialog:

```python
from PyQt6.QtWidgets import QDialogButtonBox, QFileDialog

dialog = QFileDialog()
dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)

button_box = dialog.findChild(QDialogButtonBox)
print([button.text() for button in button_box.buttons()])
# ['&Guardar', 'Cancelar']
```

Here, `DontUseNativeDialog` is used only so an automated test can inspect Qt
Widgets buttons. It is not a global application setting.

## Debian and Ubuntu

For development with system packages:

```bash
sudo apt update
sudo apt install python3-pyqt6 qt6-translations-l10n
```

The application can declare it as a recommendation in `debian/control`:

```text
Package: my-application
Architecture: all
Depends:
 ${misc:Depends},
 ${python3:Depends}
Recommends:
 qt6-translations-l10n
```

`Recommends` is appropriate when the application still works without the
catalogs but standard Qt controls would appear in English. Application-specific
catalogs should remain in the main application package and must not be confused
with `qt6-translations-l10n`.

## PyQt6 installed from pip

Inside a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install PyQt6
```

`QLibraryInfo.TranslationsPath` follows the Qt runtime used by that PyQt6. If
the wheel contains translation catalogs, the application will find them there.
If it does not, the Linux fallback may locate distribution-provided catalogs
through `XDG_DATA_DIRS`, provided they are compatible with the active Qt.

Do not silently copy catalogs from a Debian path into the virtual environment,
and do not hardcode `/usr/share/qt6/translations` as the only location.

## Windows and macOS

`qt6-translations-l10n` is a Debian package name and should not be requested on
Windows or macOS.

On those systems, include the required files during packaging:

```text
qtbase_es.qm
qtbase_fr.qm
qtbase_de.qm
```

They belong in the translation directory of the Qt runtime bundled with the
application. The Python logic does not change because it asks `QLibraryInfo`
for that location.

When using PyInstaller, Nuitka, or another freezing tool, its packaging recipe
must copy those `.qm` files alongside Qt and the result should be verified on a
clean machine.

## Preventive prompt for creating or porting an application with an AI agent

```text
I am creating an application with Python/PyQt6 [or porting a C++/Qt application
to PyQt6]. Design a complete internationalization system from the beginning
that translates both application-specific text and standard Qt6 components.

Mandatory requirements:

1. Install QTranslator objects before constructing MainWindow or any dialog.
2. Load the official qtbase catalog for the selected QLocale first, followed
   by the application's own catalogs.
3. Obtain the primary path exclusively through
   QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath), or paths() when
   available. Do not assume /usr/share/qt6/translations.
4. Keep live references to every installed QTranslator and properly remove old
   translators when the language changes.
5. On Linux, add only an XDG_DATA_DIRS-based fallback for qt6/translations and
   qt/translations.
6. For Debian/Ubuntu, document sudo apt install qt6-translations-l10n and
   evaluate declaring it as Recommends in debian/control.
7. Explain that this package translates standard Qt widgets and does not
   replace the application's own translation catalogs.
8. For pip, Windows, and macOS, always follow the Qt runtime reported by
   QLibraryInfo and document that the final package must include
   qtbase_<locale>.qm.
9. Wrap every visible application title, filter, and text in self.tr() or
   QCoreApplication.translate(), then update catalogs through Qt Linguist.
10. Add tests for QFileDialog/Open and QPlatformTheme/Open in Spanish, plus at
    least one application-specific string.
11. If the optional Qt catalog is absent in a test environment, the integration
    test may be explicitly skipped, but directory-resolution logic must remain
    covered by unit tests.

Before implementing, inspect the project structure, startup sequence, existing
catalogs, Debian packaging, and pip strategy. Deliver the implementation,
tests, documentation, and wheel or package verification.
```

## Prompt for repairing an existing PyQt6 application

```text
Audit this PyQt6 application: its own menus are translated, but standard Qt6
dialogs—including Open, Save, and Cancel—appear in English.

Review i18n.py, QApplication/MainWindow construction order, every QTranslator,
QLocale, .ts/.qm catalogs, and packaging. Implement loading of
qtbase_<locale>.qm using QLibraryInfo.LibraryPath.TranslationsPath as the
primary source. Do not hardcode a Debian path.

Add a safe XDG_DATA_DIRS-based fallback on Linux only. Preserve compatibility
with PyQt6 installed from pip and with Windows and macOS deployments. Keep
QTranslator references alive, install qtbase before application catalogs, and
migrate any remaining visible title or filter literal to tr().

Update Qt Linguist catalogs, README, and debian/control. Document
qt6-translations-l10n as translations for standard Qt components, not as a
replacement for application translations. Add tests for QFileDialog/Open,
QPlatformTheme/Open, and at least one application string. Build the wheel and
run the complete test suite before finishing.
```

## Conclusion

Translating a Qt application involves more than compiling its own `.ts` file.
The application and framework have separate catalogs. Loading `qtbase` from
the location declared by the active runtime and then installing application
translators allows the same code to work with Debian packages, a virtual
environment, and properly prepared Windows or macOS distributions.
