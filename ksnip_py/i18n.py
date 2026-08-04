from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QLocale, QTranslator


_translators: list[QTranslator] = []


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
    locale = QLocale(locale_name) if locale_name else QLocale.system()
    translations_path = Path(__file__).resolve().parent / "translations"
    for catalog in ("ksnip", "ksnip_py"):
        translator = QTranslator(app)
        if translator.load(locale, catalog, "_", str(translations_path)):
            app.installTranslator(translator)
            _translators.append(translator)
    return locale.name()
