"""Bridge to the vendored ``pyqt6-linguistic-tools`` toolkit.

The toolkit lives in the ``libs/pyqt6-linguistic-tools`` git submodule.  It is a
portable spelling and thesaurus stack (Spylls + PyThes) with verified dictionary
downloads, and it is what makes spell checking work on **Windows**, where no
system Hunspell installation exists.

It is used on Windows only.  Linux distributions package hunspell and its
dictionaries, so ksnip prefers the system ``hunspell`` program there and this
module reports the toolkit as unavailable; a ``.deb``, wheel or PyInstaller build
therefore needs no submodule at all.  macOS keeps the same fallback because no
system Hunspell is guaranteed either.
"""

from __future__ import annotations

import importlib
import locale as _locale
import sys
from pathlib import Path
from typing import Any, Optional

TOOLKIT_DIRECTORY_NAME = "pyqt6-linguistic-tools"
DICTIONARY_NAMESPACE = "ksnip-pyqt6"

# Windows has no system Hunspell installation, so it is the only platform where
# ksnip uses the bundled toolkit. Linux distributions already package hunspell
# and its dictionaries, and the system backend is preferred there on purpose.
TOOLKIT_PLATFORMS = ("win32",)

_toolkit_checked = False
_toolkit_error: Optional[str] = None
_shared_service: Any = None


def toolkit_supported_platform() -> bool:
    """Return whether this platform uses the bundled toolkit at all."""

    return sys.platform in TOOLKIT_PLATFORMS


def repository_root() -> Path:
    """Return the directory that contains the ``ksnip_py`` package."""

    return Path(__file__).resolve().parent.parent


def toolkit_directory() -> Path:
    """Return the expected location of the linguistic toolkit submodule."""

    return repository_root() / "libs" / TOOLKIT_DIRECTORY_NAME


def reset_toolkit_cache() -> None:
    """Forget the import and service results (used by tests)."""

    global _toolkit_checked, _toolkit_error, _shared_service
    _close_service()
    _toolkit_checked = False
    _toolkit_error = None


def ensure_toolkit_importable() -> bool:
    """Put the submodule and its vendored engines on ``sys.path`` once."""

    global _toolkit_checked, _toolkit_error
    if _toolkit_checked:
        return _toolkit_error is None
    _toolkit_checked = True

    if not toolkit_supported_platform():
        _toolkit_error = (
            "the linguistic toolkit is used on Windows only; this system uses "
            "the hunspell program and the dictionaries of its distribution"
        )
        return False

    directory = toolkit_directory()
    if not directory.is_dir():
        _toolkit_error = f"toolkit directory not found: {directory}"
        return False
    try:
        if str(directory) not in sys.path:
            sys.path.insert(0, str(directory))
        # The bootstrap module adds src/, libs/spylls and libs/pythes.
        importlib.import_module("pyqt6_linguistic_tools_bootstrap")
        importlib.import_module("pyqt6_linguistic_tools")
    except Exception as exc:  # noqa: BLE001 - any import problem means "absent"
        _toolkit_error = f"{type(exc).__name__}: {exc}"
        return False
    _toolkit_error = None
    return True


def toolkit_available() -> bool:
    """Return whether the bundled toolkit can be imported."""

    return ensure_toolkit_importable()


def toolkit_error() -> Optional[str]:
    """Return why the toolkit is unavailable, or ``None`` when it works."""

    ensure_toolkit_importable()
    return _toolkit_error


def dictionary_storage_directory() -> Optional[Path]:
    """Return the directory holding managed, user and personal dictionaries."""

    if not ensure_toolkit_importable():
        return None
    try:
        from pyqt6_linguistic_tools import dictionary_storage_paths

        return dictionary_storage_paths(DICTIONARY_NAMESPACE).root
    except Exception:  # noqa: BLE001
        return None


