# ksnip PyQt6 Port

[![Port status](https://img.shields.io/badge/status-active%20port-orange)](ROADMAP.md)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6%2B-41CD52?logo=qt&logoColor=white)](pyproject.toml)
[![Debian 13](https://img.shields.io/badge/Debian-13-A81D33?logo=debian&logoColor=white)](#debian-13--mx-linux-25)
[![MX Linux 25](https://img.shields.io/badge/MX%20Linux-25-222222)](#debian-13--mx-linux-25)
[![License: GPL-2.0](https://img.shields.io/badge/license-GPL--2.0-blue)](LICENSE.txt)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen)](#contributing)
[![GitHub issues](https://img.shields.io/github/issues/wachin/ksnip)](https://github.com/wachin/ksnip/issues)
[![GitHub stars](https://img.shields.io/github/stars/wachin/ksnip?style=flat)](https://github.com/wachin/ksnip/stargazers)

An active port of the [ksnip](https://github.com/ksnip/ksnip) screenshot and annotation application from C++/Qt to Python/PyQt6.

The port lives in `ksnip_py/` and aims to preserve the original application structure, workflow, icons, settings hierarchy, and kImageAnnotator behavior. It is already usable, but it is still under development and is not a finished replacement for upstream ksnip.

![Current ksnip interface reference](images/02-ksnip-cuando-a-hecho-su-primer-captura-de-pantalla.png)

## Help wanted

Developers, testers, designers, Debian packagers, and translators are welcome. The most useful areas for contributions are:

- Wayland and `xdg-desktop-portal` capture support.
- Native global hotkeys.
- Fine visual parity with the original toolbar, editor, and settings dialog.
- Remaining kImageAnnotator behavior and effects.
- Imgur, FTP, OCR, and plugin-system parity.
- Automated GUI tests.
- Debian packaging and policy review.

See [ROADMAP.md](ROADMAP.md) for the detailed implementation status and reference screenshots.

## Current features

- Rectangular, last-area, full-screen, current-screen, active-window, and window-under-cursor capture modes.
- Optional real X11 cursor capture through XFixes, inserted as an editable image item.
- Capture delay, implicit delay, startup capture, auto-copy, and auto-save preferences.
- Open, paste, embedded paste, save, save as, save all, rename, delete, print, and print preview.
- Multiple image tabs with dirty-state tracking and dynamic window titles.
- Recent images, containing-directory access, path copying, and Data URI copying.
- Annotation tools for selection, pen, markers, lines, arrows, shapes, text, numbers, blur, pixelate, stickers, and crop.
- Inline multiline text editing with re-editing and Hunspell-backed spelling suggestions.
- Multiple selection, move, resize, duplicate, ordering, copy/paste, undo, and redo.
- Rotate, scale, crop, and modify-canvas operations.
- Watermarks and always-on-top pin windows.
- Script uploader and experimental PaddleOCR/script OCR backends.
- System tray workflow and configurable application shortcuts.
- Hierarchical settings dialog modeled after the original C++ application.
- Command-line image opening and capture-mode selection.

## Known gaps

- Generic Wayland portal capture and Wayland-specific screenshot scaling.
- Native OS-global hotkey registration.
- Complete C++ plugin-system parity.
- Native Imgur and FTP uploaders.
- Full `Cut` tool parity.
- Exact visual and behavioral parity across every editor control.
- Final Debian packaging and automated GUI coverage.

## Debian 13 / MX Linux 25

The current development environment is AV Linux MXe based on Debian 13 and MX Linux 25.

Install the system runtime and development dependencies:

```bash
sudo apt update
sudo apt install \
  python3-pyqt6 \
  python3-venv \
  python3-pip \
  hunspell \
  hunspell-en-us \
  hunspell-es \
  libxcb-cursor0 \
  libxfixes3 \
  x11-utils \
  xdotool
```

Important X11 dependencies:

- `libxcb-cursor0` is required by the Qt 6 `xcb` platform plugin. Without it, PyQt6 may fail to start on X11.
- `libxfixes3` is used to capture the real mouse cursor.
- `x11-utils` supplies helpers used for active-window geometry.
- `xdotool` is used to identify the window under the cursor.

Hunspell dictionaries are optional but recommended. Install the dictionary packages appropriate for your language if they differ from the English and Spanish examples above.

## Run from system packages

```bash
git clone https://github.com/wachin/ksnip.git
cd ksnip
python3 -m ksnip_py
```

## Run from a virtual environment

Debian uses an externally managed system Python, so Python-only optional dependencies should be installed in a virtual environment:

```bash
git clone https://github.com/wachin/ksnip.git
cd ksnip

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .

ksnip-pyqt6
```

The spell checker continues to use the system `hunspell` executable and dictionaries when the application runs inside a virtual environment.

## Desktop theme integration

On GTK-based desktops, the following can help Qt use the desktop file-dialog and menu theme:

```bash
QT_QPA_PLATFORMTHEME=gtk3 python3 -m ksnip_py
```

## Command line

```text
ksnip-pyqt6 [IMAGE]
ksnip-pyqt6 --edit IMAGE
ksnip-pyqt6 --rectarea
ksnip-pyqt6 --lastrectarea
ksnip-pyqt6 --fullscreen
ksnip-pyqt6 --current
ksnip-pyqt6 --active
ksnip-pyqt6 --windowundercursor
ksnip-pyqt6 --delay SECONDS --fullscreen
ksnip-pyqt6 --fullscreen --cursor
ksnip-pyqt6 --fullscreen --save
ksnip-pyqt6 --current --saveto /path/to/capture.png
```

Use `ksnip-pyqt6 --help` for the current option list. Portal and direct-upload CLI parity are still pending.

## Text tool

1. Select `Text`.
2. Drag a rectangle on the screenshot.
3. Type directly in the inline editor.
4. Press `Ctrl+Enter` to accept or `Esc` to cancel a new text item.
5. Double-click an existing text item, or use `Edit text`, to edit it again.

Hunspell automatically detects installed dictionaries, underlines misspelled words, and provides replacement suggestions in the context menu.

## Optional OCR

OCR is experimental and does not prevent the application from starting when PaddleOCR is unavailable. A script backend can also be configured in Settings.

To install PaddleOCR in the project virtual environment:

```bash
source .venv/bin/activate
python -m pip install paddlepaddle paddleocr
```

Current limitations:

- Cancellation is best-effort after a backend call has started.
- Live PaddleOCR recognition has not yet received full automated coverage.
- Plugin and modeless-window behavior does not yet match the C++ implementation completely.

## Project layout

```text
ksnip_py/       Active PyQt6 implementation
src/            Original C++ ksnip reference implementation
images/         UI and behavior reference screenshots
debian/         Initial Debian packaging scaffold
ROADMAP.md      Detailed port status and next work blocks
pyproject.toml  Python package and executable metadata
```

The `kColorPicker` and `kImageAnnotator` git submodules are behavioral references, not Python runtime dependencies. After a fresh clone, initialize them with:

```bash
git submodule update --init --recursive
```

## Development checks

At minimum, run:

```bash
python3 -m compileall -q ksnip_py
python3 -m ksnip_py --help
```

For a headless startup smoke test:

```bash
timeout 8s env QT_QPA_PLATFORM=offscreen python3 -m ksnip_py
```

## Contributing

1. Read [ROADMAP.md](ROADMAP.md).
2. Pick one small unchecked behavior or visual-parity item.
3. Compare against the C++ sources and the reference screenshots before changing behavior.
4. Keep unrelated user changes intact.
5. Add a focused smoke test or reproducible verification when possible.
6. Open an issue or pull request at [wachin/ksnip](https://github.com/wachin/ksnip).

Please mention your desktop environment, display protocol (`X11` or `Wayland`), Python version, PyQt6 version, and reproduction steps in bug reports.

## Packaging status

The `debian/` directory contains an initial scaffold only. The package should not be considered policy-complete or ready for Debian submission until UI behavior, dependencies, tests, copyright metadata, and installation paths have been reviewed.

## License

This project follows the existing ksnip licensing terms. See [LICENSE.txt](LICENSE.txt).
