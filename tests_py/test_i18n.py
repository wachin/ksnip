import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QLocale, QTranslator
from PyQt6.QtWidgets import QApplication, QFileDialog, QLabel

from ksnip_py.i18n import _QtFallbackTranslator, load_translation, qt_translation_directories


APP = QApplication.instance() or QApplication([])


class _FakeQtTranslator(QTranslator):
    def translate(self, context, source_text, disambiguation=None, n=-1):  # noqa: N802
        if context == "QFileDialog" and source_text == "Look in:":
            return "Ver en:"
        return ""


class QtTranslationTest(unittest.TestCase):
    def test_fallback_restores_the_mnemonic_for_a_qt_label(self) -> None:
        fallback = _QtFallbackTranslator([_FakeQtTranslator()])
        self.assertEqual(fallback.translate("QFileDialog", "&Look in:"), "&Ver en:")

    def test_spanish_qt_file_dialog_labels_are_translated(self) -> None:
        if not any((directory / "qtbase_es.qm").exists() for directory in qt_translation_directories()):
            self.skipTest("qtbase_es.qm is not installed")

        try:
            load_translation(APP, "es")
            self.assertTrue(QLocale().name().startswith("es"))

            dialog = QFileDialog()
            dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
            labels = [label.text() for label in dialog.findChildren(QLabel)]
            self.assertIn("&Ver en:", labels)
            self.assertNotIn("&Look in:", labels)
        finally:
            load_translation(APP, "en")


if __name__ == "__main__":
    unittest.main()
