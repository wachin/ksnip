#!/usr/bin/env bash
# Build the macOS portable application with PyInstaller.
#
# PyInstaller --windowed creates the .app bundle itself. Do not assemble the
# bundle by hand on top of the onedir output: the executable inside
# Contents/MacOS is the program, and replacing it with a launcher script makes
# the bundle exec itself forever.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

VERSION="${VERSION:-$(python3 packaging/scripts/get_version.py)}"
MACOS_ARCH="${MACOS_ARCH:-$(uname -m)}"
BUILD="$ROOT/build/macos"
DIST="$ROOT/dist"
APP="$DIST/ksnip-pyqt6.app"
ZIP="$DIST/ksnip-pyqt6-${VERSION}-macOS-${MACOS_ARCH}.zip"

rm -rf "$BUILD" "$APP" "$ZIP"
mkdir -p "$BUILD" "$DIST"

echo "Building ksnip-pyqt6 $VERSION for macOS $MACOS_ARCH"

# Build the .icns from the 1024 px source with the tools macOS ships.
ICONSET="$BUILD/ksnip.iconset"
mkdir -p "$ICONSET"
for size in 16 32 128 256 512; do
  sips -z "$size" "$size" packaging/macos/ksnip-1024.png \
    --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
  double=$((size * 2))
  sips -z "$double" "$double" packaging/macos/ksnip-1024.png \
    --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$BUILD/ksnip.icns"

python3 -m PyInstaller \
  --noconfirm --clean --onedir --windowed \
  --name ksnip-pyqt6 \
  --osx-bundle-identifier org.ksnip.ksnip-pyqt6 \
  --icon "$BUILD/ksnip.icns" \
  --distpath "$DIST" \
  --workpath "$BUILD/work" \
  --specpath "$BUILD" \
  --add-data "$ROOT/ksnip_py/icons:ksnip_py/icons" \
  --add-data "$ROOT/ksnip_py/stickers:ksnip_py/stickers" \
  --add-data "$ROOT/ksnip_py/translations:ksnip_py/translations" \
  --add-data "$ROOT/ksnip_py/licenses:ksnip_py/licenses" \
  --hidden-import PyQt6.QtCore \
  --hidden-import PyQt6.QtGui \
  --hidden-import PyQt6.QtWidgets \
  --hidden-import PyQt6.QtNetwork \
  --hidden-import PyQt6.QtPrintSupport \
  --hidden-import PyQt6.QtSvg \
  --hidden-import PyQt6.QtSvgWidgets \
  --exclude-module PyQt6.QtDBus \
  --exclude-module paddleocr \
  --exclude-module paddlepaddle \
  --exclude-module paddlex \
  --exclude-module modelscope \
  --exclude-module markdownify \
  "$ROOT/run_ksnip.py"

# Verify the bundle, then run the binary itself. --version exits before any
# QApplication is constructed, so this needs no display.
test -d "$APP"
plutil -lint "$APP/Contents/Info.plist"
test -x "$APP/Contents/MacOS/ksnip-pyqt6"
QT_QPA_PLATFORM=offscreen "$APP/Contents/MacOS/ksnip-pyqt6" --version

# --keepParent keeps ksnip-pyqt6.app as the single top-level entry. Without
# it the archive unpacks Contents/ into the current directory.
ditto -c -k --sequesterRsrc --keepParent "$APP" "$ZIP"
unzip -l "$ZIP" | grep -q "ksnip-pyqt6.app/Contents/MacOS/ksnip-pyqt6"

echo "Created $ZIP"
