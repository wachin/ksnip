# Windows OCR setup for ksnip-pyqt6

This guide is for the **packaged Windows build** (`ksnip-pyqt6.exe`). The
packaged application does not include a Python interpreter, so it cannot
install PaddleOCR into itself. Instead, install Python and PaddleOCR in a
separate environment and connect them to ksnip-pyqt6 through an **external OCR
script**.

> **Important — what Model Manager will show**
>
> In the packaged build, the **External OCR Script** card shows as installed
> once you set the script path. The **PaddleOCR** cards will still say
> *Not installed*, because the application cannot import packages from another
> Python installation. OCR still works: ksnip-pyqt6 runs your script, and the
> script uses the separate Python environment.
>
> If you want the PaddleOCR cards themselves to show as installed, run
> ksnip-pyqt6 from source in the same environment:
> `python -m ksnip_py`. The frozen `.exe` will not do that.

## Requirements

- Windows 10 or Windows 11, 64-bit.
- **Python 3.12.x, 64-bit**. Do not use Python 3.13: PaddlePaddle 3.3.1
  publishes Windows wheels for Python 3.12, not 3.13.
- About 2 GB of free disk space (Python, PaddlePaddle, dependencies and the
  first model download).
- An internet connection for the first OCR run, when PaddleOCR downloads its
  models.
- Microsoft Visual C++ Redistributable 2015–2022 (x64). Most Windows 10/11
  installations already have it; if Paddle fails with a missing `msvcp140.dll`,
  install it from Microsoft.

## 1. Install Python 3.12 with PATH

1. Open <https://www.python.org/downloads/windows/>.
2. Download **Python 3.12.x — Windows installer (64-bit)**.
3. Run the installer.
4. On the first page:
   - check **Add python.exe to PATH**;
   - optionally check **Install launcher for all users**;
   - click **Install Now**.
5. When it finishes, open a **new** PowerShell window (not the one that was
   already open) and verify:

```powershell
py -3.12 --version
python --version
```

