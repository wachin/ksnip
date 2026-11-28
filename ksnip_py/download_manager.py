from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import traceback
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from PyQt6.QtCore import (
    QObject,
    QSettings,
    QStandardPaths,
    QThread,
    QTimer,
    Qt,
    QUrl,
    pyqtSignal,
)
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


def _is_frozen_build() -> bool:
    """Return whether this code is running from a frozen application."""

    return bool(getattr(sys, "frozen", False)) or "__compiled__" in globals()


def _model_manager_log_path() -> Path:
    """Return the log file that records every Model Manager installation.

    The download manager runs long, network-bound steps in a worker thread and
    the dialog only has room for one line of text, so the full pip output and
    every traceback are appended here.  That log is the only way to see why an
    installation failed, especially on Windows where the GUI has no console.
    """

    base = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.GenericDataLocation
    )
    candidates = [Path(base) / "ksnip-pyqt6" / "logs"] if base else []
    candidates.append(Path.home() / ".local" / "share" / "ksnip-pyqt6" / "logs")
    for directory in candidates:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError:
            continue
        return directory / "model-manager.log"
    return Path(tempfile.gettempdir()) / "ksnip-pyqt6-model-manager.log"


def _append_log(log_path: Optional[Path], text: str) -> None:
    """Append ``text`` to the installation log, ignoring a broken log path."""

    if log_path is None:
        return
    try:
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(text)
    except OSError:
        pass


def open_in_file_manager(path: Optional[Path]) -> bool:
    """Open *path* in the desktop file manager (Explorer, Nautilus, Finder).

    Returns whether a request was issued. A missing directory is not an error the
    caller has to guess about: it simply returns ``False``.
    """

    if path is None:
        return False
    try:
        resolved = Path(path).expanduser()
        if not resolved.is_dir():
            return False
        return bool(QDesktopServices.openUrl(QUrl.fromLocalFile(str(resolved))))
    except OSError:
        return False


class ModelInfo:
    """Information about a downloadable model/component."""

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        size_mb: int,
        check_installed: Callable[[], bool],
        install_action: Callable[[Callable[[int], None], Callable[[str], None]], bool],
        category: str = "OCR",
        folder: Optional[Callable[[], Optional[Path]]] = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.size_mb = size_mb
        self.check_installed = check_installed
        self.install_action = install_action
        self.category = category
        # Where the model files live, so the card can open that folder. Resolved
        # on every call because the folder may appear after an installation.
        self.folder = folder


class CheckModelsWorker(QThread):
    """Background worker to check model installation status without blocking UI."""

    model_checked = pyqtSignal(str, bool)  # (model_id, is_installed)
    all_finished = pyqtSignal()

    def __init__(self, models: list[ModelInfo]):
        super().__init__()
        self._models = models

    def run(self) -> None:
        for model in self._models:
            try:
                installed = model.check_installed()
            except Exception:
                installed = False
            self.model_checked.emit(model.id, installed)
        self.all_finished.emit()


class DownloadWorker(QThread):
    """Worker thread for downloading/installing models."""

    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(
        self,
        model: ModelInfo,
        errors: Optional[dict[str, str]] = None,
    ):
        super().__init__()
        self._model = model
        self._errors = errors if errors is not None else {}

    def run(self) -> None:
        try:
            def progress(p: int) -> None:
                self.progress.emit(p)

            def status(s: str) -> None:
                self.status.emit(s)

            success = self._model.install_action(progress, status)
            self.finished.emit(success, self._model.id)
        except Exception as e:
            self._errors[self._model.id] = f"{type(e).__name__}: {e}"
            self.status.emit(f"Error: {e}")
            self.finished.emit(False, self._model.id)


