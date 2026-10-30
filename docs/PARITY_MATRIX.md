# C++ to PyQt6 parity matrix

This is the consolidated equivalence record between the original C++ ksnip and
the PyQt6 port in `ksnip_py/`. It exists so that nobody has to read the C++
sources to answer one question: did upstream have this, and what happened to
it in the port?

- Reference implementation: ksnip 1.11.0, restored for this audit under
  `external/ksnip/`. That directory is ignored by Git (`.gitignore`).
- Pre-removal state of the port: tag `cpp-final`.
- Method: comparison of the C++ sources, the Python implementation, the
  automated tests and the focused audits already in `docs/`.
- Limitation: `libraries/kImageAnnotator` and `libraries/kColorPicker` are Git
  submodules and were empty during this audit. The annotation rows rely on
  `docs/KIMAGEANNOTATOR_TOOL_PARITY.md`, written while the submodule was
  present, and on the property tables kept in `ROADMAP.md`.

## Verdicts

| Verdict | Meaning |
| --- | --- |
| Equivalent | Same behaviour, same user-visible result. |
| Differs | Ported, but with a difference that the row states. |
| Missing | Present upstream, absent in the port, no decision recorded. |
| Dropped | Present upstream, deliberately left out, decision recorded. |
| Added | No upstream counterpart; port-only feature. |

Rows marked **Missing** are the open decisions. Everything else is closed.

## Summary

| Subsystem | Overall | Notable gap |
| --- | --- | --- |
| Command line | Equivalent | The port adds `--language` and standard-input images |
| Startup and lifecycle | Equivalent | None |
| Capture backends | Differs | Gnome and KDE Wayland grabbers replaced by the generic portal; Windows and macOS grabbers dropped |
| Editor and annotation | Equivalent | Sticker collections, item rotation, spell checking and SVG export are port extensions |
| Files and formats | Differs | Fixed save-format list instead of the Qt writer list |
| Settings | Differs | Imgur, FTP, Actions and Plugins pages are placeholders, the Stickers page as well, and several controls on Application, Snipping Area and Annotator are disabled |
| Tray icon | Equivalent | None |
| Modeless windows | Equivalent | None; the Windows OCR window went with the Linux-only decision |
| Uploaders | Missing | Only the script uploader works; FTP is still undecided |
| Watermark | Equivalent | None |
| OCR | Differs | Plugin backend replaced by PaddleOCR and a script backend |
| Plugins and actions | Missing | Actions are still a placeholder; plugins dropped |
| Hotkeys | Differs | Application shortcuts only; no native global hotkeys |
| Translations | Equivalent | 41 bundled catalogues against 39 upstream |
| Packaging and platform | Differs | Debian package exists; no AppImage, RPM, Windows or macOS builds |

## 1. Command line

Upstream reference: `src/backend/commandLine/CommandLine.cpp`.

| C++ | ksnip_py | Verdict | Evidence |
| --- | --- | --- | --- |
| `-r`, `--rectarea` | `--rectarea` | Equivalent | `app.py`, `docs/CLI_PARITY.md` |
| `-l`, `--lastrectarea` | `--lastrectarea` | Equivalent | `app.py`, `capture.py` |
| `-f`, `--fullscreen` | `--fullscreen` | Equivalent | `app.py`, `capture.py` |
| `-m`, `--current` | `--current` | Equivalent | `app.py`, `capture.py` |
| `-a`, `--active` | `--active` | Equivalent | `app.py`, `capture.py` |
| `-u`, `--windowundercursor` | `--windowundercursor` | Equivalent | `app.py`, `capture.py` |
| `-t`, `--portal` | `--portal` | Equivalent | `app.py`, `capture.py` |
| `-d`, `--delay SECONDS` | `--delay` | Equivalent | `app.py` |
| `-c`, `--cursor` | `--cursor` | Differs | Works on X11 only; the C++ version also covers Windows and macOS |
| `-e`, `--edit IMAGE` | `--edit` | Equivalent | `app.py` |
| `-s`, `--save` | `--save` | Equivalent | `app.py` |
| `-p`, `--saveto PATH` | `--saveto` | Equivalent | `app.py` |
| `-o`, `--upload` | `--upload` | Equivalent | `app.py`, `uploader.py` |
| `-v`, `--version` | `--version` | Equivalent | `app.py` |
| `-h`, `--help` | `--help` | Equivalent | `app.py` |
| Positional image argument | Positional `image` | Equivalent | `app.py` |
| No language override | `--language LOCALE` | Added | `app.py`, `i18n.py` |
| No standard input support | `-` reads an image from stdin | Added | `app.py`, `main_window.py` |

