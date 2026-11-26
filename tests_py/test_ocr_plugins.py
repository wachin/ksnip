import os
import unittest
from unittest.mock import patch

from ksnip_py.ocr_plugins import discover_ocr_plugins


class FakePlugin:
    api_version = 1
    plugin_id = "fake"
    plugin_name = "Fake OCR"

    def is_available(self) -> bool:
        return True

    def open_model_manager(self, parent=None, settings=None) -> bool:
        return True

    def configure_script(self, settings=None) -> bool:
        return True


class WrongVersionPlugin(FakePlugin):
    api_version = 99


class FakeEntryPoint:
    def __init__(self, name: str, loaded) -> None:
        self.name = name
        self._loaded = loaded

    def load(self):
        if isinstance(self._loaded, Exception):
            raise self._loaded
        return self._loaded


class OcrPluginDiscoveryTest(unittest.TestCase):
    def test_valid_entry_point_is_discovered(self) -> None:
        with patch(
            "ksnip_py.ocr_plugins.entry_points",
            return_value=[FakeEntryPoint("paddle", FakePlugin)],
        ):
            plugins = discover_ocr_plugins()
        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0].plugin_id, "fake")

    def test_disabled_discovery_returns_no_plugins(self) -> None:
        with (
            patch.dict(os.environ, {"KSNIP_DISABLE_OCR_PLUGINS": "1"}),
            patch(
                "ksnip_py.ocr_plugins.entry_points",
                return_value=[FakeEntryPoint("paddle", FakePlugin)],
            ),
        ):
            self.assertEqual(discover_ocr_plugins(), [])

    def test_broken_plugin_is_isolated(self) -> None:
        with patch(
            "ksnip_py.ocr_plugins.entry_points",
            return_value=[FakeEntryPoint("broken", RuntimeError("boom"))],
        ):
            self.assertEqual(discover_ocr_plugins(), [])

    def test_incompatible_api_is_ignored(self) -> None:
        with patch(
            "ksnip_py.ocr_plugins.entry_points",
            return_value=[FakeEntryPoint("old", WrongVersionPlugin)],
        ):
            self.assertEqual(discover_ocr_plugins(), [])

    def test_duplicate_plugin_ids_are_ignored(self) -> None:
        with patch(
            "ksnip_py.ocr_plugins.entry_points",
            return_value=[
                FakeEntryPoint("first", FakePlugin),
                FakeEntryPoint("second", FakePlugin),
            ],
        ):
            plugins = discover_ocr_plugins()
        self.assertEqual(len(plugins), 1)


if __name__ == "__main__":
    unittest.main()
