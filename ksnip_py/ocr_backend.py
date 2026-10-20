from __future__ import annotations

import os
import signal
import subprocess
import tempfile
from collections.abc import Callable
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


# Languages shared by the line-oriented PaddleOCR pipeline and the layout
# pipeline (PP-StructureV3).  Both take PaddleOCR language codes.
_PADDLE_LANGUAGES = {
    "english": "en",
    "spanish": "es",
}

# PaddleOCR's layout pipeline requires PaddleX's `ocr` extra.  Its absence
# surfaces as a chained DependencyError that is rewritten into a generic
# RuntimeError, so both are probed when reporting the problem.
_PRIMARY_BACKEND = "paddleocr"
_STRUCTURE_BACKEND = "paddleocr_structure"
_SCRIPT_BACKEND = "script"


@dataclass
class OcrOptions:
    backend: str
    language: str
    script_path: str = ""
    # PP-StructureV3 only: also run the formula model so maths comes back as
    # LaTeX inside the Markdown.  It downloads an extra model, so it is off by
    # default.
    structure_formulas: bool = False


class OcrBackend:
    def recognize_file(
        self,
        image_path: str,
        options: OcrOptions,
        on_process: Callable[[subprocess.Popen], None] | None = None,
    ) -> str:
        if options.backend == _SCRIPT_BACKEND:
            return self._recognize_with_script(image_path, options.script_path, on_process)
        if options.backend == _PRIMARY_BACKEND:
            return self._recognize_with_paddleocr(image_path, options.language)
        if options.backend == _STRUCTURE_BACKEND:
            return self._recognize_with_pp_structure(
                image_path, options.language, options.structure_formulas
            )
        raise OcrError(f"Unsupported OCR backend: {options.backend}")

    def _recognize_with_script(
        self,
        image_path: str,
        script_path: str,
        on_process: Callable[[subprocess.Popen], None] | None = None,
    ) -> str:
        if not script_path:
            raise OcrError("No OCR script configured.")
        path = Path(script_path)
        if not path.exists():
            raise OcrError(f"OCR script does not exist: {script_path}")
        try:
            process = subprocess.Popen(
                [script_path, image_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                # Own process group so a cancel can kill the script's children,
                # which would otherwise hold the pipes open and block here.
                start_new_session=True,
            )
        except OSError as exc:
            raise OcrError(f"Unable to start OCR script: {exc}") from exc
        if on_process is not None:
            on_process(process)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise OcrError((stderr or "").strip() or f"OCR script exited with code {process.returncode}.")
        text = (stdout or "").strip()
        if not text:
            raise OcrError("OCR script finished but returned no text.")
        return text

    def _recognize_with_paddleocr(self, image_path: str, language: str) -> str:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            if self._is_paddle_protobuf_error(exc):
                raise self._paddle_protobuf_error() from exc
            raise OcrMissingDependencyError(
                "PaddleOCR is not installed.\n\n"
                "In your virtual environment run:\n"
                "pip install -r requirements-ocr.txt"
            ) from exc
        except Exception as exc:  # noqa: BLE001
            if self._is_paddle_protobuf_error(exc):
                raise self._paddle_protobuf_error() from exc
            raise OcrError(f"PaddleOCR could not be loaded: {exc}") from exc

        if language == "spanish_english":
            raise OcrError(
                "PaddleOCR 3.7.0 in this port does not provide a working mixed Spanish+English setting. "
                "Use English or Spanish, or switch to the OCR script backend."
            )

        lang_map = _PADDLE_LANGUAGES
        try:
            # Screenshots are already oriented, flat images, so the document
            # orientation, unwarping, and text-line orientation models only
            # add startup cost here.  oneDNN must remain disabled with the
            # currently supported PaddlePaddle CPU runtime: PP-OCRv6 otherwise
            # fails in ConvertPirAttribute2RuntimeAttribute before inference.
            ocr = PaddleOCR(
                lang=lang_map.get(language, "en"),
                enable_mkldnn=False,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
            result = ocr.predict(image_path)
        except Exception as exc:  # noqa: BLE001
            if self._is_paddle_protobuf_error(exc):
                raise self._paddle_protobuf_error() from exc
            if "ConvertPirAttribute2RuntimeAttribute" in str(exc):
                raise self._mkldnn_unsupported_error() from exc
            raise OcrError(f"PaddleOCR failed: {exc}") from exc

        lines = self._extract_paddleocr_text(result)
        if not lines:
            raise OcrError("PaddleOCR finished but returned no recognized text.")
        return "\n".join(lines).strip()

    def _recognize_with_pp_structure(
        self,
        image_path: str,
        language: str,
        recognize_formulas: bool = False,
    ) -> str:
        """Recognize text keeping the document layout and return Markdown.

        Unlike :meth:`_recognize_with_paddleocr`, which returns text lines with
        no geometry, this runs PaddleOCR's document structure pipeline
        (``PP-StructureV3``): layout detection plus table recognition, rendered
        as Markdown.  That is what keeps tables as tables instead of a flat list
        of cells.  It is slower and needs extra models, so it is opt-in.
        """
        try:
            from paddleocr import PPStructureV3
        except ImportError as exc:
            if self._is_paddle_protobuf_error(exc):
                raise self._paddle_protobuf_error() from exc
            raise OcrMissingDependencyError(self._structure_dependency_message()) from exc
        except Exception as exc:  # noqa: BLE001
            if self._is_paddle_protobuf_error(exc):
                raise self._paddle_protobuf_error() from exc
            raise OcrError(f"PaddleOCR could not be loaded: {exc}") from exc

        try:
            pipeline = PPStructureV3(
                lang=_PADDLE_LANGUAGES.get(language, "en"),
                # Same guards as the line-oriented pipeline: screenshots are
                # already oriented and flat, so the orientation/unwarping models
                # only cost startup time, and oneDNN must stay disabled with the
                # supported PaddlePaddle CPU runtime.
                enable_mkldnn=False,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                use_table_recognition=True,
                use_formula_recognition=recognize_formulas,
            )
        except Exception as exc:  # noqa: BLE001
            if self._is_paddle_protobuf_error(exc):
                raise self._paddle_protobuf_error() from exc
            if self._is_structure_dependency_error(exc):
                raise OcrMissingDependencyError(self._structure_dependency_message()) from exc
            raise OcrError(f"PaddleOCR layout pipeline could not be created: {exc}") from exc

        try:
            results = pipeline.predict(image_path)
        except Exception as exc:  # noqa: BLE001
            if self._is_paddle_protobuf_error(exc):
                raise self._paddle_protobuf_error() from exc
            if "ConvertPirAttribute2RuntimeAttribute" in str(exc):
                raise self._mkldnn_unsupported_error() from exc
            raise OcrError(f"PaddleOCR layout parsing failed: {exc}") from exc

        markdown = self._extract_structure_markdown(results)
        if not markdown:
            raise OcrError("PaddleOCR layout parsing finished but returned no recognized text.")
        return markdown

    @staticmethod
    def _extract_structure_markdown(results) -> str:
        """Collect ``markdown_texts`` from every page of a layout result."""
        pages: list[str] = []
        for result in results or []:
            markdown = getattr(result, "markdown", None)
            if not isinstance(markdown, dict):
                continue
            text = markdown.get("markdown_texts")
            if isinstance(text, str) and text.strip():
                pages.append(text.strip())
        return "\n\n".join(pages).strip()

    @classmethod
    def _is_structure_dependency_error(cls, exc: BaseException) -> bool:
        """Detect the missing ``paddlex[ocr]`` error hidden in a cause chain.

        PaddleOCR rewrites PaddleX's ``DependencyError`` into a generic
        ``RuntimeError``, keeping the original as ``__cause__``.
        """
        seen = 0
        current: BaseException | None = exc
        while current is not None and seen < 6:
            if (
                type(current).__name__ == "DependencyError"
                or "requires additional dependencies" in str(current)
            ):
                return True
            current = current.__cause__ or current.__context__
            seen += 1
        return False

    @staticmethod
    def _structure_dependency_message() -> str:
        return (
            "The PaddleOCR layout pipeline (tables + Markdown) needs extra dependencies "
            "that are not installed.\n\n"
            "Close ksnip_py, activate its virtual environment and run:\n"
            "python -m pip install -r requirements-ocr.txt\n\n"
            "Restart ksnip_py afterwards. The first run also downloads the layout and "
            "table models into ~/.paddlex/official_models."
        )

    @staticmethod
    def _mkldnn_unsupported_error() -> OcrError:
        return OcrError(
            "PaddleOCR reached an unsupported oneDNN operation even though ksnip_py disabled its MKL-DNN backend. "
            "Please report the installed PaddlePaddle, PaddleOCR, and CPU details."
        )

    @staticmethod
    def _is_paddle_protobuf_error(exc: BaseException) -> bool:
        message = str(exc).lower()
        return (
            "couldn't build proto file into descriptor pool" in message
            or "partially initialized module 'paddle'" in message
            or "partially initialized module \"paddle\"" in message
        )

    @staticmethod
    def _paddle_protobuf_error() -> OcrError:
        return OcrError(
            "PaddleOCR and the installed Protobuf version are incompatible. "
            "Close ksnip_py, activate its virtual environment, run "
            "`python -m pip install -r requirements-ocr.txt`, and restart ksnip_py. "
            "A restart is required because Paddle may remain partially loaded after this failure."
        )

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
        self._process: subprocess.Popen | None = None

    def cancel(self) -> None:
        self._cancel_requested = True
        self._kill_process()

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
                text = self._backend.recognize_file(temp_path, self._options, on_process=self._capture_process)
            except OcrCancelledError:
                self.cancelled.emit()
                return
            except OcrError as exc:
                # A killed script surfaces as an error; report cancellation instead.
                if self._cancel_requested:
                    self.cancelled.emit()
                    return
                self.failed.emit(str(exc))
                return
            if self._cancel_requested:
                self.cancelled.emit()
                return
            self.finished.emit(text)
        finally:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except OSError:
                pass

    def _capture_process(self, process: subprocess.Popen) -> None:
        self._process = process
        if self._cancel_requested:
            self._kill_process()

    def _kill_process(self) -> None:
        process = self._process
        if process is None or process.poll() is not None:
            return
        try:
            # start_new_session makes pgid == pid, so this reaches the script's children.
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (OSError, ProcessLookupError):
            try:
                process.kill()
            except OSError:
                pass