## 2. Startup and lifecycle

Upstream reference: `src/main.cpp`, `src/gui/MainWindow.cpp`, `src/backend/ipc/`.

| C++ | ksnip_py | Verdict | Evidence |
| --- | --- | --- | --- |
| Single instance with IPC forwarding | Same, over a Qt local socket | Equivalent | `single_instance.py`, `docs/STARTUP_LIFECYCLE_PARITY.md` |
| Forward command-line arguments to the running instance | Same | Equivalent | `single_instance.py` |
| Capture on startup with the last capture mode | Same | Equivalent | `main_window.py`, settings page Application |
| Remember main-window position | Same | Equivalent | `main_window.py` |
| Restore the last used capture mode | Same | Equivalent | `main_window.py` |
| Prompt to save unsaved images on exit | Same | Equivalent | `main_window.py` |
| Tabs with dirty state and dynamic titles | Same | Equivalent | `main_window.py` |
| Auto hide tabs | Same | Equivalent | settings page Application |
| Auto hide docks | Same | Equivalent | `main_window.py` |
| Auto resize to content with a configurable delay | Same | Equivalent | `main_window.py` |
| Remember editor window size and position | Same | Equivalent | `main_window.py` |
| No equivalent | Forward image bytes from stdin to the running instance | Added | `single_instance.py` |

## 3. Capture backends

Upstream reference: `src/backend/imageGrabber/`, `src/gui/snippingArea/`.

| C++ | ksnip_py | Verdict | Evidence |
| --- | --- | --- | --- |
| X11 full screen, all monitors | Same | Equivalent | `capture.py` |
| X11 current screen | Same | Equivalent | `capture.py` |
| X11 active window | Same | Equivalent | `capture.py` |
| X11 window under cursor | Same | Equivalent | `capture.py` |
| X11 rectangular area with magnifier, rulers and info text | Same | Equivalent | `capture.py`, `SelectionOverlay` |
| X11 cursor capture through XFixes | Same | Equivalent | `capture.py` |
| Gnome X11 grabber | Generic X11 grabber | Differs | `capture.py` |
| Generic Wayland grabber through `xdg-desktop-portal` | Same, as a portal client | Equivalent | `capture.py`, `docs/CAPTURE_BACKEND_PARITY.md` |
| Gnome Wayland grabber | Portal only | Differs | No GNOME-specific path |
| KDE Wayland grabber | Portal only | Differs | No KDE-specific path |
| Interactive portal chooser for area, window and screen modes | Same | Equivalent | `capture.py` |
| Non-interactive full-screen portal request | Same | Equivalent | `capture.py` |
| Wayland device-pixel-ratio scaling option | Same, with the same limits | Equivalent | `capture.py` |
| Freeze image while snipping | Same | Equivalent | settings page Image Grabber |
| Snipping-area transparency, cursor colour and thickness | Same | Equivalent | settings page Image Grabber |
| Capture delay and implicit delay | Same semantics | Equivalent | `main_window.py`, `capture.py` |
| Hide and restore the main window during capture | Same | Equivalent | `main_window.py` |
| Windows grabber | None | Dropped | The port is Linux-only; decided on 2026-10-30 |
| macOS grabber | None | Dropped | The port is Linux-only; decided on 2026-10-30 |

## 4. Editor and annotation

Upstream reference: `src/gui/imageAnnotator/`, `libraries/kImageAnnotator/`.
Tool rows are backed by `docs/KIMAGEANNOTATOR_TOOL_PARITY.md`.

