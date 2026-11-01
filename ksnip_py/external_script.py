from __future__ import annotations

import os


def external_script_command(script_path: str, *arguments: str) -> list[str]:
    """Build a command line for a user-supplied OCR/upload script.

    Windows cannot execute a .bat or .cmd file directly through CreateProcess,
    so route those through cmd.exe.  Executables are launched as-is on every
    platform.
    """

    if os.name == "nt" and script_path.lower().endswith((".bat", ".cmd")):
        return ["cmd.exe", "/d", "/c", "call", script_path, *arguments]
    return [script_path, *arguments]
