from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QLocale, QTranslator


_translators: list[QTranslator] = []

def load_translation(app, locale_name: str | None = None) -> str:
    locale = QLocale(locale_name) if locale_name else QLocale.system()
    translations_path = Path(__file__).resolve().parent / "translations"
    translator = QTranslator(app)
    loaded = translator.load(locale, "ksnip_py", "_", str(translations_path))
    if loaded:
        app.installTranslator(translator)
        _translators.append(translator)
    return locale.name()
