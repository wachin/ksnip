# PyQt6 Port MVP

This repository now contains a parallel PyQt6 port of `ksnip` under `ksnip_py/`.

Current scope:

- Main window with toolbar and menus
- Capture modes: rectangular area, last rectangular area, full screen, current screen, active window, window under cursor
- Open image from disk
- Paste image from clipboard
- Save and save as
- Copy image to clipboard
- Tabbed image editing
- Basic settings persistence for window state and editor defaults
- Settings dialog for editor defaults and watermark options
- Configurable persisted application hotkeys for capture and core actions
- Script uploader support with persisted settings
- Experimental OCR integration with optional PaddleOCR or script backend
- Tray icon workflow with show/hide, start/minimize/close-to-tray settings
- Recent images menu with reopen support
- Pin current image into always-on-top floating windows
- Watermark image storage and add-watermark action
- Capture preferences for delay, auto-copy, and hide/show main-window behavior
- Undo and redo
- Rotate and scale transforms
- Select and move overlay annotation items
- Ctrl-click additive multi-selection with group move
- Resize handles for overlay rectangle, ellipse, line, arrow, and text items
- Delete selected overlay item or selection
- Duplicate selected overlay item or selection
- Re-edit selected text item
- Bring selected overlay item or selection to front or send it to back
- Edit selected text font family and size
- Apply color and stroke width to selected overlay items
- Apply fill color and opacity to selected overlay items
- Apply fill mode to selected shape items
- Apply bold and italic styling to selected text items
- Copy and paste selected overlay item selections
- Region editing tools: crop, blur, pixelate
- Basic annotation tools: pen, line, arrow, rectangle, ellipse, text
- Color and stroke width controls

Not yet ported:

- OCR/plugin parity with the C++ plugin system
- Native OS-global hotkey registration
- Effects beyond crop/blur/pixelate polish

Reference source trees now available locally:

- `libraries/kColorPicker`
- `libraries/kImageAnnotator`

These are being used as the behavioral reference for the PyQt6 reimplementation, not as direct Python runtime dependencies.

## Run

MX Linux 23 / Debian 12 note:

System Python is typically externally managed, so install optional OCR dependencies inside a virtual environment instead of using global `pip`.

```bash
sudo apt update
sudo apt install python3-venv python3-pip

cd /path/to/ksnip
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e .
ksnip-pyqt6
```

Or without installing:

```bash
python3 -m ksnip_py
```

And if you're not using a KDE operating system (like Kubuntu, MX Linux KDE, Neon, or others) and you want Ksnip to use the operating system's context menu, type this:

```bash
$ QT_QPA_PLATFORMTHEME=gtk3 python3 -m ksnip_py
```

an

## OCR

OCR in `ksnip_py/` is optional and experimental.

- The application still starts normally when PaddleOCR is not installed.
- The default OCR backend is `PaddleOCR`, but a script-based fallback backend is also available in Settings.
- If PaddleOCR is missing and you trigger OCR, the app shows an install hint instead of failing at startup.
- The `Spanish + English` setting uses PaddleOCR's `latin` model as the practical mixed-language fallback.

Install PaddleOCR only if you want OCR:

```bash
sudo apt update
sudo apt install python3-venv python3-pip

cd /path/to/ksnip
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install paddlepaddle paddleocr
```

Then reinstall or run the app from the same virtual environment:

```bash
pip install -e .
ksnip-pyqt6
```

Current OCR workflow:

- Saves the current image to a temporary PNG
- Runs OCR in a worker thread so the main window stays responsive
- Shows recognized text in a dialog with copy-to-clipboard support
- Can copy OCR text to the clipboard automatically if enabled in Settings

Current OCR limitations:

- Cancellation is best-effort. Once a backend call is actively running, it may not stop immediately.
- PaddleOCR was not installed in the validation environment used for the current smoke tests, so runtime verification covered the optional-import path and settings persistence, not live OCR recognition.
