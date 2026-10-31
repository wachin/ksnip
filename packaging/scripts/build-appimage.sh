#!/usr/bin/env bash
# Build the Linux AppImage: PyInstaller onedir payload + manually assembled AppDir.
#
# Run from anywhere. The finished AppImage is written to dist/. Build on the
# oldest Ubuntu still supported so the linked glibc is the oldest that runs it.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

VERSION="${VERSION:-$(python3 packaging/scripts/get_version.py)}"
ARCH="${ARCH:-x86_64}"
APP_ID="org.ksnip.ksnip-pyqt6"
BUILD="$ROOT/build/appimage"
APPDIR="$BUILD/ksnip-pyqt6.AppDir"
DIST="$BUILD/dist"
OUT="$ROOT/dist"

# Pin a versioned appimagetool release: the "continuous" asset is republished
# and invalidates its checksum without warning.
APPIMAGETOOL_VERSION="1.9.1"
APPIMAGETOOL_SHA256="ed4ce84f0d9caff66f50bcca6ff6f35aae54ce8135408b3fa33abfc3cb384eb0"
APPIMAGETOOL="$BUILD/appimagetool"

rm -rf "$BUILD"
mkdir -p "$DIST" "$OUT" \
  "$APPDIR/usr/bin" \
  "$APPDIR/usr/share/applications" \
  "$APPDIR/usr/share/icons/hicolor/256x256/apps" \
  "$APPDIR/usr/share/icons/hicolor/scalable/apps" \
  "$APPDIR/usr/share/metainfo"

echo "Building ksnip-pyqt6 $VERSION for $ARCH"

# 1. Payload ---------------------------------------------------------------
# --add-data destinations must match how the package resolves its data:
# modules use Path(__file__).parent, which is <dist>/_internal/ksnip_py.
python3 -m PyInstaller \
  --noconfirm --clean --onedir \
  --name ksnip-pyqt6 \
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
  --exclude-module paddleocr \
  --exclude-module paddlepaddle \
  --exclude-module paddlex \
  --exclude-module modelscope \
  --exclude-module markdownify \
  "$ROOT/run_ksnip.py"

test -x "$DIST/ksnip-pyqt6/ksnip-pyqt6"
cp -a "$DIST/ksnip-pyqt6/." "$APPDIR/usr/bin/"

# 2. Desktop integration ---------------------------------------------------
install -Dm644 "debian/$APP_ID.desktop" "$APPDIR/$APP_ID.desktop"
install -Dm644 "debian/$APP_ID.desktop" "$APPDIR/usr/share/applications/$APP_ID.desktop"
install -Dm644 "debian/$APP_ID.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/$APP_ID.svg"
install -Dm644 "debian/$APP_ID.metainfo.xml" "$APPDIR/usr/share/metainfo/$APP_ID.metainfo.xml"
# appimagetool 1.9.1 looks for the older .appdata.xml suffix.
install -Dm644 "debian/$APP_ID.metainfo.xml" "$APPDIR/usr/share/metainfo/$APP_ID.appdata.xml"

# The icon at the AppDir root must be named after the desktop Icon= key.
if command -v rsvg-convert >/dev/null 2>&1; then
  rsvg-convert -w 256 -h 256 "debian/$APP_ID.svg" -o "$APPDIR/$APP_ID.png"
elif command -v magick >/dev/null 2>&1; then
  magick -background none "debian/$APP_ID.svg" -resize 256x256 "$APPDIR/$APP_ID.png"
else
  echo "rsvg-convert or ImageMagick is required to render the AppImage icon" >&2
  exit 1
fi
install -Dm644 "$APPDIR/$APP_ID.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/$APP_ID.png"

# 3. AppRun ---------------------------------------------------------------
# The mount point changes every run, so AppRun resolves its own directory.
cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
set -eu
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/ksnip-pyqt6" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# 4. appimagetool ----------------------------------------------------------
curl -fsSL -o "$APPIMAGETOOL" \
  "https://github.com/AppImage/appimagetool/releases/download/${APPIMAGETOOL_VERSION}/appimagetool-${ARCH}.AppImage"
echo "${APPIMAGETOOL_SHA256}  ${APPIMAGETOOL}" | sha256sum -c -
chmod +x "$APPIMAGETOOL"

APPIMAGE="$OUT/ksnip-pyqt6-${VERSION}-${ARCH}.AppImage"
ARCH="$ARCH" "$APPIMAGETOOL" --appimage-extract-and-run "$APPDIR" "$APPIMAGE"

# 5. Verify the finished file, not just the exit status -------------------
test -s "$APPIMAGE"
chmod +x "$APPIMAGE"
(
  cd "$BUILD"
  rm -rf squashfs-root
  "$APPIMAGE" --appimage-extract >/dev/null
  test -x squashfs-root/usr/bin/ksnip-pyqt6
  test -f squashfs-root/usr/bin/_internal/ksnip_py/icons/ksnip.svg
  test -f "squashfs-root/usr/share/applications/$APP_ID.desktop"
  test -f "squashfs-root/$APP_ID.png"
  rm -rf squashfs-root
)

echo "Created $APPIMAGE"
