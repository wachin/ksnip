from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from PyQt6.QtCore import QSettings, QSize, QStandardPaths, Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon, QImage, QImageReader
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStyle,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


SUPPORTED_STICKER_SUFFIXES = {".svg", ".png", ".xpm"}


@dataclass(frozen=True)
class StickerCollection:
    name: str
    directory: Path


def sticker_collections(package_dir: Path | None = None) -> tuple[StickerCollection, ...]:
    bundled = package_dir or Path(__file__).resolve().parent / "stickers"
    return (
        StickerCollection("Original", bundled),
        StickerCollection("Papirus", bundled / "themes" / "papirus"),
        StickerCollection("GNOME", bundled / "themes" / "gnome"),
        StickerCollection("Numix", bundled / "themes" / "numix"),
        StickerCollection("SuperTux", bundled / "themes" / "supertux"),
        StickerCollection("TuxBaby", bundled / "themes" / "tuxbaby"),
        StickerCollection("User", user_sticker_directory()),
    )


def discover_stickers(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and not path.is_symlink() and path.suffix.lower() in SUPPORTED_STICKER_SUFFIXES
    )


def user_sticker_directory() -> Path:
    config_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    return Path(config_path) / "stickers" / "user"


def import_user_sticker(source: Path, destination: Path, maximum_size: int = 512) -> Path | None:
    reader = QImageReader(str(source))
    reader.setAutoTransform(True)
    source_size = reader.size()
    if source_size.isValid() and max(source_size.width(), source_size.height()) > maximum_size:
        source_size.scale(QSize(maximum_size, maximum_size), Qt.AspectRatioMode.KeepAspectRatio)
        reader.setScaledSize(source_size)
    image = reader.read()
    if image.isNull():
        return None
    if max(image.width(), image.height()) > maximum_size:
        image = image.scaled(
            maximum_size,
            maximum_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    image = image.convertToFormat(QImage.Format.Format_ARGB32)
    destination.mkdir(parents=True, exist_ok=True)
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", source.stem).strip("._-") or "sticker"
    target = destination / f"{safe_stem}.png"
    suffix = 2
    while target.exists():
        target = destination / f"{safe_stem}_{suffix}.png"
        suffix += 1
    return target if image.save(str(target), "PNG") else None


class StickerPickerDialog(QDialog):
    FAVORITES_KEY = "editor/favorite_stickers"
    LAST_TAB_KEY = "editor/sticker_picker_last_tab"

    def __init__(
        self,
        parent=None,
        *,
        settings: QSettings | None = None,
        current_path: str | None = None,
        collections: tuple[StickerCollection, ...] | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings or QSettings()
        self._collections = collections or sticker_collections()
        self._current_path = current_path
        self._selected_path: str | None = None
        self._favorites = self._load_favorites()
        self.setWindowTitle(self.tr("Select Sticker"))
        self.resize(720, 560)

        self._favorites_box = QGroupBox(self.tr("Pinned Stickers"), self)
        self._favorites_layout = QHBoxLayout(self._favorites_box)
        self._favorites_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.tabs = QTabWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self._favorites_box)
        layout.addWidget(self.tabs, 1)
        self._rebuild()
        self.tabs.currentChanged.connect(self._remember_current_tab)

    def selected_path(self) -> str | None:
        return self._selected_path

    def favorite_paths(self) -> list[str]:
        return list(self._favorites)

    def _load_favorites(self) -> list[str]:
        value = self._settings.value(self.FAVORITES_KEY, [])
        candidates = [value] if isinstance(value, str) else list(value or [])
        return [
            str(path)
            for candidate in candidates
            if (path := Path(str(candidate))).is_file() and not path.is_symlink()
        ]

    def _save_favorites(self) -> None:
        self._settings.setValue(self.FAVORITES_KEY, self._favorites)
        self._settings.sync()

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _rebuild(self) -> None:
        self._clear_layout(self._favorites_layout)
        if self._favorites:
            for path in self._favorites:
                self._favorites_layout.addWidget(self._favorite_card(Path(path)))
        else:
            self._favorites_layout.addWidget(QLabel(self.tr("Use the star button to pin frequently used stickers."), self))

        current_name = (
            self.tabs.tabBar().tabData(self.tabs.currentIndex())
            if self.tabs.currentIndex() >= 0
            else str(self._settings.value(self.LAST_TAB_KEY, "Original"))
        )
        self.tabs.blockSignals(True)
        self.tabs.clear()
        for collection in self._collections:
            title = self.tr("User") if collection.name == "User" else collection.name
            index = self.tabs.addTab(self._collection_page(collection), title)
            self.tabs.tabBar().setTabData(index, collection.name)
        matching_index = next(
            (index for index in range(self.tabs.count()) if self.tabs.tabBar().tabData(index) == current_name),
            0,
        )
        self.tabs.setCurrentIndex(matching_index)
        self.tabs.blockSignals(False)

    def _remember_current_tab(self, index: int) -> None:
        if index < 0:
            return
        self._settings.setValue(self.LAST_TAB_KEY, self.tabs.tabBar().tabData(index))
        self._settings.sync()

    def _collection_page(self, collection: StickerCollection) -> QWidget:
        stickers = discover_stickers(collection.directory)
        page = QWidget(self.tabs)
        layout = QVBoxLayout(page)
        if collection.name == "User":
            controls = QHBoxLayout()
            add_button = QPushButton(self.tr("Add Images..."), page)
            add_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
            add_button.clicked.connect(lambda checked=False, directory=collection.directory: self._add_user_images(directory))
            open_button = QPushButton(self.tr("Open Here with File Manager"), page)
            open_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
            open_button.clicked.connect(lambda checked=False, directory=collection.directory: self._open_user_directory(directory))
            controls.addWidget(add_button)
            controls.addWidget(open_button)
            controls.addStretch(1)
            layout.addLayout(controls)
        if not stickers:
            if collection.name == "User":
                message = self.tr("Add your own images to use them as stickers.")
            else:
                message = self.tr("Sticker theme is not installed: %1").replace("%1", str(collection.directory))
            label = QLabel(message, page)
            label.setWordWrap(True)
            layout.addWidget(label)
            layout.addStretch(1)
            return page

        content = QWidget(page)
        grid = QGridLayout(content)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        for index, path in enumerate(stickers):
            grid.addWidget(self._sticker_card(path), index // 7, index % 7)
        scroll = QScrollArea(page)
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return page

    def _add_user_images(self, directory: Path) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            self.tr("Add Sticker Images"),
            str(Path.home()),
            self.tr("Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.svg *.xpm);;All Files (*)"),
        )
        if not paths:
            return
        failures = [path for path in paths if import_user_sticker(Path(path), directory) is None]
        if failures:
            QMessageBox.warning(
                self,
                self.tr("Unable to Add Images"),
                self.tr("Some files could not be imported as stickers."),
            )
        self._rebuild()

    def _open_user_directory(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory)))

    def _favorite_card(self, path: Path) -> QWidget:
        card = QWidget(self)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)
        layout.addWidget(self._sticker_button(path, compact=True))
        unpin = QToolButton(card)
        unpin.setText("★")
        unpin.setToolTip(self.tr("Unpin Sticker"))
        unpin.clicked.connect(lambda checked=False, sticker_path=str(path): self._toggle_favorite(sticker_path, False))
        layout.addWidget(unpin, alignment=Qt.AlignmentFlag.AlignCenter)
        return card

    def _sticker_card(self, path: Path) -> QWidget:
        card = QWidget(self)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        layout.addWidget(self._sticker_button(path))
        pin = QToolButton(card)
        pin.setCheckable(True)
        pin.setChecked(str(path) in self._favorites)
        pin.setText("★" if pin.isChecked() else "☆")
        pin.setToolTip(self.tr("Unpin Sticker") if pin.isChecked() else self.tr("Pin Sticker"))
        pin.toggled.connect(lambda checked, sticker_path=str(path): self._toggle_favorite(sticker_path, checked))
        layout.addWidget(pin, alignment=Qt.AlignmentFlag.AlignCenter)
        return card

    def _sticker_button(self, path: Path, *, compact: bool = False) -> QToolButton:
        button = QToolButton(self)
        button.setIcon(QIcon(str(path)))
        button.setIconSize(QSize(44, 44) if compact else QSize(56, 56))
        if compact:
            button.setFixedSize(52, 52)
        else:
            button.setFixedSize(72, 68)
        button.setToolTip(path.stem.replace("_", " ").replace("-", " "))
        button.setCheckable(bool(self._current_path))
        button.setChecked(str(path) == self._current_path)
        button.clicked.connect(lambda checked=False, sticker_path=str(path): self._select(sticker_path))
        return button

    def _select(self, path: str) -> None:
        self._selected_path = path
        self.accept()

    def _toggle_favorite(self, path: str, checked: bool) -> None:
        if checked and path not in self._favorites:
            self._favorites.append(path)
        elif not checked and path in self._favorites:
            self._favorites.remove(path)
        self._save_favorites()
        self._rebuild()