Both should print a Python 3.12 version. If `python` opens the Microsoft Store
instead, see [Troubleshooting](#troubleshooting) and use `py -3.12` for the
rest of this guide.

## 2. Create a dedicated virtual environment

Use a folder under your user profile; it does not need administrator rights.

### PowerShell

```powershell
$root = Join-Path $env:LOCALAPPDATA "ksnip-pyqt6"
New-Item -ItemType Directory -Force -Path $root | Out-Null
py -3.12 -m venv (Join-Path $root "ocr-venv")
```

### Command Prompt (cmd.exe)

```bat
mkdir "%LOCALAPPDATA%\ksnip-pyqt6"
py -3.12 -m venv "%LOCALAPPDATA%\ksnip-pyqt6\ocr-venv"
```

From here on, use the virtual environment's Python directly. This avoids
PowerShell execution-policy problems and makes sure `pip` installs into the
right place.

```powershell
$py = "$env:LOCALAPPDATA\ksnip-pyqt6\ocr-venv\Scripts\python.exe"
& $py --version
```

In `cmd.exe`:

```bat
set "PY=%LOCALAPPDATA%\ksnip-pyqt6\ocr-venv\Scripts\python.exe"
"%PY%" --version
```

## 3. Install PaddleOCR and its dependencies

This downloads several hundred megabytes. Run it once and let it finish.

### PowerShell

```powershell
& $py -m pip install --upgrade pip
& $py -m pip install paddlepaddle==3.3.1 paddleocr==3.7.0 protobuf==3.20.2 "paddlex[ocr]==3.7.2" markdownify
```

### Command Prompt

```bat
"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install paddlepaddle==3.3.1 paddleocr==3.7.0 protobuf==3.20.2 "paddlex[ocr]==3.7.2" markdownify
```

If `pip` stops with `No matching distribution found for paddlepaddle`, confirm
that you are using **64-bit Python 3.12**:

```powershell
& $py -c "import platform, struct; print(platform.python_version(), platform.architecture(), struct.calcsize('P') * 8)"
```

The last number must be `64`.

## 4. Verify the installation

```powershell
& $py -c "import paddle; print('paddle', paddle.__version__)"
& $py -c "from paddleocr import PaddleOCR; print('paddleocr OK')"
```

If both commands succeed, the Python side is ready.

## 5. Create the OCR wrapper script

Save the following as:

```text
%LOCALAPPDATA%\ksnip-pyqt6\ksnip_ocr.py
```

```python
"""OCR wrapper for ksnip-pyqt6.

Receives one image path and writes the recognized text to stdout.
PaddleOCR's own progress and warning messages go to stderr.
"""

from __future__ import annotations

import sys

from paddleocr import PaddleOCR


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: ksnip_ocr.py IMAGE", file=sys.stderr)
        return 2

    image_path = sys.argv[1]

    # Use "es" for Spanish, "en" for English, and other PaddleOCR language
    # codes as needed.
    ocr = PaddleOCR(
        lang="en",
        enable_mkldnn=False,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )

    result = ocr.predict(image_path)
    lines: list[str] = []
    for item in result or []:
        rec_texts = getattr(item, "rec_texts", None)
        if rec_texts:
            lines.extend(str(text).strip() for text in rec_texts if str(text).strip())
            continue

        if isinstance(item, dict):
            texts = item.get("rec_texts")
            if texts:
                lines.extend(str(text).strip() for text in texts if str(text).strip())

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

You can create it with Notepad:

```powershell
notepad "$env:LOCALAPPDATA\ksnip-pyqt6\ksnip_ocr.py"
```

Paste the code, save, and close Notepad.

## 6. Create the Windows batch wrapper

Save the following as:

```text
%LOCALAPPDATA%\ksnip-pyqt6\ksnip_ocr.bat
```

```bat
@echo off
setlocal
set "VENV=%LOCALAPPDATA%\ksnip-pyqt6\ocr-venv"
"%VENV%\Scripts\python.exe" "%VENV%\ksnip_ocr.py" "%~1"
```

Test it from PowerShell with a real image:

```powershell
& "$env:LOCALAPPDATA\ksnip-pyqt6\ksnip_ocr.bat" "C:\path\to\your\image.png"
```

The first run downloads the PaddleOCR models (about 150 MB) and may take a
few minutes. Later runs use the cached models. The command should print the
recognized text.

If it prints nothing, run the Python wrapper directly to see the error:

```powershell
& "$env:LOCALAPPDATA\ksnip-pyqt6\ocr-venv\Scripts\python.exe" `
  "$env:LOCALAPPDATA\ksnip-pyqt6\ksnip_ocr.py" "C:\path\to\your\image.png"
```

## 7. Configure ksnip-pyqt6

1. Open ksnip-pyqt6.
2. Go to **Settings → OCR** (or **Options → Settings → OCR**).
3. Enable the OCR actions.
4. Set **Backend** to **Script**.
5. In **Script path**, browse to:

   ```text
   %LOCALAPPDATA%\ksnip-pyqt6\ksnip_ocr.bat
   ```

6. Close Settings.
7. Open an image and run the OCR action.

The application now runs:

```text
ksnip_ocr.bat "C:\path\to\image.png"
```

and reads the text from standard output. The batch file is routed through
`cmd.exe`, which is required on Windows for `.bat`/`.cmd` scripts.

## 8. What Model Manager will show

Open **Options → Model Manager…** after configuring the script:

- **External OCR Script** — shows as installed, because the configured path
  exists. This is the card that matches the setup in this guide.
- **PaddleOCR Line Models**, **PaddleOCR Structure**, **PaddleOCR Formula** —
  remain **Not installed** in the packaged build. The embedded Python cannot
  import the packages from `ocr-venv`. This is expected and does not prevent
  OCR from working through the script.
- **Spellcheck Dictionaries** — the packaged build disables this install too;
  Hunspell dictionaries are a separate component.

If you run ksnip-pyqt6 from source in the same virtual environment:

```powershell
& "$env:LOCALAPPDATA\ksnip-pyqt6\ocr-venv\Scripts\Activate.ps1"
python -m ksnip_py
```

then the PaddleOCR cards can detect the packages and show as installed, and the
in-process PaddleOCR backends also become available.

## Troubleshooting

### `python` is not recognized, or opens the Microsoft Store

- Reopen PowerShell after installing Python; PATH changes are only visible in
  new terminals.
- Use `py -3.12` instead of `python`.
- To stop the Store alias: **Settings → Apps → Advanced app settings → App
  execution aliases**, and turn off `python.exe` and `python3.exe`.

### `No matching distribution found for paddlepaddle`

- Confirm 64-bit Python 3.12, as shown in step 3.
- Make sure the command uses the virtual environment's `python.exe`, not a
  different Python.
- Python 3.13 is not supported by the PaddlePaddle 3.3.1 Windows wheel; create
  the venv with `py -3.12`.

### `DLL load failed` or `msvcp140.dll` is missing

Install **Microsoft Visual C++ Redistributable 2015–2022 (x64)** from
Microsoft, then reopen the terminal and retry.

### `pip` fails behind a corporate proxy

```powershell
& $py -m pip install --proxy http://user:password@proxy.example.com:8080 `
  paddlepaddle==3.3.1 paddleocr==3.7.0 protobuf==3.20.2 "paddlex[ocr]==3.7.2" markdownify
```

Ask your network administrator for the correct proxy address.

### PaddleOCR fails while loading `protobuf`

This environment is dedicated to OCR. Reinstall the pinned version:

```powershell
& $py -m pip install --force-reinstall protobuf==3.20.2
```

### The model download is slow or fails

The first OCR run downloads models from the internet. Check your connection and
proxy, then delete the cache and retry:

```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.paddlex" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:USERPROFILE\.paddleocr" -ErrorAction SilentlyContinue
```

### Antivirus warns about Paddle files

PaddlePaddle ships large native DLLs. If your antivirus flags them, scan the
files and, only if you trust the downloaded packages, add an exclusion for:

```text
%LOCALAPPDATA%\ksnip-pyqt6\ocr-venv
```

Do not disable antivirus globally.

### OCR returns empty text

- Test the wrapper directly with the same image (step 6).
- Make sure the image is a supported format (PNG, JPEG, BMP, WebP).
- Try a different model language (`lang="en"` or `lang="es"`).
- Check that the image path contains no unquoted special characters; the batch
  file quotes `%~1`.

## Uninstall

1. In ksnip-pyqt6, clear the script path under **Settings → OCR**.
2. Delete the environment and model caches:

```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\ksnip-pyqt6\ocr-venv"
Remove-Item -Recurse -Force "$env:USERPROFILE\.paddlex"
Remove-Item -Recurse -Force "$env:USERPROFILE\.paddleocr"
```

3. Uninstall Python 3.12 if you no longer need it.

## Security notes

- An external OCR script runs with your user permissions. Only configure a
  script you created or reviewed.
- PaddleOCR downloads models from its official sources. Keep the default
  sources and verify your network if downloads fail.
- The packaged application does not install anything silently; this setup is
  explicit and lives under your user profile.