def _system_languages() -> list[str]:
    """Return likely system locales, most specific first."""

    candidates: list[str] = []
    # Qt reads the Windows/desktop regional settings and never depends on the
    # deprecated locale.getdefaultlocale().
    try:
        from PyQt6.QtCore import QLocale

        name = str(QLocale.system().name() or "")
        if name and name not in {"C", "POSIX"}:
            candidates.append(name)
    except Exception:  # noqa: BLE001
        pass
    try:
        import os

        for variable in ("LC_ALL", "LC_MESSAGES", "LANG"):
            value = os.environ.get(variable, "").split(".")[0]
            if value and value not in {"C", "POSIX"}:
                candidates.append(value)
    except Exception:  # noqa: BLE001
        pass
    if not candidates:
        try:
            import warnings

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                language, _encoding = _locale.getdefaultlocale()
            if language:
                candidates.append(language)
        except Exception:  # noqa: BLE001
            pass
    return candidates


def preferred_languages() -> tuple[str, ...]:
    """Return configured and system locales in priority order."""

    values: list[str] = []
    try:
        from PyQt6.QtCore import QSettings

        configured = str(QSettings().value("application/language", "") or "")
    except Exception:  # noqa: BLE001
        configured = ""
    if configured:
        values.append(configured)
    values.extend(_system_languages())
    return tuple(value for value in dict.fromkeys(values) if value)


def _normalize(value: str) -> str:
    return value.replace("-", "_").strip()


def resolve_spellcheck_locale(
    service: Any,
    preferred: tuple[str, ...] = (),
) -> Optional[str]:
    """Pick the installed dictionary locale that best matches the user.

    Exact matches win, then another regional variant of the same language, then
    any locale that has spelling, so a user with only ``es_ES`` installed still
    gets Spanish checking while asking for ``es_EC``.

    Only locales that actually provide spelling are considered: a
    thesaurus-only bundle must not shadow a spelling dictionary.
    """

    try:
        available = tuple(service.available_languages())
    except Exception:  # noqa: BLE001
        return None
    if not available:
        return None

    usable: dict[str, bool] = {}

    def has_spelling(locale_name: str) -> bool:
        if locale_name not in usable:
            try:
                usable[locale_name] = bool(
                    service.capabilities(locale_name).spell_check
                )
            except Exception:  # noqa: BLE001
                usable[locale_name] = False
        return usable[locale_name]

    wanted = [_normalize(value) for value in preferred if value]
    wanted.extend(_normalize(value) for value in (_system_languages() or []))

    for locale_name in wanted:
        if locale_name in available and has_spelling(locale_name):
            return locale_name
    for locale_name in wanted:
        language = locale_name.split("_")[0]
        for candidate in available:
            if candidate.split("_")[0] == language and has_spelling(candidate):
                return candidate
    for candidate in available:
        if has_spelling(candidate):
            return candidate
    return available[0]


def shared_service() -> Any:
    """Return the process-wide linguistic service, creating it on first use."""

    global _shared_service, _toolkit_error
    if _shared_service is not None:
        return _shared_service
    if not ensure_toolkit_importable():
        return None
    try:
        from pyqt6_linguistic_tools import create_service

        _shared_service = create_service(namespace=DICTIONARY_NAMESPACE)
    except Exception as exc:  # noqa: BLE001
        _toolkit_error = f"{type(exc).__name__}: {exc}"
        return None
    return _shared_service


def _close_service() -> None:
    global _shared_service
    service = _shared_service
    _shared_service = None
    if service is not None:
        try:
            service.close()
        except Exception:  # noqa: BLE001
            pass


def reset_shared_service() -> None:
    """Drop the cached service so new dictionaries are discovered."""

    _close_service()


def install_toolkit_translations(app: Any, language: Optional[str] = None) -> bool:
    """Install the toolkit's own Qt catalog for *language* on *app*."""

    if not ensure_toolkit_importable():
        return False
    try:
        from pyqt6_linguistic_tools.qt import install_toolkit_translations as install

        return install(app, language) is not None
    except Exception:  # noqa: BLE001
        return False


def spelling_summary() -> str:
    """Return a short human-readable state for diagnostics and status bars."""

    if not toolkit_available():
        return "hunspell"
    service = shared_service()
    if service is None:
        return "unavailable"
    locale_name = resolve_spellcheck_locale(service, preferred_languages())
    if locale_name is None:
        return "no dictionaries"
    try:
        capabilities = service.capabilities(locale_name)
    except Exception:  # noqa: BLE001
        return "no dictionaries"
    parts = [locale_name]
    parts.append("spelling" if capabilities.spell_check else "no spelling")
    if capabilities.thesaurus:
        parts.append("thesaurus")
    return ", ".join(parts)
