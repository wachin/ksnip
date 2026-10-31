# Packaging for ksnip-pyqt6

All release artifacts are built by GitHub Actions. Nothing in this document is
meant to be run on a developer machine to produce a release; local runs are for
checking the pipeline before pushing a tag.

## Artifacts

| Platform | Artifact | Built with | Runner |
|---|---|---|---|
| Ubuntu / Debian | `ksnip-pyqt6_<version>-1_all.deb` | debhelper + pybuild | `ubuntu-24.04` |
| Ubuntu / Debian | `ksnip-pyqt6-<version>-x86_64.AppImage` | PyInstaller onedir + appimagetool 1.9.1 | `ubuntu-22.04` |
| macOS (Intel) | `ksnip-pyqt6-<version>-macOS-x86_64.zip` (contains `.app`) | PyInstaller `--windowed` + `ditto` | `macos-15-intel` |
| Windows 10/11 | `ksnip-pyqt6-<version>-Windows-x64-portable.zip` | Nuitka `--standalone` | `windows-2025` |
| Windows 10/11 | `ksnip-pyqt6-<version>-Windows-x64-setup.exe` | Nuitka + NSIS (per-user) | `windows-2025` |

The workflow only builds and uploads artifacts. It never creates a release and
never writes to the repository, so a run can be inspected and scanned before
anything becomes public.

## How a release is produced

The workflow is `.github/workflows/build.yml`. It runs on `workflow_dispatch`
and on any `v*` tag push, and stops once the five artifacts are uploaded.

1. Start a run (Actions → *Build packages* → *Run workflow*), or push a tag.
2. Download the artifacts from the run page.
3. Create or edit the GitHub release and attach the files by hand.

The version in `pyproject.toml` is used for workflow-dispatch runs. Tag runs use
the tag without its leading `v`, so the tag and the package version stay in step.
The `.deb` is the exception: `dpkg-buildpackage` reads its version from
`debian/changelog`. Bump `debian/changelog` and `pyproject.toml` together before
tagging, or the `.deb` will carry the previous version.

## What each job verifies

A green build is not proof that the artifact is usable, so every job checks its
own output:

- **Debian**: builds with `dpkg-buildpackage`, runs `lintian --fail-on error`,
  checks that `/usr/bin/ksnip-pyqt6` is in the archive, installs the `.deb`, and
  runs `ksnip-pyqt6 --version` plus an import smoke test.
- **AppImage**: builds the AppDir, extracts the finished AppImage and checks the
  executable, `_internal/ksnip_py/icons/ksnip.svg`, the desktop file and the
  icon, then runs `--appimage-extract-and-run --version`.
- **macOS**: lints `Info.plist`, checks the bundle executable, runs it with
  `--version`, and verifies that the ZIP contains the `.app` as its top-level
  entry.
- **Windows portable**: checks that the ZIP has forward-slash entry names and
  contains `ksnip-pyqt6.exe` and `COPYING` under one top-level folder.
- **Windows installer**: silently installs, runs the installed executable with
  `--version`, then uninstalls.

## Toolchain decisions

- **Linux and macOS payloads use PyInstaller onedir.** Onefile is deliberately
  avoided: it extracts to a temporary directory on every start and is the shape
  that produces most antivirus false positives on Windows.
- **Windows uses Nuitka `--standalone`.** The packaging research measured
  0/71 detections for a Nuitka standalone build against 3/73 for PyInstaller
  builds of the same application. No UPX or other packer is used.
- **The AppImage uses a pinned appimagetool release** (`1.9.1`) with a checksum.
  The `continuous` asset is republished and invalidates its checksum.
- **The AppImage is built on Ubuntu 22.04** so its glibc baseline is older than
  the distributions it is expected to run on.
- **The Windows installer is per-user** (`RequestExecutionLevel user`) and does
  not prompt for UAC.