| C++ | ksnip_py | Verdict | Evidence |
| --- | --- | --- | --- |
| Select tool | Same | Equivalent | `canvas.py` |
| Duplicate area tool | Same | Equivalent | `canvas.py` |
| Arrow tool | Same | Equivalent | `canvas.py` |
| Double arrow tool | Same | Equivalent | `canvas.py` |
| Line tool | Same | Equivalent | `canvas.py` |
| Pen tool | Same | Equivalent | `canvas.py` |
| Marker pen tool | Same | Equivalent | `canvas.py` |
| Marker rectangle tool | Same | Equivalent | `canvas.py` |
| Marker ellipse tool | Same | Equivalent | `canvas.py` |
| Rectangle tool | Same | Equivalent | `canvas.py` |
| Ellipse tool | Same | Equivalent | `canvas.py` |
| Text tool | Same, plus inline editor and spell checking | Equivalent | `canvas.py`, `spellcheck.py` |
| Text pointer tool | Same | Equivalent | `canvas.py` |
| Text arrow tool | Same | Equivalent | `canvas.py` |
| Number tool | Same | Equivalent | `canvas.py` |
| Number pointer tool | Same | Equivalent | `canvas.py` |
| Number arrow tool | Same | Equivalent | `canvas.py` |
| Blur tool | Same | Equivalent | `canvas.py` |
| Pixelate tool | Same | Equivalent | `canvas.py` |
| Sticker tool | Same tool, different catalogue | Differs | Nine bundled collections plus a user folder, instead of the upstream sticker set (`sticker_picker.py`) |
| Crop | Same | Equivalent | `canvas.py` |
| Undo and redo | Same | Equivalent | `canvas.py` |
| Multi-selection, move and resize | Same | Equivalent | `canvas.py` |
| Item copy, paste, duplicate and delete | Same | Equivalent | `main_window.py` |
| Item ordering, bring to front and send to back | Same | Equivalent | `main_window.py` |
| Rotate image | Same | Equivalent | `main_window.py` |
| Scale image | Same | Equivalent | `main_window.py` |
| Modify canvas | Same | Equivalent | `main_window.py` |
| Zoom from 10 to 800 percent, fit to window, Ctrl and wheel | Same | Equivalent | `canvas.py` |
| Item shadow, opacity, fill mode and text properties | Same | Equivalent | `canvas.py` |
| No grayscale or invert effect | `No Effect`, `Drop Shadow`, `Grayscale`, `Invert Color`, `Border` | Added | `main_window.py`, `canvas.py` |
| No spell checking | Hunspell suggestions in the text editor | Added | `spellcheck.py` |
| No item rotation | Rotation handle on the selected item, Shift snaps to 15 degree steps | Added | `canvas.py` |
| No SVG export | `File > Export as SVG` | Added | `main_window.py` |
| No project format | `.ksnip` projects | Added | `project_io.py` |

## 5. Files, formats and projects

Upstream reference: `src/backend/saver/`, `src/gui/captureHandler/`.

| C++ | ksnip_py | Verdict | Evidence |
| --- | --- | --- | --- |
| Open image | Same | Equivalent | `main_window.py` |
| Open directory | Same | Equivalent | `main_window.py` |
| Open recent images | Same | Equivalent | `main_window.py` |
| Paste image from clipboard | Same | Equivalent | `main_window.py` |
| Paste embedded image | Same | Equivalent | `main_window.py` |
| Save | Same | Equivalent | `main_window.py` |
| Save as | Same | Equivalent | `main_window.py` |
| Save all | Same | Equivalent | `main_window.py` |
| Rename | Same | Equivalent | `main_window.py` |
| Delete image | Same | Equivalent | `main_window.py` |
| Print | Same | Equivalent | `main_window.py` |
| Print preview | Same | Equivalent | `main_window.py` |
| Copy composed image | Same | Equivalent | `main_window.py` |
| Copy path | Same | Equivalent | `main_window.py` |
| Copy as data URI | Same | Equivalent | `main_window.py` |
| Save formats taken from `QImageWriter::supportedImageFormats()` | Fixed list: PNG, JPEG, BMP, WebP | Differs | `main_window.py`, `FileDialogFilterHelper.cpp` |
| Save quality mode and factor | Same | Equivalent | settings page Saver |
| Filename wildcards `$Y $M $D $T $h $m $s` and a numeric counter | Same | Equivalent | `main_window.py`, `WildcardResolver.cpp` |
| Overwrite file with the same name | Same | Equivalent | settings page Saver |
| Default save directory and filename | Same | Equivalent | settings page Saver |
| Remember the last save directory | Same | Equivalent | settings page Saver |
| Drag and drop images onto the window | Same | Equivalent | `main_window.py` |
| No companion image | Optional flattened image next to a `.ksnip` project | Added | settings page Saver, `project_io.py` |

