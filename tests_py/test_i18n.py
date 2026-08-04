import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QApplication

from ksnip_py.i18n import available_languages, load_translation


APP = QApplication.instance() or QApplication([])


class TranslationCatalogTest(unittest.TestCase):
    def test_all_generated_catalogs_are_discovered(self) -> None:
        languages = dict(available_languages())
        self.assertEqual(len(languages), 41)
        self.assertIn("de", languages.values())
        self.assertIn("pt_BR", languages.values())
        self.assertIn("zh_Hant", languages.values())

    def test_python_context_uses_reused_upstream_translation(self) -> None:
        load_translation(APP, "de")
        self.assertEqual(QCoreApplication.translate("MainWindow", "Save"), "Speichern")
        self.assertEqual(QCoreApplication.translate("MainWindow", "Settings"), "Einstellungen")


if __name__ == "__main__":
    unittest.main()
