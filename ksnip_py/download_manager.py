from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

from PyQt6.QtCore import QObject, QSettings, QThread, QTimer, Qt, pyqtSignal
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
    ):
        self.id = id
        self.name = name
        self.description = description
        self.size_mb = size_mb
        self.check_installed = check_installed
        self.install_action = install_action
        self.category = category


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
    ):
        super().__init__()
        self._model = model

    def run(self) -> None:
        try:
            def progress(p: int) -> None:
                self.progress.emit(p)

            def status(s: str) -> None:
                self.status.emit(s)

            success = self._model.install_action(progress, status)
            self.finished.emit(success, self._model.id)
        except Exception as e:
            self.status.emit(f"Error: {e}")
            self.finished.emit(False, str(e))


class ModelCard(QWidget):
    """UI card for a single model."""

    def __init__(self, model: ModelInfo, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._model = model
        self._worker: Optional[DownloadWorker] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        self.setStyleSheet("""
            ModelCard {
                background: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            ModelCard:hover {
                border: 1px solid #b0b0b0;
            }
        """)

        # Header with name and category
        header_layout = QHBoxLayout()
        self.name_label = QLabel(self._model.name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #222;")
        header_layout.addWidget(self.name_label)

        self.category_label = QLabel(self._model.category)
        self.category_label.setStyleSheet(
            "color: #555; font-size: 11px; background: #eef2f7; padding: 3px 8px; border-radius: 4px; font-weight: 500;"
        )
        header_layout.addWidget(self.category_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Description
        self.desc_label = QLabel(self._model.description)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #555; font-size: 12px; line-height: 1.4;")
        layout.addWidget(self.desc_label)

        # Size info
        if self._model.size_mb > 0:
            size_text = self.tr("Download size: ~%1 MB").replace("%1", str(self._model.size_mb))
        else:
            size_text = self.tr("No download required")
        self.size_label = QLabel(size_text)
        self.size_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.size_label)

        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
                height: 18px;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel(self.tr("Checking status..."))
        self.status_label.setStyleSheet("color: #888; font-size: 11px; font-style: italic;")
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.install_btn = QPushButton(self.tr("Install"))
        self.install_btn.setFixedWidth(110)
        self.install_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #93c5fd;
            }
        """)
        self.install_btn.clicked.connect(self._on_install_clicked)
        button_layout.addWidget(self.install_btn)

        self.remove_btn = QPushButton(self.tr("Remove"))
        self.remove_btn.setFixedWidth(90)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        self.remove_btn.setVisible(False)
        button_layout.addWidget(self.remove_btn)

        layout.addLayout(button_layout)

    def set_installed_status(self, installed: bool) -> None:
        """Called asynchronously when background check completes."""
        if installed:
            self.install_btn.setText(self.tr("Reinstall"))
            self.remove_btn.setVisible(True)
            self.status_label.setText(self.tr("✓ Installed"))
            self.status_label.setStyleSheet("color: #16a34a; font-size: 11px; font-weight: bold;")
        else:
            self.install_btn.setText(self.tr("Install"))
            self.remove_btn.setVisible(False)
            self.status_label.setText(self.tr("Not installed"))
            self.status_label.setStyleSheet("color: #888; font-size: 11px;")

    def _on_install_clicked(self) -> None:
        if self._worker and self._worker.isRunning():
            return

        self.install_btn.setEnabled(False)
        self.remove_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText(self.tr("Starting download..."))
        self.status_label.setStyleSheet("color: #2563eb; font-size: 11px;")

        self._worker = DownloadWorker(self._model)
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

    def _on_finished(self, success: bool, model_id: str) -> None:
        self.install_btn.setEnabled(True)
        self.remove_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.status_label.setText(self.tr("✓ Installed successfully"))
            self.status_label.setStyleSheet("color: #16a34a; font-size: 11px; font-weight: bold;")
            self.install_btn.setText(self.tr("Reinstall"))
            self.remove_btn.setVisible(True)
        else:
            self.status_label.setText(self.tr("✗ Installation failed"))
            self.status_label.setStyleSheet("color: #dc2626; font-size: 11px; font-weight: bold;")


class DownloadManagerDialog(QDialog):
    """Dialog for managing downloadable models and components."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Model & Component Manager"))
        self.resize(720, 580)
        self._models: list[ModelInfo] = []
        self._cards: dict[str, ModelCard] = {}
        self._checker_worker: Optional[CheckModelsWorker] = None
        self._setup_ui()
        self._load_models()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet("background: #f8fafc; border-bottom: 1px solid #e2e8f0;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 18, 20, 18)

        title_layout = QHBoxLayout()
        title = QLabel(self.tr("Model & Component Manager"))
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e293b;")
        title_layout.addWidget(title)

        self.global_progress = QProgressBar()
        self.global_progress.setRange(0, 0)  # Indeterminate loading bar
        self.global_progress.setFixedWidth(120)
        self.global_progress.setFixedHeight(14)
        self.global_progress.setTextVisible(False)
        self.global_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cbd5e1;
                border-radius: 3px;
                background: #f1f5f9;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
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
        subtitle.setStyleSheet("color: #64748b; font-size: 12px; margin-top: 4px;")
        header_layout.addWidget(subtitle)

        layout.addWidget(header)

        # Scroll area for model cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background: #f1f5f9;")

        self.models_container = QWidget()
        self.models_container.setStyleSheet("background: #f1f5f9;")
        self.models_layout = QVBoxLayout(self.models_container)
        self.models_layout.setContentsMargins(20, 16, 20, 16)
        self.models_layout.setSpacing(12)
        self.models_layout.addStretch()

        scroll.setWidget(self.models_container)
        layout.addWidget(scroll, 1)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.accept)
        button_box.setStyleSheet("padding: 14px 20px; background: #ffffff; border-top: 1px solid #e2e8f0;")
        layout.addWidget(button_box)

    def _load_models(self) -> None:
        # Clear existing
        for card in self._cards.values():
            card.deleteLater()
        self._cards.clear()

        self._models = self._get_available_models()

        for model in self._models:
            card = ModelCard(model)
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
        ))

        # PaddleOCR Structure (tables + layout)
        models.append(ModelInfo(
            id="paddleocr-structure",
            name=self.tr("PaddleOCR Structure (PP-StructureV3)"),
            description=self.tr(
                "Document layout analysis and table recognition. "
                "Converts tables to Markdown/HTML."
            ),
            size_mb=300,
            check_installed=self._check_paddleocr_structure,
            install_action=self._install_paddleocr_structure,
            category=self.tr("OCR"),
        ))

        # PaddleOCR Formula recognition
        models.append(ModelInfo(
            id="paddleocr-formula",
            name=self.tr("PaddleOCR Formula Recognition"),
            description=self.tr(
                "Mathematical formula recognition (LaTeX output). "
                "Optional extra for structure pipeline."
            ),
            size_mb=50,
            check_installed=self._check_paddleocr_formula,
            install_action=self._install_paddleocr_formula,
            category=self.tr("OCR"),
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
        ))

        # Spellcheck dictionaries
        models.append(ModelInfo(
            id="spellcheck-dicts",
            name=self.tr("Spellcheck Dictionaries (Hunspell)"),
            description=self.tr(
                "Additional language dictionaries for spell checking "
                "in text annotations."
            ),
            size_mb=50,
            check_installed=self._check_spellcheck_dicts,
            install_action=self._install_spellcheck_dicts,
            category=self.tr("Spellcheck"),
        ))

        return models

    # ── Fast check & install helpers ──

    @staticmethod
    def _is_package_installed(pkg_name: str) -> bool:
        return importlib.util.find_spec(pkg_name) is not None

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
        script_path = settings.value("ocr/external_script_path", "")
        return bool(script_path and Path(script_path).exists())

    def _check_spellcheck_dicts(self) -> bool:
        dict_dir = Path("/usr/share/hunspell")
        return dict_dir.exists() and any(dict_dir.glob("*.dic"))

    def _install_paddleocr_line(
        self,
        progress: Callable[[int], None],
        status: Callable[[str], None],
    ) -> bool:
        try:
            status(self.tr("Downloading & installing packages (pip)..."))
            progress(15)

            process = subprocess.Popen(
                [
                    sys.executable, "-m", "pip", "install",
                    "paddlepaddle==3.3.1",
                    "paddleocr==3.7.0",
                    "protobuf==3.20.2",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            if process.stdout:
                for line in process.stdout:
                    if "Downloading" in line:
                        status(self.tr("Downloading: %1").replace("%1", line.strip()[:60]))
                        progress(40)

            process.wait()
            if process.returncode != 0:
                return False

            progress(85)
            status(self.tr("Initializing model cache..."))

            from paddleocr import PaddleOCR
            _ = PaddleOCR(
                lang="en",
                enable_mkldnn=False,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )

            progress(100)
            status(self.tr("Installation complete!"))
            return True
        except Exception as e:
            status(f"Error: {e}")
            return False

    def _install_paddleocr_structure(
        self,
        progress: Callable[[int], None],
        status: Callable[[str], None],
    ) -> bool:
        try:
            status(self.tr("Installing PaddleX with OCR extra..."))
            progress(15)

            subprocess.run(
                [
                    sys.executable, "-m", "pip", "install",
                    "paddlepaddle==3.3.1",
                    "paddleocr==3.7.0",
                    "protobuf==3.20.2",
                    "paddlex[ocr]==3.7.2",
                    "markdownify",
                ],
                check=True,
            )

            progress(75)
            status(self.tr("Initializing layout model..."))

            from paddleocr import PPStructureV3
            _ = PPStructureV3(
                lang="en",
                enable_mkldnn=False,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                use_table_recognition=True,
            )

            progress(100)
            status(self.tr("Installation complete!"))
            return True
        except Exception as e:
            status(f"Error: {e}")
            return False

    def _install_paddleocr_formula(
        self,
        progress: Callable[[int], None],
        status: Callable[[str], None],
    ) -> bool:
        return self._install_paddleocr_structure(progress, status)

    def _install_external_script(
        self,
        progress: Callable[[int], None],
        status: Callable[[str], None],
    ) -> bool:
        status(self.tr("Configure script path in Settings → OCR"))
        progress(100)
        return True

    def _install_spellcheck_dicts(
        self,
        progress: Callable[[int], None],
        status: Callable[[str], None],
    ) -> bool:
        status(self.tr("Install hunspell packages with apt/dnf"))
        progress(100)
        return True


def show_download_manager(parent: Optional[QWidget] = None) -> None:
    """Show the model download manager dialog."""
    dialog = DownloadManagerDialog(parent)
    dialog.exec()