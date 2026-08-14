from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import QSettings, QUrl
from PyQt6.QtWidgets import QFileDialog


_URL_LIST_KEYS = ("shortcuts", "history")
_URL_KEYS = ("lastVisited",)


def _qt_file_dialog_settings() -> QSettings:
    # QFileDialog itself uses this organization-only store for its widget
    # implementation. It is intentionally not the application's QSettings.
    return QSettings(QSettings.Scope.UserScope, "QtProject")


def _url_from_persisted_value(value: object) -> QUrl:
    text = str(value)
    return QUrl.fromLocalFile(text) if text.startswith("/") else QUrl(text)


def _fully_encoded_url(value: object) -> str:
    url = value if isinstance(value, QUrl) else _url_from_persisted_value(value)
    if not url.isValid() or url.isEmpty():
        return str(value)
    if not url.scheme() and not str(value).startswith("/"):
        return str(value)
    if url.isLocalFile():
        local_path = url.toLocalFile()
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


def _run_dialog(method: Callable[..., Any], *args, **kwargs):
    normalize_qt_file_dialog_url_settings()
    try:
        return method(*args, **kwargs)
    finally:
        # Static QFileDialog helpers destroy their temporary dialog before
        # returning, which is when Qt writes sidebarUrls() back to QSettings.
        normalize_qt_file_dialog_url_settings()


def get_open_file_name(*args, **kwargs) -> tuple[str, str]:
    return _run_dialog(QFileDialog.getOpenFileName, *args, **kwargs)


def get_open_file_names(*args, **kwargs) -> tuple[list[str], str]:
    return _run_dialog(QFileDialog.getOpenFileNames, *args, **kwargs)


def get_save_file_name(*args, **kwargs) -> tuple[str, str]:
    return _run_dialog(QFileDialog.getSaveFileName, *args, **kwargs)
