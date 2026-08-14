from __future__ import annotations

import os
from pathlib import Path
import sys

from PyQt6.QtCore import QLibraryInfo, QLocale, QTranslator


_translators: list[QTranslator] = []


def qt_translation_directories() -> list[Path]:
    """Return portable Qt translation locations in preference order."""

    translation_path = QLibraryInfo.LibraryPath.TranslationsPath
    try:
        configured = QLibraryInfo.paths(translation_path)
    except AttributeError:  # PyQt6/Qt older than 6.8
        configured = [QLibraryInfo.path(translation_path)]

    candidates = [Path(path) for path in configured if path]
    if sys.platform.startswith("linux"):
        data_roots = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share")
        for root in data_roots.split(os.pathsep):
            if root:
                candidates.extend((Path(root) / "qt6" / "translations", Path(root) / "qt" / "translations"))

    unique: list[Path] = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    return unique


def _install_translator(app, locale: QLocale, catalog: str, directories: list[Path]) -> bool:
    for directory in directories:
        translator = QTranslator(app)
        if translator.load(locale, catalog, "_", str(directory)):
            app.installTranslator(translator)
            _translators.append(translator)
            return True
    return False


def available_languages() -> list[tuple[str, str]]:
    translations_path = Path(__file__).resolve().parent / "translations"
    locales = {path.stem.removeprefix("ksnip_py_") for path in translations_path.glob("ksnip_py_*.qm")}
    languages: list[tuple[str, str]] = []
    for locale_name in locales:
        locale = QLocale(locale_name)
        label = locale.nativeLanguageName().strip() or locale_name
        if "_" in locale_name:
            territory = locale.nativeTerritoryName().strip()
            if territory:
                label = f"{label} ({territory})"
        languages.append((label[:1].upper() + label[1:], locale_name))
    return sorted(languages, key=lambda entry: entry[0].casefold())

def load_translation(app, locale_name: str | None = None) -> str:
    for translator in _translators:
        app.removeTranslator(translator)
        translator.deleteLater()
    _translators.clear()

    locale = QLocale(locale_name) if locale_name else QLocale.system()
    translations_path = Path(__file__).resolve().parent / "translations"
    _install_translator(app, locale, "qtbase", qt_translation_directories())
    for catalog in ("ksnip", "ksnip_py"):
        _install_translator(app, locale, catalog, [translations_path])
    return locale.name()