## 6. Settings

Upstream reference: `src/gui/settingsDialog/`, `src/backend/config/IConfig.h`.

Page-level equivalence only: individual controls inside a page are not
tracked row by row here, but a page whose controls are disabled is not
equivalent to the upstream page.

| C++ | ksnip_py | Verdict | Evidence |
| --- | --- | --- | --- |
| Application page | Same controls, but `Use Tabs` is a disabled placeholder | Differs | `settings_dialog.py` |
| Image Grabber page | Same controls | Equivalent | `settings_dialog.py` |
| Snipping Area page | Ten of the eleven controls are disabled placeholders; only the magnifying glass works | Differs | `settings_dialog.py` |
| Saver page | Same controls | Equivalent | `settings_dialog.py` |
| Annotator page | Same controls, but smooth painter paths, smooth factor and canvas colour are disabled placeholders | Differs | `settings_dialog.py` |
| Sticker page | Placeholder that states management parity is pending | Missing | `settings_dialog.py` |
| Tray Icon page | Same controls | Equivalent | `settings_dialog.py` |
| Watermark page | Same controls | Equivalent | `settings_dialog.py` |
| Uploader page | Type selector disabled and fixed to Script | Differs | `settings_dialog.py` |
| Script Uploader page | Same controls | Equivalent | `settings_dialog.py` |
| Imgur Uploader page | Placeholder page that states parity is pending | Dropped | Deferred until an Imgur Client ID is registered; see `docs/imgur/README_ES.md` |
| FTP Uploader page | Placeholder page that states parity is pending | Missing | `settings_dialog.py` |
| HotKeys page | Application shortcuts only | Differs | `settings_dialog.py` |
| Actions page | Placeholder with a disabled Add button | Missing | `settings_dialog.py` |
| Plugins page | Placeholder with disabled search-path controls | Dropped | Follows the plugin system decision |
| No OCR page | OCR backend, language and script | Added | `settings_dialog.py` |
| No scheme colours page | Editable annotation colour scheme table | Added | `settings_dialog.py` |
| Search box filtering the settings tree | Navigation filter | Equivalent | `settings_dialog.py`, `SettingsDialog.cpp` |
| Application style selector | Disabled combo, applies nothing | Missing | `settings_dialog.py` |
| Debug logging toggle | Disabled checkbox | Missing | `settings_dialog.py` |
| Temporary directory setting | Disabled field fixed to `/tmp` | Missing | `IConfig.h` has `tempDirectory` |

## 7. Tray icon

Upstream reference: `src/gui/TrayIcon.cpp`, `src/gui/settingsDialog/TrayIconSettings.cpp`.

| C++ | ksnip_py | Verdict | Evidence |
| --- | --- | --- | --- |
| Enable the tray icon | Same | Equivalent | `main_window.py` |
| Default tray action: show editor or capture | Same | Equivalent | `main_window.py` |
| Default tray capture mode | Same | Equivalent | `main_window.py` |
| Minimize to tray | Same | Equivalent | `main_window.py` |
| Close to tray | Same | Equivalent | `main_window.py` |
| Start minimized to tray | Same | Equivalent | `main_window.py` |
| Tray notifications | Same | Equivalent | `main_window.py` |
| Platform-specific notification service | Desktop notifications through Qt | Differs | No separate platform service |
| Tray menu with capture modes and actions | Same | Equivalent | `main_window.py` |

