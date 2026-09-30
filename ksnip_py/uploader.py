from __future__ import annotations

import os
import re
import signal
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QImage


@dataclass
class UploadResult:
    ok: bool
    message: str
    output: str = ""


class ScriptUploader:
    def upload(
        self,
        image: QImage,
        script_path: str,
        copy_output_filter: str = "",
        stop_on_stderr: bool = False,
        on_process: Callable[[subprocess.Popen], None] | None = None,
    ) -> UploadResult:
        if image.isNull():
            return UploadResult(False, "No image available for upload.")
        if not script_path:
            return UploadResult(False, "No upload script configured.")
        if not Path(script_path).exists():
            return UploadResult(False, f"Upload script does not exist: {script_path}")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
            temp_path = handle.name
        try:
            if not image.save(temp_path):
                return UploadResult(False, "Unable to save temporary image for upload.")

            try:
                process = subprocess.Popen(
                    [script_path, temp_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    # Own process group so cancel() can kill the script's children,
                    # which would otherwise keep the pipes open and block communicate().
                    start_new_session=True,
                )
            except OSError as exc:
                return UploadResult(False, f"Unable to start upload script: {exc}")
            # Lets a background worker keep the handle so it can kill a hung script.
            if on_process is not None:
                on_process(process)
            stdout, stderr = process.communicate()
            stdout = stdout or ""
            stderr = stderr or ""
            if stop_on_stderr and stderr.strip():
                return UploadResult(False, "Upload script wrote to stderr.", stderr.strip())
            if process.returncode != 0:
                message = stderr.strip() or f"Upload script exited with code {process.returncode}."
                return UploadResult(False, message, stdout.strip())

            output = self._filtered_output(stdout, copy_output_filter)
            return UploadResult(True, "Upload finished successfully.", output.strip())
        finally:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except OSError:
                pass

    def _filtered_output(self, output: str, copy_output_filter: str) -> str:
        if not copy_output_filter:
            return output
        match = re.search(copy_output_filter, output)
        return match.group(0) if match is not None else output


class UploadWorker(QObject):
    """Runs ScriptUploader off the GUI thread so a slow script cannot freeze the window."""

    finished = pyqtSignal(object)
    cancelled = pyqtSignal()

    def __init__(self, uploader: ScriptUploader, image: QImage, script_path: str,
                 copy_output_filter: str = "", stop_on_stderr: bool = False) -> None:
        super().__init__()
        self._uploader = uploader
        self._image = image.copy()
        self._script_path = script_path
        self._copy_output_filter = copy_output_filter
        self._stop_on_stderr = stop_on_stderr
        self._cancel_requested = False
        self._process: subprocess.Popen | None = None

    def cancel(self) -> None:
        self._cancel_requested = True
        self._kill_process()

    def run(self) -> None:
        result = self._uploader.upload(
            self._image,
            script_path=self._script_path,
            copy_output_filter=self._copy_output_filter,
            stop_on_stderr=self._stop_on_stderr,
            on_process=self._capture_process,
        )
        if self._cancel_requested:
            self.cancelled.emit()
            return
        self.finished.emit(result)

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
