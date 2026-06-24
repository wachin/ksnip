from __future__ import annotations

import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

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
                process = subprocess.run(
                    [script_path, temp_path],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except OSError as exc:
                return UploadResult(False, f"Unable to start upload script: {exc}")

            stdout = process.stdout or ""
            stderr = process.stderr or ""
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
