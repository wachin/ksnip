import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication

from ksnip_py.spellcheck import SpellCheckTextEdit


APP = QApplication.instance() or QApplication([])


def _editor_without_qt_widget() -> SpellCheckTextEdit:
    editor = SpellCheckTextEdit()
    editor._spellcheck_scheme = [
        ("Red", QColor("#df5a17"), QColor("#ffffff")),
        ("White", QColor("#ffffff"), QColor("#000000")),
    ]
    return editor


def test_red_background_and_white_text_do_not_use_white_underline() -> None:
    editor = _editor_without_qt_widget()

    underline = editor._resolve_underline_color(QColor("#df5a17"), QColor("#ffffff"))

    assert underline == QColor("#000000")


def test_configured_color_is_kept_when_it_contrasts_with_background_and_text() -> None:
    editor = _editor_without_qt_widget()
    editor._spellcheck_scheme = [("White", QColor("#ffffff"), QColor("#c2255c"))]

    underline = editor._resolve_underline_color(QColor("#ffffff"), QColor("#000000"))

    assert underline == QColor("#c2255c")


def test_contrast_ratio_is_symmetric() -> None:
    black = QColor("#000000")
    white = QColor("#ffffff")

    assert SpellCheckTextEdit._contrast_ratio(black, white) == SpellCheckTextEdit._contrast_ratio(white, black)
