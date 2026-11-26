"""Discovery contract for optional ksnip-pyqt6 OCR plugins.

The core must keep this module dependency-light.  A plugin is an installed
Python distribution that exposes an entry point in the ``ksnip_py.ocr`` group.
The plugin object is loaded lazily, and every failure is isolated so a broken
plugin cannot prevent ksnip-pyqt6 from starting.
"""

from __future__ import annotations

import logging
import os
from importlib.metadata import entry_points
from typing import Any

LOGGER = logging.getLogger(__name__)
ENTRY_POINT_GROUP = "ksnip_py.ocr"
PLUGIN_API_VERSION = 1

_TRUE_VALUES = {"1", "true", "yes", "on"}


def plugins_disabled() -> bool:
    """Return whether OCR plugin loading was explicitly disabled."""

    return os.environ.get("KSNIP_DISABLE_OCR_PLUGINS", "").strip().lower() in _TRUE_VALUES


def _entry_points():
    """Return the entry points for the OCR plugin group.

    Python versions differ in the exact ``entry_points`` calling convention;
    both the modern group= form and the older select() form are supported.
    """

    try:
        return entry_points(group=ENTRY_POINT_GROUP)
    except TypeError:
        return entry_points().select(group=ENTRY_POINT_GROUP)


def _plugin_is_valid(plugin: object) -> bool:
    return all(
        (
            getattr(plugin, "api_version", None) == PLUGIN_API_VERSION,
            isinstance(getattr(plugin, "plugin_id", None), str),
            isinstance(getattr(plugin, "plugin_name", None), str),
            callable(getattr(plugin, "is_available", None)),
            callable(getattr(plugin, "open_model_manager", None)),
            callable(getattr(plugin, "configure_script", None)),
        )
    )


def discover_ocr_plugins() -> list[Any]:
    """Load all valid installed OCR plugins.

    Discovery is intentionally best-effort.  Logged plugin failures are not
    fatal to the core application.  The returned objects are opaque to the
    core except for the small API checked here.
    """

    if plugins_disabled():
        LOGGER.info("OCR plugin discovery disabled by KSNIP_DISABLE_OCR_PLUGINS")
        return []

    plugins: list[Any] = []
    seen_ids: set[str] = set()
    try:
        points = _entry_points()
    except Exception:
        LOGGER.exception("Could not enumerate OCR plugin entry points")
        return []

    for entry_point in points:
        try:
            plugin_class = entry_point.load()
            plugin = plugin_class()
            if not _plugin_is_valid(plugin):
                LOGGER.warning(
                    "Ignoring OCR plugin %s: it does not implement API version %s",
                    entry_point.name,
                    PLUGIN_API_VERSION,
                )
                continue

            plugin_id = plugin.plugin_id
            if plugin_id in seen_ids:
                LOGGER.warning(
                    "Ignoring duplicate OCR plugin id %s from %s",
                    plugin_id,
                    entry_point.name,
                )
                continue
            seen_ids.add(plugin_id)
            plugins.append(plugin)
        except Exception:
            LOGGER.exception(
                "Could not load OCR plugin entry point %s",
                entry_point.name,
            )

    LOGGER.info("Loaded %d OCR plugin(s)", len(plugins))
    return plugins
