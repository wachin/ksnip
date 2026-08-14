import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QCoreApplication, QLibraryInfo
from PyQt6.QtWidgets import QApplication

from ksnip_py.i18n import available_languages, load_translation, qt_translation_directories


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

    def test_qtbase_catalog_translates_standard_file_dialog_controls(self) -> None:
        if not any((path / "qtbase_es.qm").is_file() for path in qt_translation_directories()):
            self.skipTest("optional Qt Spanish translation catalog is not installed")
        load_translation(APP, "es_EC")
        self.assertEqual(QCoreApplication.translate("QFileDialog", "Open"), "Abrir")
        self.assertEqual(QCoreApplication.translate("QPlatformTheme", "Open"), "Abrir")
        self.assertEqual(QCoreApplication.translate("MainWindow", "Open image"), "Abrir imagen")

    def test_qt_runtime_translation_path_is_the_primary_location(self) -> None:
        expected = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
        self.assertEqual(str(qt_translation_directories()[0]), expected)


if __name__ == "__main__":
    unittest.main()
