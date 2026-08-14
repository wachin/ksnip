# How to Preserve Unicode Bookmarks Correctly in PyQt6 File Dialogs

When developing a PyQt6 application, files are commonly opened with
`QFileDialog.getOpenFileName()` and saved with
`QFileDialog.getSaveFileName()`. The API is convenient, but the dialog shown
to the user does not always come from the same component: it may be the
platform's native file chooser or Qt's widget-based dialog.

This difference matters when users drag directories into the sidebar to create
favorite places. A bookmark such as:

```text
/home/user/Pictures
/home/user/Música
/home/user/Documentación
```

may work while the application remains open and fail after a complete restart.
This article explains how to investigate that problem without immediately
blaming UTF-8, manually converting strings to bytes, or disabling native file
dialogs indiscriminately.

## Do not start by forcing `DontUseNativeDialog`

This option forces Qt to build its widget-based dialog:

```python
QFileDialog.Option.DontUseNativeDialog
```

It is useful for a comparative test, but it should not become the first or
final solution without a diagnosis. Forcing it can discard GTK, KDE, Windows,
or macOS integration, special system locations, portals, and desktop styling.

According to the official
[`QFileDialog` documentation](https://doc.qt.io/qt-6/qfiledialog.html), Qt uses
the native file dialog when the platform provides one. When a native helper is
active, widget-specific APIs such as `layout()` may return `None`.

The following temporary test compares both configurations and inspects their
internal widgets:

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
        "forced=" if force_qt_widgets else "default=",
        "layout:", bool(dialog.layout()),
        "internal views:", views,
    )
    dialog.close()
```

Run this test with a temporary configuration directory so it does not modify
the user's real bookmarks:

```bash
XDG_CONFIG_HOME="$(mktemp -d)" python3 dialog_test.py
```

In the case that motivated this article—Debian 13 with AV Linux MXe, Qt 6.8,
and the `qt6ct` platform theme—the default configuration and the explicit
`DontUseNativeDialog` configuration both produced the Qt Widgets dialog.
Forcing the option could not fix the issue because the dialog was already the
Qt implementation.

## Find out who stores the bookmarks

Native dialogs manage favorite places through platform-specific mechanisms.
GTK, for example, may use:

```text
~/.config/gtk-3.0/bookmarks
```

A valid Unicode entry may look like this:

```text
file:///home/user/Im%C3%A1genes
file:///home/user/M%C3%BAsica
```

The Qt Widgets dialog uses a different persistence store. Qt6 source code
shows that `QFileDialogPrivate::saveSettings()` creates:

```cpp
QSettings settings(QSettings::UserScope, u"QtProject"_s);
settings.beginGroup("FileDialog");
```

and stores `shortcuts`, `history`, and `lastVisited` there. On Linux, these
values normally end up in:

```text
~/.config/QtProject.conf
```

Qt saves the sidebar through `QUrl::toStringList()` and reconstructs it with
`QUrl::fromStringList()`. This behavior can be inspected in the
[Qt6 QFileDialog source code](https://codebrowser.dev/qt6/qtbase/src/widgets/dialogs/qfiledialog.cpp.html).

This is why blindly modifying GTK's bookmark file is wrong when the visible
dialog is actually provided by Qt Widgets.

## The correct way to handle a Unicode path

PyQt6 returns local paths as `str`. They do not need to be manually converted
to UTF-8 before being passed to Qt:

```python
from PyQt6.QtCore import QUrl

path = "/home/user/Imágenes"
url = QUrl.fromLocalFile(path)

print(url.toString())
# file:///home/user/Imágenes

print(url.toString(QUrl.ComponentFormattingOption.FullyEncoded))
# file:///home/user/Im%C3%A1genes

print(url.toLocalFile())
# /home/user/Imágenes
```

The correct conversion cycle is:

```text
local str → QUrl.fromLocalFile() → persisted URL → QUrl.toLocalFile() → local str
```

Operations such as these are unnecessary:

```python
path.encode("utf-8")
path.decode("utf-8")
urllib.parse.quote(path)
urllib.parse.unquote(path)
```

Combining those operations with `QUrl` can cause double encoding, producing
`%25C3%25A1` instead of `%C3%A1`.

## A robust solution for the Qt Widgets dialog

The solution is to let Qt select the appropriate backend and normalize only
its own `QtProject/FileDialog` persistence before and after each dialog. URLs
are stored using `FullyEncoded`; the INI boundary remains ASCII-only while
`toLocalFile()` still restores the original Unicode path.

All file dialogs can be centralized in a module:

```python
from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import QSettings, QUrl
from PyQt6.QtWidgets import QFileDialog


URL_LIST_KEYS = ("shortcuts", "history")
URL_KEYS = ("lastVisited",)


def qt_file_dialog_settings() -> QSettings:
    # This is the same store used internally by Qt Widgets QFileDialog.
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
        # The static helper has destroyed its QFileDialog and Qt has saved it.
        normalize_file_dialog_urls()