class ModelCard(QWidget):
    """UI card for a single model."""

    def __init__(
        self,
        model: ModelInfo,
        errors: Optional[dict[str, str]] = None,
        log_path: Optional[Path] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._model = model
        self._worker: Optional[DownloadWorker] = None
        self._errors = errors if errors is not None else {}
        self._log_path = log_path
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        self.setStyleSheet("""
            ModelCard {
                background: palette(base);
                border: 1px solid palette(mid);
                border-radius: 8px;
            }
            ModelCard:hover {
                border: 1px solid palette(highlight);
            }
        """)

        # Header with name and category
        header_layout = QHBoxLayout()
        self.name_label = QLabel(self._model.name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: palette(text);")
        header_layout.addWidget(self.name_label)

        self.category_label = QLabel(self._model.category)
        self.category_label.setStyleSheet(
            "color: palette(text); font-size: 11px; background: palette(alternate-base); "
            "padding: 3px 8px; border-radius: 4px; font-weight: 500;"
        )
        header_layout.addWidget(self.category_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Description
        self.desc_label = QLabel(self._model.description)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: palette(text); font-size: 12px; line-height: 1.4;")
        layout.addWidget(self.desc_label)

        # Size info
        if self._model.size_mb > 0:
            size_text = self.tr("Download size: ~%1 MB").replace("%1", str(self._model.size_mb))
        else:
            size_text = self.tr("No download required")
        self.size_label = QLabel(size_text)
        self.size_label.setStyleSheet("color: palette(mid); font-size: 11px;")
        layout.addWidget(self.size_label)

        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid palette(mid);
                border-radius: 4px;
                text-align: center;
                height: 18px;
            }
            QProgressBar::chunk {
                background-color: palette(highlight);
                border-radius: 3px;
            }
        """)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel(self.tr("Checking status..."))
        self.status_label.setStyleSheet("color: palette(mid); font-size: 11px; font-style: italic;")
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.install_btn = QPushButton(self.tr("Install"))
        self.install_btn.setFixedWidth(110)
        self.install_btn.setStyleSheet("""
            QPushButton {
                background-color: palette(highlight);
                color: palette(highlighted-text);
                font-weight: bold;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: palette(dark);
            }
            QPushButton:disabled {
                background-color: palette(mid);
            }
        """)
        self.install_btn.clicked.connect(self._on_install_clicked)
        if _is_frozen_build() and self._model.id != "external-ocr-script":
            self.install_btn.setEnabled(False)
            self.install_btn.setToolTip(
                self.tr(
                    "Not available in a packaged build. Use a source checkout or an "
                    "external OCR script."
                )
            )
        button_layout.addWidget(self.install_btn)

        self.remove_btn = QPushButton(self.tr("Remove"))
        self.remove_btn.setFixedWidth(90)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: palette(button);
                color: palette(button-text);
                border: 1px solid palette(mid);
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: palette(mid);
            }
        """)
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        self.remove_btn.setVisible(False)
        button_layout.addWidget(self.remove_btn)

        self.folder_btn = QPushButton(self.tr("Open folder"))
        self.folder_btn.setFixedWidth(120)
        self.folder_btn.setStyleSheet("""
            QPushButton {
                background-color: palette(button);
                color: palette(button-text);
                border: 1px solid palette(mid);
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: palette(mid);
            }
            QPushButton:disabled {
                color: palette(mid);
            }
        """)
        self.folder_btn.setToolTip(
            self.tr("Show the model files in the file manager.")
        )
        self.folder_btn.clicked.connect(self._on_open_folder_clicked)
        self.folder_btn.setVisible(False)
        button_layout.addWidget(self.folder_btn)

        self.log_btn = QPushButton(self.tr("Show log"))
        self.log_btn.setFixedWidth(110)
        self.log_btn.setStyleSheet("""
            QPushButton {
                background-color: palette(button);
                color: palette(button-text);
                border: 1px solid palette(mid);
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: palette(mid);
            }
        """)
        self.log_btn.setToolTip(
            self.tr("Open the installation log with the full pip and Paddle output.")
        )
        self.log_btn.clicked.connect(self._on_show_log_clicked)
        self.log_btn.setVisible(False)
        button_layout.addWidget(self.log_btn)

        layout.addLayout(button_layout)

    def set_installed_status(self, installed: bool) -> None:
        """Called asynchronously when background check completes."""
        self.status_label.setToolTip("")
        self.log_btn.setVisible(False)
        self._sync_folder_button(installed)
        if installed:
            self.install_btn.setText(self.tr("Reinstall"))
            self.remove_btn.setVisible(True)
            self.status_label.setText(self.tr("✓ Installed"))
            self.status_label.setStyleSheet("color: palette(text); font-size: 11px; font-weight: bold;")
        else:
            self.install_btn.setText(self.tr("Install"))
            self.remove_btn.setVisible(False)
            self.status_label.setText(self.tr("Not installed"))
            self.status_label.setStyleSheet("color: palette(mid); font-size: 11px;")

    def _folder_path(self) -> Optional[Path]:
        """Resolve the model folder now; it may appear after an install."""

        if self._model.folder is None:
            return None
        try:
            return self._model.folder()
        except Exception:  # noqa: BLE001 - a broken path must not break the card
            return None

    def _sync_folder_button(self, installed: bool) -> None:
        """Show the folder button only when the model is installed."""

        path = self._folder_path() if installed else None
        visible = path is not None and path.is_dir()
        self.folder_btn.setVisible(visible)
        if not visible:
            return
        self.folder_btn.setToolTip(
            self.tr("Show the model files in the file manager: %1").replace(
                "%1", str(path)
            )
        )

    def _on_open_folder_clicked(self) -> None:
        path = self._folder_path()
        if open_in_file_manager(path):
            return
        QMessageBox.information(
            self,
            self.tr("Open model folder"),
            self.tr("The folder does not exist yet: %1").replace(
                "%1", str(path) if path is not None else ""
            ),
        )

    def _on_install_clicked(self) -> None:
        if self._worker and self._worker.isRunning():
            return

        self.install_btn.setEnabled(False)
        self.remove_btn.setEnabled(False)
        self.log_btn.setVisible(False)
        self.folder_btn.setVisible(False)
        self.status_label.setToolTip("")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText(self.tr("Starting download..."))
        self.status_label.setStyleSheet("color: palette(highlight); font-size: 11px;")

        self._worker = DownloadWorker(self._model, self._errors)
        self._worker.progress.connect(self.progress_bar.setValue)
        self._worker.status.connect(self.status_label.setText)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_remove_clicked(self) -> None:
        QMessageBox.information(
            self,
            self.tr("Remove Model"),
            self.tr(
                "To remove %1, you can clear its cached directory or uninstall its package via pip.\n\n"
                "Directory: %2"
            ).replace("%1", self._model.name).replace("%2", str(Path.home() / ".paddlex")),
        )

    def _on_show_log_clicked(self) -> None:
        if self._log_path is None:
            return
        if not self._log_path.exists():
            QMessageBox.information(
                self,
                self.tr("Installation log"),
                self.tr("The log file has not been created yet."),
            )
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._log_path)))

    def _on_finished(self, success: bool, model_id: str) -> None:
        self.install_btn.setEnabled(True)
        self.remove_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self._errors.pop(model_id, None)
            self.log_btn.setVisible(False)
            self.status_label.setToolTip("")
            self.status_label.setText(self.tr("✓ Installed successfully"))
            self.status_label.setStyleSheet("color: palette(text); font-size: 11px; font-weight: bold;")
            self.install_btn.setText(self.tr("Reinstall"))
            self.remove_btn.setVisible(True)
            self._sync_folder_button(True)
        else:
            self.folder_btn.setVisible(False)
            message = (self._errors.get(model_id) or "").strip()
            summary = message.splitlines()[0] if message else ""
            if len(summary) > 120:
                summary = summary[:117] + "…"
            self.status_label.setText(
                self.tr("✗ Installation failed")
                + (f": {summary}" if summary else "")
            )
            self.status_label.setStyleSheet("color: palette(text); font-size: 11px; font-weight: bold;")
            tooltip = message
            if self._log_path is not None:
                tooltip = (
                    f"{tooltip}\n\n{self.tr('Full log')}: {self._log_path}"
                    if tooltip
                    else f"{self.tr('Full log')}: {self._log_path}"
                )
                self.log_btn.setVisible(True)
            self.status_label.setToolTip(tooltip)


