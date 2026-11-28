"""Render contact sheets of the packaged action icons, one per theme.

Useful when adding or auditing icons: it shows every SVG at real toolbar size on
the background it is designed for, so a missing glyph, a wrong colour or an icon
that only exists in one theme is obvious.

Usage::

    python3 tools/render_icon_sheets.py [--output DIR] [--size 32]

Writes ``icons-light.png`` and ``icons-dark.png``. Uses only PyQt6, like the
application itself. Defaults to the system temporary directory, so it never
dirties the package.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QIcon, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication

ICON_DIRECTORY = Path(__file__).resolve().parent.parent / "ksnip_py" / "icons"
THEMES = (
    ("light", QColor("#f8fafc"), QColor("#5f6b7a")),
    ("dark", QColor("#353535"), QColor("#b8c0cc")),
)
COLUMNS = 4
CELL_WIDTH = 190
CELL_HEIGHT = 56


def _icon_image(icon: QIcon, size: int, background: QColor) -> QImage:
    image = QImage(size + 8, size + 8, QImage.Format.Format_ARGB32)
    image.fill(background)
    painter = QPainter(image)
    painter.drawPixmap(4, 4, icon.pixmap(QSize(size, size)))
    painter.end()
    return image


def _render_theme(theme: str, background: QColor, label: QColor, size: int) -> QImage:
    files = sorted((ICON_DIRECTORY / theme).glob("*.svg"))
    rows = max(1, (len(files) + COLUMNS - 1) // COLUMNS)
    sheet = QImage(
        CELL_WIDTH * COLUMNS,
        CELL_HEIGHT * rows,
        QImage.Format.Format_ARGB32,
    )
    sheet.fill(background)

    painter = QPainter(sheet)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    font = QFont(painter.font())
    font.setPointSizeF(8.5)
    painter.setFont(font)
    for index, path in enumerate(files):
        column, row = index % COLUMNS, index // COLUMNS
        left, top = column * CELL_WIDTH, row * CELL_HEIGHT
        icon = QIcon(str(path))
        painter.drawImage(left + 4, top + 4, _icon_image(icon, size, background))
        painter.setPen(label)
        painter.drawText(
            QRect(left + 4 + size + 14, top, CELL_WIDTH - size - 30, CELL_HEIGHT),
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            path.stem,
        )
        painter.setPen(QColor(label).lighter(150) if theme == "light" else QColor(label).darker(130))
        painter.drawRect(left, top, CELL_WIDTH - 1, CELL_HEIGHT - 1)
    painter.end()
    return sheet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=tempfile.gettempdir(),
        help="directory for the two PNG sheets (default: the temporary directory)",
    )
    parser.add_argument("--size", type=int, default=32, help="icon size in pixels")
    arguments = parser.parse_args()

    output = Path(arguments.output).expanduser()
    output.mkdir(parents=True, exist_ok=True)

    application = QApplication(sys.argv[:1])
    for theme, background, label in THEMES:
        sheet = _render_theme(theme, background, label, arguments.size)
        target = output / f"icons-{theme}.png"
        if not sheet.save(str(target), "PNG"):
            raise SystemExit(f"could not write {target}")
        print(f"written: {target}")
    del application
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