- **The NSIS installer uses `SetCompressor ZLIB`**, the same setting as the
  reference project that measured 0/68 detections on its installer. Solid LZMA
  squeezed the 94 MB payload into a single opaque 34.7 MB block; ZLIB costs
  about 9 MB and keeps the payload file-oriented, which is the shape ML
  heuristics score less aggressively.
- **The macOS bundle is unsigned.** Gatekeeper will warn on first launch; the
  user has to right-click the application and choose Open. Signing and
  notarization need an Apple Developer certificate and are not configured here.
- **The macOS artifact is built on `macos-15-intel`.** PyQt6 6.12 publishes a
  `macosx_14_0` universal2 wheel, so the Intel build targets macOS 14 and newer.
  Building for an older macOS requires pinning an older PyQt6 release.

## Debian policy notes

- The package is `Architecture: all`; it ships Python sources and depends on the
  distribution Qt bindings (`python3-pyqt6`, `python3-pyqt6.qtsvg`) instead of
  embedding a second copy of Qt.
- `lintian --fail-on error` gates the build. Warnings are reported but do not
  fail it.
- The `[project]` metadata has to stay parseable by the setuptools that ships
  with the build distribution, not by the newest one on PyPI. Ubuntu 24.04 has
  setuptools 68.1.2, which predates PEP 639, so `license` uses the
  `{text = "..."}` table and `license-files` lives under `[tool.setuptools]`.
  The SPDX string form fails the pybuild wheel step with
  `configuration error: 'project.license' must be valid exactly by one
  definition`. Newer setuptools accepts both and only warns about the table.
- OCR and the PaddlePaddle runtime are **not** bundled. They are hundreds of
  megabytes of ML code and models, and Debian policy does not favour embedding
  them in a desktop package. See the limitation below.

## OCR in the frozen builds

The installers do not include PaddleOCR, PaddlePaddle or PaddleX. The in-app
Model Manager installs those packages with `pip`, which requires a real Python
interpreter. In a frozen build `sys.executable` is the frozen application, so
that install path does not work. OCR is therefore not available out of the box
  in any artifact. The `.deb` can use a PaddleOCR runtime installed system-wide;
  the frozen artifacts cannot install one.

Bundling OCR would make every artifact several hundred megabytes larger and
would add a large native runtime to the Windows build, which is exactly the
kind of payload that attracts heuristic antivirus detections. If OCR must ship
in the frozen builds, it should be a separate, explicitly tested decision.

## Antivirus expectations

The Nuitka choice follows two measured projects, not a guarantee. The research
records 0/71 for one Nuitka standalone build and 0/68 for one Nuitka + NSIS
installer; those are two applications on one platform. A different build can
still be flagged. Do not respond to a false positive by obfuscating, packing or
mutating the binary; report it to the vendor.

## Running a build locally

These commands reproduce what CI does. They are for validation only.

```bash
# Debian package
sudo apt-get install -y build-essential debhelper dh-python \
  pybuild-plugin-pyproject python3-all python3-setuptools python3-wheel \
  python3-build python3-installer lintian
dpkg-buildpackage -us -uc -b
lintian --fail-on error ../ksnip-pyqt6_*.deb

# AppImage
python -m pip install "pyinstaller>=6.10,<7"
python -m pip install -r requirements.txt
bash packaging/scripts/build-appimage.sh

# macOS (run on macOS)
python -m pip install "pyinstaller>=6.10,<7"
python -m pip install -r requirements.txt
bash packaging/scripts/build-macos-app.sh

# Windows portable (run in PowerShell)
python -m pip install -r requirements.txt "nuitka>=2.6,<3" ordered-set zstandard
powershell -ExecutionPolicy Bypass -File packaging/scripts/build-windows-portable.ps1 -Version 0.1.1
```

The entry point for both freezers is `run_ksnip.py`. `ksnip_py/app.py` uses
relative imports and cannot be used directly as a top-level freezer script.