class DownloadManagerDialog(QDialog):
    """Dialog for managing downloadable models and components."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Model & Component Manager"))
        self.resize(720, 580)
        self._models: list[ModelInfo] = []
        self._cards: dict[str, ModelCard] = {}
        self._checker_worker: Optional[CheckModelsWorker] = None
        self._errors: dict[str, str] = {}
        self._log_path: Optional[Path] = _model_manager_log_path()
        self._setup_ui()
        self._load_models()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet("background: palette(window); border-bottom: 1px solid palette(mid);")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 18, 20, 18)

        title_layout = QHBoxLayout()
        title = QLabel(self.tr("Model & Component Manager"))
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: palette(text);")
        title_layout.addWidget(title)

        self.global_progress = QProgressBar()
        self.global_progress.setRange(0, 0)  # Indeterminate loading bar
        self.global_progress.setFixedWidth(120)
        self.global_progress.setFixedHeight(14)
        self.global_progress.setTextVisible(False)
        self.global_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid palette(mid);
                border-radius: 3px;
                background: palette(base);
            }
            QProgressBar::chunk {
                background-color: palette(highlight);
            }
        """)
        title_layout.addWidget(self.global_progress)
        title_layout.addStretch()

        header_layout.addLayout(title_layout)

        subtitle = QLabel(
            self.tr(
                "Download additional components for OCR and other features. "
                "Models are stored in your user directory and are not bundled with the application."
            )
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: palette(mid); font-size: 12px; margin-top: 4px;")
        header_layout.addWidget(subtitle)

        if _is_frozen_build():
            notice = QLabel(
                self.tr(
                    "This is a packaged build. Installing Python packages (PaddleOCR, "
                    "PaddlePaddle, PaddleX) is disabled because no Python interpreter is "
                    "shipped with it. Use a source checkout, or configure an external OCR "
                    "script under Settings → OCR."
                )
            )
            notice.setWordWrap(True)
            notice.setStyleSheet(
                "background: palette(alternate-base); color: palette(text); "
                "border: 1px solid palette(mid); border-radius: 6px; padding: 8px 10px; "
                "font-size: 12px; margin-top: 8px;"
            )
            header_layout.addWidget(notice)

        layout.addWidget(header)

        # Scroll area for model cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background: palette(window);")

        self.models_container = QWidget()
        self.models_container.setStyleSheet("background: palette(window);")
        self.models_layout = QVBoxLayout(self.models_container)
        self.models_layout.setContentsMargins(20, 16, 20, 16)
        self.models_layout.setSpacing(12)
        self.models_layout.addStretch()

        scroll.setWidget(self.models_container)
        layout.addWidget(scroll, 1)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.accept)
        button_box.setStyleSheet("padding: 14px 20px; background: palette(window); border-top: 1px solid palette(mid);")
        layout.addWidget(button_box)

    def _load_models(self) -> None:
        # Clear existing
        for card in self._cards.values():
            card.deleteLater()
        self._cards.clear()

        self._models = self._get_available_models()

        for model in self._models:
            card = ModelCard(model, self._errors, self._log_path)
            self._cards[model.id] = card
            self.models_layout.insertWidget(self.models_layout.count() - 1, card)

        # Start background check worker so the GUI opens immediately!
        self.global_progress.setVisible(True)
        self._checker_worker = CheckModelsWorker(self._models)
        self._checker_worker.model_checked.connect(self._on_model_checked)
        self._checker_worker.all_finished.connect(self._on_checks_finished)
        self._checker_worker.start()

    def _on_model_checked(self, model_id: str, installed: bool) -> None:
        card = self._cards.get(model_id)
        if card:
            card.set_installed_status(installed)

    def _on_checks_finished(self) -> None:
        self.global_progress.setVisible(False)

    def _get_available_models(self) -> list[ModelInfo]:
        models = []

        # PaddleOCR line models
        models.append(ModelInfo(
            id="paddleocr-line",
            name=self.tr("PaddleOCR Line Models (PP-OCRv5)"),
            description=self.tr(
                "Lightweight OCR models for text line recognition. "
                "Supports English, Spanish, and 80+ languages."
            ),
            size_mb=150,
            check_installed=self._check_paddleocr_line,
            install_action=self._install_paddleocr_line,
            category=self.tr("OCR"),
            folder=self._paddle_models_directory,
        ))

        # PaddleOCR Structure (tables + layout)
        models.append(ModelInfo(
            id="paddleocr-structure",
            name=self.tr("PaddleOCR Structure (PP-StructureV3)"),
            description=self.tr(
                "Document layout analysis and table recognition. "
                "Converts tables to Markdown/HTML."
            ),
            size_mb=1800,
            check_installed=self._check_paddleocr_structure,
            install_action=self._install_paddleocr_structure,
            category=self.tr("OCR"),
            folder=self._paddle_models_directory,
        ))

        # PaddleOCR Formula recognition
        models.append(ModelInfo(
            id="paddleocr-formula",
            name=self.tr("PaddleOCR Formula Recognition"),
            description=self.tr(
                "Mathematical formula recognition (LaTeX output). "
                "Optional extra for structure pipeline."
            ),
            size_mb=700,
            check_installed=self._check_paddleocr_formula,
            install_action=self._install_paddleocr_formula,
            category=self.tr("OCR"),
            folder=self._paddle_models_directory,
        ))

        # External OCR script
        models.append(ModelInfo(
            id="external-ocr-script",
            name=self.tr("External OCR Script"),
            description=self.tr(
                "Use any custom OCR engine via a script/executable. "
                "The script receives the image path as its only argument and must "
                "print the recognized text to stdout. "
                "\n\n"
                "Example script (save as ~/ocr.sh):\n"
                "#!/bin/bash\n"
                "tesseract \"$1\" stdout -l spa+eng\n"
                "\n"
                "Make it executable: chmod +x ~/ocr.sh\n"
                "Then configure the path in Settings → OCR → External OCR script."
            ),
            size_mb=0,
            check_installed=self._check_external_script,
            install_action=self._install_external_script,
            category=self.tr("OCR"),
            folder=self._external_script_directory,
        ))

        return models

    # ── Fast check & install helpers ──

    @staticmethod
    def _is_package_installed(pkg_name: str) -> bool:
        return importlib.util.find_spec(pkg_name) is not None

    @staticmethod
    def _paddle_models_directory() -> Optional[Path]:
        """Return the folder that holds the Paddle models, if it exists.

        PaddleX keeps every downloaded model under ``~/.paddlex/official_models``;
        older PaddleOCR releases used ``~/.paddleocr``, which is only opened when
        the PaddleX cache is absent.
        """

        paddle_x = Path.home() / ".paddlex" / "official_models"
        if paddle_x.is_dir():
            return paddle_x
        legacy = Path.home() / ".paddleocr"
        if legacy.is_dir():
            return legacy
        return None

    @staticmethod
    def _external_script_directory() -> Optional[Path]:
        """Return the folder of the configured external OCR script."""

        settings = QSettings()
        script_path = str(settings.value("ocr/script_path", "") or "")
        if not script_path:
            return None
        path = Path(script_path).expanduser()
        return path.parent if path.exists() else None

    def _check_paddleocr_line(self) -> bool:
        if not self._is_package_installed("paddleocr"):
            return False
        # Fast filesystem check without instantiating model
        paddlex_dir = Path.home() / ".paddlex" / "official_models"
        ocr_dir = Path.home() / ".paddleocr"
        return (paddlex_dir.exists() and any(paddlex_dir.iterdir())) or (ocr_dir.exists() and any(ocr_dir.iterdir()))

    def _check_paddleocr_structure(self) -> bool:
        if not self._is_package_installed("paddlex"):
            return False
        paddlex_dir = Path.home() / ".paddlex" / "official_models"
        return paddlex_dir.exists() and any("DocLayout" in str(p) or "Table" in str(p) or "SLANet" in str(p) for p in paddlex_dir.iterdir())

    def _check_paddleocr_formula(self) -> bool:
        if not self._is_package_installed("paddlex"):
            return False
        paddlex_dir = Path.home() / ".paddlex" / "official_models"
        return paddlex_dir.exists() and any("Formula" in str(p) for p in paddlex_dir.iterdir())

    def _check_external_script(self) -> bool:
        settings = QSettings()
        script_path = settings.value("ocr/script_path", "")
        return bool(script_path and Path(script_path).exists())

    def _run_pip(
        self,
        args: list[str],
        status: Callable[[str], None],
        progress: Callable[[int], None],
        progress_after: int,
    ) -> tuple[bool, str]:
        """Run ``pip install`` and return ``(ok, tail_of_output)``.

        Unlike a bare ``subprocess.run(..., check=True)``, this keeps pip's
        output: the last lines are what explain a failure (missing wheel for the
        interpreter, network error, dependency conflict), and they are also
        appended to the installation log.
        """

        command = [sys.executable, "-m", "pip", "install", *args]
        _append_log(
            self._log_path,
            f"\n=== {datetime.now().isoformat(timespec='seconds')} pip install "
            f"{' '.join(args)} ===\n",
        )

        tail: deque[str] = deque(maxlen=60)
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError as exc:
            return False, f"{type(exc).__name__}: {exc}"

        handle = None
        if self._log_path is not None:
            try:
                handle = self._log_path.open("a", encoding="utf-8")
            except OSError:
                handle = None

        try:
            if process.stdout is not None:
                for line in process.stdout:
                    if handle is not None:
                        try:
                            handle.write(line)
                        except OSError:
                            pass
                    tail.append(line.rstrip())
                    stripped = line.strip()
                    if stripped.startswith("Downloading "):
                        progress(progress_after)
                        status(
                            self.tr("Downloading: %1").replace("%1", stripped[:60])
                        )
                    elif stripped.startswith("Installing collected packages"):
                        status(self.tr("Installing packages..."))
            return process.wait() == 0, "\n".join(tail)
        finally:
            if handle is not None:
                handle.close()

    def _fail(
        self,
        model_id: str,
        status: Callable[[str], None],
        summary: str,
        detail: str = "",
    ) -> bool:
        """Record a readable failure reason and keep the details in the log."""

        summary = summary.strip() or self.tr("Unknown error")
        self._errors[model_id] = summary
        _append_log(
            self._log_path,
            f"\n=== {datetime.now().isoformat(timespec='seconds')} "
            f"{model_id} FAILED ===\n{summary}\n{detail}\n",
        )
        status(f"{self.tr('Installation failed')}: {summary}")
        return False

    def _install_paddleocr_line(
        self,
        progress: Callable[[int], None],
        status: Callable[[str], None],
    ) -> bool:
        model_id = "paddleocr-line"
        self._errors.pop(model_id, None)
        status(self.tr("Downloading & installing packages (pip)..."))
        progress(15)

        ok, tail = self._run_pip(
            ["paddlepaddle==3.3.1", "paddleocr==3.7.0", "protobuf==3.20.2"],
            status,
            progress,
            40,
        )
        if not ok:
            return self._fail(
                model_id,
                status,
                self.tr("pip could not install the PaddleOCR packages"),
                tail,
            )

        progress(70)
        status(self.tr("Downloading the recognition models (~150 MB)..."))
        try:
            from paddleocr import PaddleOCR

            _ = PaddleOCR(
                lang="en",
                enable_mkldnn=False,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
        except Exception as exc:  # noqa: BLE001
            return self._fail(
                model_id,
                status,
                f"{type(exc).__name__}: {exc}",
                traceback.format_exc(),
            )

        progress(100)
        status(self.tr("Installation complete!"))
        return True

    @staticmethod
    def _structure_kwargs(with_formula: bool) -> dict:
        """Return the PP-StructureV3 arguments used by both install and OCR.

        Keeping these identical to ``OcrBackend._recognize_with_pp_structure``
        means the installer downloads exactly the models the OCR action later
        loads, instead of caching a second, larger set.
        """

        return {
            "lang": "en",
            "enable_mkldnn": False,
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_textline_orientation": False,
            "use_table_recognition": True,
            "use_formula_recognition": with_formula,
            "layout_detection_model_name": "PP-DocLayout_plus-L",
            "text_detection_model_name": "PP-OCRv5_mobile_det",
            "text_recognition_model_name": "PP-OCRv5_mobile_rec",
            "wired_table_structure_recognition_model_name": "SLANeXt_wired",
            "wireless_table_structure_recognition_model_name": "SLANet_plus",
            "wired_table_cells_detection_model_name": "RT-DETR-L_wired_table_cell_det",
            "wireless_table_cells_detection_model_name": "RT-DETR-L_wireless_table_cell_det",
        }

    def _install_paddle_structure(
        self,
        model_id: str,
        progress: Callable[[int], None],
        status: Callable[[str], None],
        with_formula: bool,
        download_mb: int,
    ) -> bool:
        self._errors.pop(model_id, None)
        status(self.tr("Installing PaddleX with OCR extra..."))
        progress(10)

        ok, tail = self._run_pip(
            [
                "paddlepaddle==3.3.1",
                "paddleocr==3.7.0",
                "protobuf==3.20.2",
                "paddlex[ocr]==3.7.2",
                "markdownify",
            ],
            status,
            progress,
            40,
        )
        if not ok:
            return self._fail(
                model_id,
                status,
                self.tr("pip could not install the PaddleOCR packages"),
                tail,
            )

        progress(60)
        status(
            self.tr(
                "Downloading layout and table models (~%1 MB, one time). "
                "This can take a long time; the progress bar will not move until it ends."
            ).replace("%1", str(download_mb))
        )

        try:
            from paddleocr import PPStructureV3

            _ = PPStructureV3(**self._structure_kwargs(with_formula))
        except Exception as exc:  # noqa: BLE001
            return self._fail(
                model_id,
                status,
                f"{type(exc).__name__}: {exc}",
                traceback.format_exc(),
            )

        progress(100)
        status(self.tr("Installation complete!"))
        return True

    def _install_paddleocr_structure(
        self,
        progress: Callable[[int], None],
        status: Callable[[str], None],
    ) -> bool:
        return self._install_paddle_structure(
            "paddleocr-structure", progress, status, with_formula=False, download_mb=1800
        )

    def _install_paddleocr_formula(
        self,
        progress: Callable[[int], None],
        status: Callable[[str], None],
    ) -> bool:
        return self._install_paddle_structure(
            "paddleocr-formula", progress, status, with_formula=True, download_mb=700
        )

    def _install_external_script(
        self,
        progress: Callable[[int], None],
        status: Callable[[str], None],
    ) -> bool:
        status(self.tr("Configure script path in Settings → OCR"))
        progress(100)
        return True


def show_download_manager(parent: Optional[QWidget] = None) -> None:
    """Show the model download manager dialog."""
    dialog = DownloadManagerDialog(parent)
    dialog.exec()