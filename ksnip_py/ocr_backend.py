from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QImage


class OcrError(Exception):
    pass


class OcrMissingDependencyError(OcrError):
    pass


class OcrCancelledError(OcrError):
    pass


@dataclass
class OcrOptions:
    backend: str
    language: str
    script_path: str = ""


class OcrBackend:
    def recognize_file(self, image_path: str, options: OcrOptions) -> str:
        if options.backend == "script":
            return self._recognize_with_script(image_path, options.script_path)
        if options.backend == "paddleocr":
            return self._recognize_with_paddleocr(image_path, options.language)
        raise OcrError(f"Unsupported OCR backend: {options.backend}")

    def _recognize_with_script(self, image_path: str, script_path: str) -> str:
        if not script_path:
            raise OcrError("No OCR script configured.")
        path = Path(script_path)
        if not path.exists():
            raise OcrError(f"OCR script does not exist: {script_path}")
        try:
            result = subprocess.run(
                [script_path, image_path],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise OcrError(f"Unable to start OCR script: {exc}") from exc
        if result.returncode != 0:
            raise OcrError(result.stderr.strip() or f"OCR script exited with code {result.returncode}.")
        text = result.stdout.strip()
        if not text:
            raise OcrError("OCR script finished but returned no text.")
        return text

    def _recognize_with_paddleocr(self, image_path: str, language: str) -> str:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise OcrMissingDependencyError(
                "PaddleOCR is not installed.\n\n"
                "In your virtual environment run:\n"
                "pip install paddlepaddle paddleocr"
            ) from exc

        if language == "spanish_english":
            raise OcrError(
                "PaddleOCR 3.7.0 in this port does not provide a working mixed Spanish+English setting. "
                "Use English or Spanish, or switch to the OCR script backend."
            )

        lang_map = {
            "english": "en",
            "spanish": "es",
        }
        try:
            ocr = PaddleOCR(lang=lang_map.get(language, "en"))
            result = ocr.predict(image_path)
        except Exception as exc:  # noqa: BLE001
            if "ConvertPirAttribute2RuntimeAttribute" in str(exc):
                raise OcrError(
                    "PaddleOCR started but PaddlePaddle failed at runtime with the installed backend. "
                    "This appears to be a PaddleOCR/PaddlePaddle runtime compatibility issue in the current environment. "
                    "Try the OCR script backend, or test a different PaddlePaddle/PaddleOCR combination in the virtual environment."
                ) from exc
            raise OcrError(f"PaddleOCR failed: {exc}") from exc

        lines = self._extract_paddleocr_text(result)
        if not lines:
            raise OcrError("PaddleOCR finished but returned no recognized text.")
        return "\n".join(lines).strip()

    def _extract_paddleocr_text(self, result) -> list[str]:
        lines: list[str] = []

        for item in result or []:
            rec_texts = getattr(item, "rec_texts", None)
            if rec_texts:
                lines.extend(text.strip() for text in rec_texts if str(text).strip())
                continue

            if isinstance(item, dict):
                texts = item.get("rec_texts")
                if texts:
                    lines.extend(str(text).strip() for text in texts if str(text).strip())
                    continue

            if isinstance(item, (list, tuple)):
                for sub_item in item:
                    if isinstance(sub_item, (list, tuple)) and len(sub_item) >= 2:
                        text_info = sub_item[1]
                        if isinstance(text_info, (list, tuple)) and text_info:
                            text = str(text_info[0]).strip()
                            if text:
                                lines.append(text)
        return lines


class OcrWorker(QObject):
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self, image: QImage, backend: OcrBackend, options: OcrOptions) -> None:
        super().__init__()
        self._image = image.copy()
        self._backend = backend
        self._options = options
        self._cancel_requested = False

    def cancel(self) -> None:
        self._cancel_requested = True

    def run(self) -> None:
        if self._cancel_requested:
            self.cancelled.emit()
            return

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
            temp_path = handle.name
        try:
            if not self._image.save(temp_path):
                self.failed.emit("Unable to save temporary image for OCR.")
                return
            if self._cancel_requested:
                self.cancelled.emit()
                return
            try:
                text = self._backend.recognize_file(temp_path, self._options)
            except OcrCancelledError:
                self.cancelled.emit()
                return
            except OcrError as exc:
                self.failed.emit(str(exc))
                return
            self.finished.emit(text)
        finally:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except OSError:
                pass
