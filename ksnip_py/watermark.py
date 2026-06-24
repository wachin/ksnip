from __future__ import annotations

import random
from pathlib import Path

from PyQt6.QtCore import QStandardPaths, Qt
from PyQt6.QtGui import QImage, QPainter, QPixmap, QTransform


class WatermarkStore:
    def __init__(self) -> None:
        app_data_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        self._image_path = Path(app_data_path) / "watermark_image.png"

    def load(self) -> QPixmap:
        return QPixmap(str(self._image_path))

    def save_from_path(self, path: str) -> bool:
        image = QPixmap(path)
        if image.isNull():
            return False
        self._image_path.parent.mkdir(parents=True, exist_ok=True)
        return image.save(str(self._image_path))


class WatermarkPreparer:
    def __init__(self, opacity: float = 0.15) -> None:
        self._opacity = opacity

    def prepare(self, image: QPixmap, available_size, rotated: bool) -> QPixmap:
        prepared_image = self._prepared_watermark_image(image, rotated)
        return self._fit_into_capture(prepared_image, available_size)

    def _prepared_watermark_image(self, watermark_image: QPixmap, rotated: bool) -> QPixmap:
        prepared_image = self._rotated_image(watermark_image) if rotated else QPixmap(watermark_image)
        transparent_watermark = QPixmap(prepared_image.size())
        transparent_watermark.fill(Qt.GlobalColor.transparent)
        painter = QPainter(transparent_watermark)
        painter.setOpacity(self._opacity)
        painter.drawPixmap(0, 0, prepared_image)
        painter.end()
        return transparent_watermark

    def _rotated_image(self, watermark_image: QPixmap) -> QPixmap:
        transform = QTransform()
        transform.rotate(45)
        return watermark_image.transformed(transform, Qt.TransformationMode.SmoothTransformation)

    def _fit_into_capture(self, finished_watermark: QPixmap, available_size) -> QPixmap:
        if finished_watermark.isNull() or available_size.width() <= 0 or available_size.height() <= 0:
            return finished_watermark
        width_ratio = available_size.width() / finished_watermark.width()
        height_ratio = available_size.height() / finished_watermark.height()
        if width_ratio < 1 or height_ratio < 1:
            min_ratio = min(width_ratio, height_ratio)
            transform = QTransform()
            transform.scale(min_ratio, min_ratio)
            finished_watermark = finished_watermark.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        return finished_watermark


def random_watermark_position(image: QImage | QPixmap, available_size) -> tuple[int, int]:
    available_width = available_size.width() - image.width()
    available_height = available_size.height() - image.height()
    x = 0 if available_width <= 0 else random.randrange(available_width)
    y = 0 if available_height <= 0 else random.randrange(available_height)
    return x, y
