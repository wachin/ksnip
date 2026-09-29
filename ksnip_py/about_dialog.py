from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QCoreApplication, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)


ICON_SIZE = 128
HOME_PAGE_URL = "https://github.com/wachin/ksnip"
ORIGINAL_PROJECT_URL = "https://github.com/ksnip/ksnip"
ORIGINAL_AUTHOR = "Damir Porobic"
SUPPORT_EMAIL = "linuxfrontier@proton.me"


class AboutDialog(QDialog):
    """Two-column about panel: large centred logo on the left, details on the right."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("About ksnip PyQt6"))

        layout = QVBoxLayout(self)

        body = QHBoxLayout()
        body.setSpacing(18)
        layout.addLayout(body)

        self.icon_label = QLabel(self)
        self.icon_label.setPixmap(self._load_logo())
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        body.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)

        self.details = QLabel(self)
        self.details.setTextFormat(Qt.TextFormat.RichText)
        self.details.setWordWrap(True)
        self.details.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self.details.setOpenExternalLinks(True)
        self.details.setAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.details.setFixedWidth(430)
        self.details.setText(self._details_html())
        body.addWidget(self.details, 1, Qt.AlignmentFlag.AlignVCenter)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)
        if close_button := buttons.button(QDialogButtonBox.StandardButton.Close):
            close_button.clicked.connect(self.reject)
        layout.addWidget(buttons)

        self.resize(620, self.sizeHint().height())

    def _load_logo(self) -> QPixmap:
        icon_path = Path(__file__).resolve().parent / "icons" / "ksnip.svg"
        pixmap = QPixmap(str(icon_path))
        if pixmap.isNull():
            return pixmap
        return pixmap.scaled(
            ICON_SIZE,
            ICON_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _details_html(self) -> str:
        version = QCoreApplication.applicationVersion() or "0.1.0"
        rows = [
            (
                self.tr("Original project"),
                f'<a href="{ORIGINAL_PROJECT_URL}">{ORIGINAL_PROJECT_URL}</a> {ORIGINAL_AUTHOR}',
            ),
            (self.tr("PyQt6 port"), "Washington Indacochea Delgado"),
            (self.tr("Copyright"), f"&copy; 2026 Washington Indacochea Delgado"),
            (self.tr("Email"), f'<a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a>'),
            (self.tr("Website"), f'<a href="{HOME_PAGE_URL}">{HOME_PAGE_URL}</a>'),
            (self.tr("License"), '<a href="https://www.gnu.org/licenses/gpl-3.0.html">GPL-3.0</a>'),
        ]
        table = "".join(
            f'<tr><td valign="top"><b>{label}:</b></td><td valign="top">&nbsp;{value}</td></tr>'
            for label, value in rows
        )
        return f"""
<h2 style="margin-bottom:0;">ksnip PyQt6</h2>
<p style="margin-top:0;">{self.tr("Version")} {version}</p>
<p>{self.tr("A screenshot and annotation tool, ported from the original C++/Qt ksnip to Python with PyQt6.")}</p>
<p>{self.tr("Capture, annotate and share screenshots with rectangles, arrows, text, numbering, blur, watermark, OCR, pin windows and upload.")}</p>
<p><b>{self.tr("Technologies")}:</b><br>{self.tr("Python 3, PyQt6 (Qt 6 Widgets), PaddleOCR (optional OCR backend)")}</p>
<table cellspacing="4">{table}</table>
"""