def get_open_file_name(*args, **kwargs) -> tuple[str, str]:
    return run_dialog(QFileDialog.getOpenFileName, *args, **kwargs)


def get_open_file_names(*args, **kwargs) -> tuple[list[str], str]:
    return run_dialog(QFileDialog.getOpenFileNames, *args, **kwargs)


def get_save_file_name(*args, **kwargs) -> tuple[str, str]:
    return run_dialog(QFileDialog.getSaveFileName, *args, **kwargs)
```

The rest of the application no longer calls `QFileDialog` directly:

```python
from .file_dialogs import get_open_file_name

path, selected_filter = get_open_file_name(
    parent,
    parent.tr("Open image"),
    initial_directory,
    parent.tr("Images (*.png *.jpg *.jpeg *.webp)"),
)
```

This technique does not change native bookmarks belonging to GTK, KDE,
Windows, or macOS. When the backend is Qt Widgets, it stabilizes the
representation persisted by Qt.

## A regression test that simulates a restart

A useful test must close and reopen the settings store instead of checking a
value that remains cached in memory:

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
            "file:///home/user/Imágenes",
            "file:///home/user/Música",
        ])
        settings.endGroup()

        normalize_file_dialog_urls(settings)
        settings.sync()
        del settings

        restored = QSettings(filename, QSettings.Format.IniFormat)
        restored.beginGroup("FileDialog")
        urls = restored.value("shortcuts")
        restored.endGroup()

        assert urls[0] == "file:///home/user/Im%C3%A1genes"
        assert QUrl(urls[0]).toLocalFile() == "/home/user/Imágenes"
        assert QUrl(urls[1]).toLocalFile() == "/home/user/Música"
```

The final manual test should reproduce the user's workflow:

1. Start the application.
2. Open a file dialog.
3. Drag `Imágenes` or `Música` into the sidebar.
4. Close the application completely.
5. Start it again.
6. Open the dialog and enter the directory through the bookmark.

## Preventive prompt for an AI agent

Use this prompt before creating a PyQt6 application or starting a C++/Qt to
PyQt6 port:

```text
I am creating a desktop application with Python and PyQt6 [or porting a C++/Qt
application to PyQt6]. Design a centralized layer from the beginning for all
Open, Open Multiple, Save, and Save As dialogs.

Mandatory requirements:

1. Do not globally force QFileDialog.Option.DontUseNativeDialog. Allow Qt to
   use the native dialog when the platform provides one.
2. Explicitly distinguish native dialogs from Qt Widgets QFileDialog.
3. Keep paths as str/QString. Convert local paths with QUrl.fromLocalFile() and
   recover them with QUrl.toLocalFile().
4. Do not use encode(), decode(), urllib.parse.quote(), or unquote() for paths.
5. Ensure sidebar bookmarks containing Unicode characters, such as Imágenes,
   Música, or Documentación, survive a complete application restart.
6. If the Qt Widgets backend persists sidebarUrls() in QtProject/FileDialog,
   normalize shortcuts, history, and lastVisited with
   QUrl.ComponentFormattingOption.FullyEncoded before and after each dialog.
7. Do not alter native GTK, KDE, Windows, or macOS bookmark stores.
8. Centralize getOpenFileName(), getOpenFileNames(), and getSaveFileName() in a
   reusable module. Do not leave direct calls scattered across the project.
9. Add automated tests with temporary QSettings that simulate a real process
   restart and verify exact Unicode path round-trips.
10. Document the tested backend, relevant environment variables, QUrl,
    percent encoding, and Linux/Windows/macOS differences.

Before implementing anything, inspect the complete project and explain with
evidence which backend is in use. Do not present DontUseNativeDialog as a fix
without comparing both behaviors.
```

## Prompt for repairing an existing application

```text
Audit this PyQt6 application because file-dialog sidebar bookmarks work during
the current execution but fail after a restart when a path contains Unicode,
for example Imágenes or Música.

Locate every QFileDialog call and determine whether the failure occurs with
the native dialog, Qt Widgets with DontUseNativeDialog, or both. Inspect
sidebarUrls(), QUrl, QSettings(UserScope, "QtProject"), the FileDialog group,
desktop bookmark stores, locale, and QT/XDG environment variables.

Do not force DontUseNativeDialog as a general fix. Do not introduce manual
encode/decode or quote/unquote conversions. Use QUrl.fromLocalFile(),
QUrl.toLocalFile(), and FullyEncoded when evidence shows that Qt Widgets
persistence must be stabilized.

Implement a shared Open/Save layer, migrate every call in the project, preserve
native integration, and add process-restart tests using Imágenes, Música, and
Documentación. Document the identified cause and run the complete test suite
before finishing.
```

## Conclusion

A path containing an accent is not a collection of bytes that the application
must repair. It is a Unicode string that Qt can handle. The correct work is to
identify which dialog and persistence store owns the bookmark, keep all path
conversion inside `QUrl`, and test the boundary that actually failed: closing
and restarting the process.
