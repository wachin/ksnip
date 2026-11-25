from __future__ import annotations

from pathlib import Path
from typing import Any

from PyQt6.QtCore import QByteArray, QCoreApplication, QEvent, QSettings, QUrl
from PyQt6.QtWidgets import QApplication, QDialog, QFileDialog


_URL_LIST_KEYS = ("shortcuts", "history")
_URL_KEYS = ("lastVisited",)


def _qt_file_dialog_settings() -> QSettings:
    # QFileDialog itself uses this organization-only store for its widget
    # implementation. It is intentionally not the application's QSettings.
    return QSettings(QSettings.Scope.UserScope, "QtProject")


def _url_from_persisted_value(value: object) -> QUrl:
    text = str(value)
    return QUrl.fromLocalFile(text) if text.startswith("/") else QUrl(text)


def _repair_mojibake_path(path: str) -> str:
    """Undo repeated UTF-8/Latin-1 mojibake in an existing local path.

    Older Qt file-dialog sessions could persist a sidebar URL whose path had
    been decoded as Latin-1 one or more times (``Imágenes`` becoming
    ``ImÃ¡genes`` and so on). Only accept a repaired spelling when that path
    actually exists, so a legitimate filename containing ``Ã`` is untouched.
    """

    if not path or Path(path).exists():
        return path
    candidate = path
    for _ in range(6):
        try:
            candidate = candidate.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        if Path(candidate).exists():
            return candidate

    # Very old sessions may have lost bytes and cannot be decoded losslessly.
    # Match the surviving ASCII skeleton against real sibling directories,
    # accepting the repair only when exactly one directory matches.
    original = Path(path)
    skeleton = "".join(char for char in original.name if ord(char) < 128)
    if skeleton and original.parent.is_dir():
        try:
            candidates = [
                child
                for child in original.parent.iterdir()
                if child.is_dir()
                and "".join(char for char in child.name if ord(char) < 128) == skeleton
            ]
        except OSError:
            candidates = []
        if len(candidates) == 1:
            return str(candidates[0])
    return path


def _fully_encoded_url(value: object) -> str:
    url = value if isinstance(value, QUrl) else _url_from_persisted_value(value)
    if not url.isValid() or url.isEmpty():
        return str(value)
    if not url.scheme() and not str(value).startswith("/"):
        return str(value)
    if url.isLocalFile():
        local_path = _repair_mojibake_path(url.toLocalFile())
        if local_path:
            url = QUrl.fromLocalFile(local_path)
    return url.toString(QUrl.ComponentFormattingOption.FullyEncoded)


def normalize_qt_file_dialog_url_settings(settings: QSettings | None = None) -> None:
    """Keep Qt Widgets file-dialog URLs lossless across process restarts.

    Qt's non-native QFileDialog stores sidebar and history URLs in the global
    ``QtProject/FileDialog`` settings group using their pretty-decoded string
    representation. Rewriting those same QUrls in FullyEncoded form keeps the
    INI boundary ASCII-only while QUrl.toLocalFile() still returns the original
    Unicode path. Native dialogs keep using their platform-owned bookmarks.
    """

    store = settings or _qt_file_dialog_settings()
    store.beginGroup("FileDialog")
    try:
        for key in _URL_LIST_KEYS:
            if not store.contains(key):
                continue
            value = store.value(key, [])
            values = value if isinstance(value, list) else [value]
            store.setValue(key, [_fully_encoded_url(item) for item in values])
        for key in _URL_KEYS:
            if store.contains(key):
                store.setValue(key, _fully_encoded_url(store.value(key)))
    finally:
        store.endGroup()
    store.sync()


def _dialog_settings() -> QSettings:
    return QSettings()


def _dialog_arguments(args: tuple[Any, ...], kwargs: dict[str, Any]) -> tuple[Any, str, str, str, str, QFileDialog.Option]:
    parent = args[0] if len(args) > 0 else kwargs.get("parent")
    caption = args[1] if len(args) > 1 else kwargs.get("caption", "")
    directory = args[2] if len(args) > 2 else kwargs.get("directory", "")
    name_filter = args[3] if len(args) > 3 else kwargs.get("filter", "")
    initial_filter = args[4] if len(args) > 4 else kwargs.get("initialFilter", "")
    options = args[5] if len(args) > 5 else kwargs.get("options", QFileDialog.Option(0))
    if options is None:
        options = QFileDialog.Option(0)
    return parent, str(caption or ""), str(directory or ""), str(name_filter or ""), str(initial_filter or ""), QFileDialog.Option(options)


class _GeometryFileDialog(QFileDialog):
    """QFileDialog that applies a saved geometry after Qt has shown it."""

    def __init__(self, *args, geometry: Any = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._pending_geometry = geometry

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        geometry = self._pending_geometry
        self._pending_geometry = None
        _restore_geometry(self, geometry)


def _restore_geometry(dialog: QFileDialog, stored: Any) -> None:
    if stored is None:
        return
    if isinstance(stored, QByteArray):
        geometry = stored
    elif isinstance(stored, (bytes, bytearray)):
        geometry = QByteArray(stored)
    else:
        return
    if not geometry.isEmpty():
        dialog.restoreGeometry(geometry)


def _run_dialog(mode: str, args: tuple[Any, ...], kwargs: dict[str, Any]):
    parent, caption, directory, name_filter, initial_filter, options = _dialog_arguments(args, kwargs)
    key = "dialogs/save_geometry" if mode == "save" else "dialogs/open_geometry"
    settings = _dialog_settings()
    dialog = _GeometryFileDialog(
        parent,
        caption,
        directory,
        name_filter,
        geometry=settings.value(key),
    )
    if mode == "open_many":
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
    elif mode == "save":
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
    else:
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
    if options:
        dialog.setOptions(options)
    if initial_filter:
        dialog.selectNameFilter(initial_filter)

    accepted = False
    files: list[str] = []
    selected_filter = ""
    normalize_qt_file_dialog_url_settings()
    try:
        accepted = dialog.exec() == QDialog.DialogCode.Accepted
        if accepted:
            files = dialog.selectedFiles()
            selected_filter = dialog.selectedNameFilter()
    finally:
        settings.setValue(key, dialog.saveGeometry())
        settings.sync()
        dialog.close()
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(dialog, QEvent.Type.DeferredDelete)
        QApplication.processEvents()
        normalize_qt_file_dialog_url_settings()

    if mode == "open_many":
        return files, selected_filter
    return (files[0] if files else ""), selected_filter


def get_open_file_name(*args, **kwargs) -> tuple[str, str]:
    return _run_dialog("open", args, kwargs)


def get_open_file_names(*args, **kwargs) -> tuple[list[str], str]:
    return _run_dialog("open_many", args, kwargs)


def get_save_file_name(*args, **kwargs) -> tuple[str, str]:
    return _run_dialog("save", args, kwargs)
