from __future__ import annotations

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QPushButton, QTextEdit, QVBoxLayout


class OcrResultDialog(QDialog):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("OCR Text Recognition")
        self.resize(720, 520)

        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(text)
        layout.addWidget(self.text_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        copy_button = QPushButton("Copy to Clipboard", self)
        buttons.addButton(copy_button, QDialogButtonBox.ButtonRole.ActionRole)
        copy_button.clicked.connect(self.copy_to_clipboard)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def copy_to_clipboard(self) -> None:
        QGuiApplication.clipboard().setText(self.text_edit.toPlainText())