## 8. Modeless windows

Upstream reference: `src/gui/modelessWindows/`.

| C++ | ksnip_py | Verdict | Evidence |
| --- | --- | --- | --- |
| Pin window | Same | Equivalent | `pin_window.py` |
| Pin window opacity, always on top and close behaviour | Same | Equivalent | `pin_window.py` |
| OCR result window | Same | Equivalent | `ocr_result_dialog.py` |
| OCR text selection and copy | Same | Equivalent | `ocr_result_dialog.py` |
| Windows OCR window (`WinOcrWindow`) | None | Dropped | The port is Linux-only; decided on 2026-10-30 |

## 9. Uploaders

Upstream reference: `src/backend/uploader/`, `src/gui/ImgurHistoryDialog.cpp`.

| C++ | ksnip_py | Verdict | Evidence |
| --- | --- | --- | --- |
| Script uploader | Same | Equivalent | `uploader.py` |
| Copy script output to clipboard | Same | Equivalent | `uploader.py` |
| Upload confirmation prompt | Same | Equivalent | `main_window.py` |
| Imgur uploader | None | Dropped | Deferred until an Imgur Client ID is registered; see `docs/imgur/README_ES.md` |
| Imgur history dialog | None | Dropped | Follows the Imgur uploader decision |
| Imgur delete and album management | None | Dropped | Follows the Imgur uploader decision |
| FTP uploader | None | Missing | No decision recorded |
| Upload progress and failure reporting | Text status and message box | Differs | No progress dialog |

## 10. Watermark

Upstream reference: `src/gui/settingsDialog/WatermarkSettings.cpp`, `src/gui/operations/`.

| C++ | ksnip_py | Verdict | Evidence |
| --- | --- | --- | --- |
| Watermark image | Same | Equivalent | `watermark.py` |
| Opacity, rotation, scale and position | Same | Equivalent | `watermark.py` |
| Watermark settings page with preview | Same | Equivalent | `settings_dialog.py` |
| Add watermark from the menu and the toolbar | Same | Equivalent | `main_window.py` |
| Multiple watermarks per image | Same | Equivalent | `watermark.py` |

## 11. OCR

Upstream reference: `src/plugins/interfaces/IPluginOcr.h`, `src/gui/modelessWindows/ocrWindow/`.

| C++ | ksnip_py | Verdict | Evidence |
| --- | --- | --- | --- |
| OCR through a plugin interface | PaddleOCR backend and a script backend | Differs | `ocr_backend.py`, `docs/OCR_PADDLEOCR_ES.md` |
| OCR result window | Same | Equivalent | `ocr_result_dialog.py` |
| OCR language selection | Same | Equivalent | `settings_dialog.py` |
| Copy the result automatically | Same | Equivalent | `settings_dialog.py` |
| OCR action enabled and disabled from settings | Same | Equivalent | `settings_dialog.py` |
| No table or formula output | Tables in HTML, Markdown and LaTeX | Added | `ocr_backend.py` |

## 12. Plugins and actions

Upstream reference: `src/plugins/`, `src/gui/actions/`.

| C++ | ksnip_py | Verdict | Evidence |
| --- | --- | --- | --- |
| Plugin manager, loader and finder | None | Dropped | Python has no stable plugin ABI; the built-in OCR backends replace the plugin interface |
| Plugin search paths | Disabled controls in the settings page | Dropped | Follows the plugin system decision |
| Plugin-provided OCR | Replaced by the built-in backends | Dropped | `ocr_backend.py` |
| User-defined actions with a command and shortcuts | None | Missing | `ActionsMenu.cpp` has no counterpart |
| Actions menu in the menu bar | None | Missing | `main_window.py` |

## 13. Hotkeys

Upstream reference: `src/gui/globalHotKeys/`.

