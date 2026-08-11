# ksnip PyQt6 Port

[![Port status](https://img.shields.io/badge/status-active%20port-orange)](ROADMAP.md)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6%2B-41CD52?logo=qt&logoColor=white)](pyproject.toml)
[![Debian 13](https://img.shields.io/badge/Debian-13-A81D33?logo=debian&logoColor=white)](#debian-13--mx-linux-25)
[![MX Linux 25](https://img.shields.io/badge/MX%20Linux-25-222222)](#debian-13--mx-linux-25)
[![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue)](LICENSE.txt)
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
- Editable `.ksnip` project files and SVG export for continued editing in Inkscape.
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
  xdg-desktop-portal \
  xdg-desktop-portal-gtk \
  x11-utils \
  xdotool
```

Important X11 dependencies:

- `libxcb-cursor0` is required by the Qt 6 `xcb` platform plugin. Without it, PyQt6 may fail to start on X11.
- `libxfixes3` is used to capture the real mouse cursor.
- `x11-utils` supplies helpers used for active-window geometry.
- `xdotool` is used to identify the window under the cursor.

Portal dependencies:

- `xdg-desktop-portal` is the desktop-independent frontend used by `--portal`.
- One backend is also required. Backend selection follows `XDG_CURRENT_DESKTOP`, not merely the window manager currently drawing windows.
- For AV Linux MXe, MX Linux, XFCE, LXDE, Openbox, Fluxbox, and IceWM sessions, `xdg-desktop-portal-gtk` is the practical default. Bare or manually assembled window-manager sessions may additionally need a `portals.conf` configuration and a correctly exported `XDG_CURRENT_DESKTOP`.
- Use `xdg-desktop-portal-kde` for Plasma, `xdg-desktop-portal-lxqt` for LXQt, `xdg-desktop-portal-xapp` for Cinnamon, `xdg-desktop-portal-phosh` for Phosh, and `xdg-desktop-portal-wlr` for wlroots-based Wayland compositors. GNOME/Ubuntu sessions normally use `xdg-desktop-portal-gnome`.
- ksnip reports the detected desktop and session type and recommends a package if portal capture is unavailable.

The `xdg-desktop-portal-dev` package is not a runtime dependency. It contains development files used to build portal backend implementations; this PyQt6 port is a portal client over D-Bus and does not need it.

Hunspell dictionaries are optional but recommended. Install the dictionary packages appropriate for your language if they differ from the English and Spanish examples above.

The sticker selector provides six tabs: Original, Papirus, GNOME, Numix, SuperTux, and User. The bundled themes use high-resolution sources, exclude symbolic-link duplicates, remember the last tab, and preserve pinned favorites across theme changes and application restarts. The User tab imports common image formats, preserves transparency and aspect ratio, converts them to PNG with a maximum dimension of 512 px, and stores them in the application's configuration directory; that directory can also be opened directly in the file manager. Copyright notices and GPL licenses for bundled artwork are documented in `THIRD_PARTY_LICENSES.md`, `LICENSES/`, and `debian/copyright`.

## Editable projects and SVG

Choose `File > Save As... > Ksnip Project` to save a `.ksnip` project. The format is a ZIP container with `project.json` and `background.png`; it preserves editable annotations, embedded images and stickers, the image effect, zoom, and number-tool state. Opening the `.ksnip` file restores the editor rather than flattening the annotations.

Whenever a `.ksnip` project is saved, ksnip_py also updates a flattened image beside it with the same base name. PNG is used by default; choose PNG, JPEG, WebP, or BMP under `Settings > Saver > Image saved alongside Ksnip projects`.

New files use PNG as their primary save format by default. Under `Settings > Saver > Default save format`, users can switch the default between a flattened PNG image and an editable `.ksnip` project.

Choose `File > Export as SVG...` to create a document for Inkscape. The screenshot is embedded as PNG while supported annotations remain SVG vectors and text. Raster overlays are embedded as PNG. SVG is intended for interchange with vector editors; use `.ksnip` as the lossless working project format.

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
cat image.png | ksnip-pyqt6 --edit -
ksnip-pyqt6 --rectarea
ksnip-pyqt6 --lastrectarea
ksnip-pyqt6 --fullscreen
ksnip-pyqt6 --current
ksnip-pyqt6 --active
ksnip-pyqt6 --windowundercursor
ksnip-pyqt6 --portal
ksnip-pyqt6 --delay SECONDS --fullscreen
ksnip-pyqt6 --fullscreen --cursor
ksnip-pyqt6 --fullscreen --save
ksnip-pyqt6 --current --saveto /path/to/capture.png
ksnip-pyqt6 --current --upload
ksnip-pyqt6 --fullscreen --save --upload
```

Use `ksnip-pyqt6 --help` for the current option list. `--upload` uses the script configured under `Settings > Uploader > Script Uploader`. On Wayland, `--portal` delegates capture selection to `xdg-desktop-portal`.

Wayland sessions are detected automatically and regular capture actions are redirected through `xdg-desktop-portal`. `Settings > Image Grabber > Force Generic Wayland` applies the same behavior manually, including on X11. Full-screen capture is requested non-interactively; the other capture modes use the portal's interactive chooser.

Single-instance mode is enabled by default and can be changed under `Settings > Application`. Additional invocations forward their command-line arguments to the existing process through a per-user Qt local socket, allowing it to show the editor, open an image, or perform a capture without starting a second GUI instance.
Images supplied through standard input are forwarded as image bytes when another instance is already running.

The PyQt6 port loads Qt Linguist `.qm` catalogs using the language selected under `Settings > Application > Language`, or the system locale by default. Use `--language LOCALE` (for example, `--language es`, `de`, `pt_BR` or `zh_Hant`) for a temporary command-line override. The language selector is generated from the 41 catalogs shipped with the package. Missing messages safely fall back to English.

Compatible strings from the original C++ `ksnip` catalogs are reused by the port. The `ksnip_py` catalog contains messages that only exist in the Python implementation.

Translation workflow for contributors. The synchronization script extracts the Python messages, reuses matching translations from the original `ksnip` and `kImageAnnotator` catalogs, and compiles every `.qm` file:

```bash
python3 tools/update_pyqt_translations.py
```

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
