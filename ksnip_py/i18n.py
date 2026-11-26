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

    candidates: list[Path] = []
    if sys.platform.startswith("linux"):
        # Prefer the distribution package (qt6-translations-l10n) on Linux;
        # fall back to the Qt deployment selected by PyQt6.
        data_roots = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share")
        for root in data_roots.split(os.pathsep):
            if root:
                candidates.extend((Path(root) / "qt6" / "translations", Path(root) / "qt" / "translations"))
    candidates.extend(Path(path) for path in configured if path)

    unique: list[Path] = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    return unique


class _QtFallbackTranslator(QTranslator):
    """Fill Qt's missing mnemonic-prefixed variants.

    Some QFileDialog labels are asked for as ``&Look in:`` while the official
    qtbase catalog only contains ``Look in:``. Qt then leaves the label in
    English even though the catalog is loaded. Query the catalog without the
    leading ampersand and restore the mnemonic in the translated text.
    """

    def __init__(self, bases: list[QTranslator], parent=None) -> None:
        super().__init__(parent)
        self._bases = bases

    def translate(self, context, source_text, disambiguation=None, n=-1):  # noqa: N802
        for base in self._bases:
            try:
                text = base.translate(context, source_text, disambiguation or "", n)
            except UnicodeEncodeError:
                # QTranslator::translate takes a const char* source string.
                # PyQt6 encodes that argument as ASCII, so a plugin or caller
                # cannot use a non-ASCII source literal in tr().  Translation
                # catalogs may still return Unicode text; only the lookup key
                # has to remain ASCII.
                continue
            if text:
                return text
        if source_text.startswith("&"):
            stripped = source_text[1:]
            for base in self._bases:
                try:
                    text = base.translate(context, stripped, disambiguation or "", n)
                except UnicodeEncodeError:
                    continue
                if text:
                    return text if "&" in text else "&" + text
        # QTranslator subclasses must provide a displayable fallback.  Returning
        # an empty string makes untranslated plugin/UI strings disappear.
        return source_text


def _load_translator(app, locale: QLocale, catalog: str, directories: list[Path]) -> QTranslator | None:
    for directory in directories:
        translator = QTranslator(app)
        if translator.load(locale, catalog, "_", str(directory)):
            return translator
    return None


def _install_translator(app, locale: QLocale, catalog: str, directories: list[Path]) -> QTranslator | None:
    translator = _load_translator(app, locale, catalog, directories)
    if translator is not None:
        app.installTranslator(translator)
        _translators.append(translator)
    return translator


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
    QLocale.setDefault(locale)
    translations_path = Path(__file__).resolve().parent / "translations"
    qt_directories = qt_translation_directories()
    qt_translators: list[QTranslator] = []
    for catalog in ("qtbase", "qt"):
        translator = _install_translator(app, locale, catalog, qt_directories)
        if translator is not None:
            qt_translators.append(translator)
    if qt_translators:
        fallback = _QtFallbackTranslator(qt_translators, app)
        app.installTranslator(fallback)
        _translators.append(fallback)
    for catalog in ("ksnip", "ksnip_py"):
        _install_translator(app, locale, catalog, [translations_path])
    return locale.name()