| C++ | ksnip_py | Verdict | Evidence |
| --- | --- | --- | --- |
| Native global hotkeys on X11 | Application shortcuts only | Missing | `docs/GLOBAL_HOTKEYS.md` |
| Native global hotkeys on Windows and macOS | None | Dropped | Follows the Linux-only decision |
| Configurable capture shortcuts | Same, while the window is active | Differs | `settings_dialog.py` |
| Default shortcut set | Same values | Equivalent | `main_window.py` |

## 14. Translations

Upstream reference: `translations/`.

| C++ | ksnip_py | Verdict | Evidence |
| --- | --- | --- | --- |
| Qt Linguist catalogues loaded at startup | Same | Equivalent | `i18n.py` |
| Language selector in settings | Same, plus `--language` | Equivalent | `settings_dialog.py`, `i18n.py` |
| Official Qt base catalogues | Same, from `QLibraryInfo.TranslationsPath` | Equivalent | `i18n.py`, `docs/FILE_DIALOGS.md` |
| 39 upstream catalogues | 41 bundled catalogues | Differs | `ksnip_py/translations/` |
| Right-to-left layout support | Not verified | Not verified | No RTL catalogue bundled |

## 15. Packaging and platform

| C++ | ksnip_py | Verdict | Evidence |
| --- | --- | --- | --- |
| CMake build | Python package through `pyproject.toml` | Differs | `pyproject.toml` |
| No Debian package | Native Debian package, Policy 4.7.4.1 | Added | `debian/`, `README.md` |
| AppImage | None | Missing | No recipe |
| RPM | None | Missing | No recipe |
| Windows installer | None | Dropped | The port is Linux-only; decided on 2026-10-30 |
| macOS DMG | None | Dropped | The port is Linux-only; decided on 2026-10-30 |
| No manual page | `ksnip-pyqt6.1` | Added | `debian/` |
| No AppStream metadata | `org.ksnip.ksnip-pyqt6.metainfo.xml` | Added | `debian/` |
| CI builds the C++ application | CI builds and tests the Python distributions | Differs | `.github/workflows/` |

## Decisions taken

These groups were open in the first pass of this matrix and are now closed.
The rows they cover are marked **Dropped** above.

1. Windows and macOS support: their grabbers, the WinRT OCR window and the
   installers. Decided on 2026-10-30: the port is Linux-only. If that ever
   changes, the rows have to be reopened together, because a partial port
   would leave capture and OCR inconsistent with each other.
2. Imgur uploader, its history dialog and its album management. Deferred, not
   abandoned: the implementation is blocked on registering a Client ID, and
   the design is already written in `docs/imgur/README_ES.md`.
3. Plugin system, its search paths and the plugin-provided OCR interface.
   Dropped: Python has no stable plugin ABI, and the built-in PaddleOCR and
   script backends already cover the use case the interface existed for.
4. Gnome and KDE Wayland grabbers. Dropped as redundant: the generic
   `xdg-desktop-portal` client already serves both desktops, which is why those
   rows were marked *differs* and never *missing*.

## Decisions still open

| # | Decision | Why it is open | Cost if implemented |
| --- | --- | --- | --- |
| 1 | FTP uploader | No decision recorded yet | `ftplib` ships with Python: about 150 lines plus a settings page and tests |
| 2 | User-defined actions and the Actions menu | No decision recorded yet | `QProcess` plus a settings page, about 100 lines |
| 3 | Native global hotkeys on X11 | Wayland has no portable equivalent, so the scope has to be decided first | `XGrabKey` through `ctypes`; `docs/GLOBAL_HOTKEYS.md` records the constraints |
| 4 | Temporary directory setting | No decision recorded yet | One preference plus its use when creating temporary files |
| 5 | AppImage and RPM packaging | No decision recorded yet | One recipe per format plus their CI jobs |
| 6 | Unimplemented settings: sticker management page, application style, debug logging | The pages and controls exist but are disabled placeholders | Wiring each control to the backend it configures |

Rows marked **Differs** are already decided; they are listed in the matrix only
so that a future change can revisit them deliberately rather than by accident.
