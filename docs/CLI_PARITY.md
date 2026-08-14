# Command-line parity matrix

This matrix compares `src/backend/commandLine/CommandLine.cpp` with
`ksnip_py/app.py`. It records the intended public interface of the C++ parser,
not accidental implementation defects in that parser.

| C++ option | Python option | Status | Python behavior |
|---|---|---|---|
| `-r`, `--rectarea` | Same | Complete | Select a rectangular capture area. |
| `-l`, `--lastrectarea` | Same | Complete | Reuse the last rectangular area. |
| `-f`, `--fullscreen` | Same | Complete | Capture all screens. |
| `-m`, `--current` | Same | Complete | Capture the screen under the pointer. |
| `-a`, `--active` | Same | Complete | Capture the active window. |
| `-u`, `--windowundercursor` | Same | Complete | Capture the window under the pointer. |
| `-t`, `--portal` | Same | Complete | Capture through `xdg-desktop-portal`. |
| `-d`, `--delay SECONDS` | Same | Complete | Accepts only integers greater than or equal to zero. |
| `-c`, `--cursor` | Same | Complete | Requests inclusion of the pointer. |
| `-e`, `--edit IMAGE` | Same | Complete | Opens an image; `-` reads it from standard input. |
| `-s`, `--save` | Same | Complete | Saves to the configured location without opening the editor. |
| `-p`, `--saveto PATH` | Same | Complete | Saves to the supplied path without opening the editor. |
| `-o`, `--upload` | Same | Complete | Runs the configured script uploader without opening the editor. |
| `-v`, `--version` | Same | Complete | Prints version information and exits. |
| `-h`, `--help` | Same | Complete | Prints usage information and exits. |
| `[IMAGE]` | Same | Complete | Opens one positional image path. |

## Intentional Python extensions

| Python interface | Reason |
|---|---|
| `--language LOCALE` | Temporarily overrides the Qt Linguist locale. |
| `--edit -` or positional `-` | Reads image bytes from standard input and forwards them through single-instance IPC when necessary. |
| Mutually exclusive capture modes | Rejects ambiguous requests instead of depending on the priority order inside `captureMode()`. |
| `--save` combined with `--upload` | Saves and uploads the same capture in one invocation. |

## Corrected C++ reference defects

The C++ implementation assigns the portal option to `mWindowUnderCursorOption`
instead of `mPortalOption`. Consequently, `isPortalSet()` cannot become true,
and `isCaptureModeSet()` also omits the portal check. These are implementation
defects rather than interface requirements: the documented `-t`/`--portal`
option works normally in the PyQt6 port.

## Result

All public command-line arguments exposed by `CommandLine.cpp` are present and
connected to their corresponding Python behavior. No C++ CLI option has been
discarded. Tests in `tests_py/test_app_cli.py` protect the option aliases,
capture-mode mapping, validation, direct-save state, image opening, and Python
extensions.
