# Qt6 file dialogs, Unicode bookmarks, and translations

## Backend diagnosis

`ksnip_py` calls the normal Qt file-dialog API and does not globally request
`QFileDialog::DontUseNativeDialog`. Qt is therefore free to select a native
platform helper when the active QPA platform theme provides one.

On the Debian 13 / AV Linux MXe test system, Qt 6.8.2 with the `qt6ct` platform
theme produced the Qt Widgets dialog for both the default configuration and an
explicit `DontUseNativeDialog` test. Both dialogs exposed a widget layout and
the same internal list/tree views. Consequently, forcing
`DontUseNativeDialog` does not fix the reported problem on this system: the
observed sidebar is already Qt's widget sidebar.

GTK bookmarks were inspected separately in `~/.config/gtk-3.0/bookmarks` and
contained valid UTF-8 percent-encoded URLs such as
`file:///home/user/Im%C3%A1genes`. They are not modified by ksnip_py. A genuine
GTK, KDE, Windows, or macOS native dialog remains responsible for its own
platform bookmark store.

## Cause and correction

The Qt Widgets implementation persists its sidebar in the organization-only
`QSettings(QSettings::UserScope, "QtProject")` store, group `FileDialog`, not
in ksnip_py's settings. Qt writes `sidebarUrls()` through
`QUrl::toStringList()`, whose default representation is human-readable and can
contain literal Unicode characters. It reconstructs the list on the next run
with `QUrl::fromStringList()`.

The paths themselves are valid: `QUrl.fromLocalFile(path)` produces the
correct UTF-8 percent-encoded URL and `QUrl.toLocalFile()` returns the original
Unicode path. No Python byte encoding or URL quoting is needed.

`ksnip_py.file_dialogs` now wraps every open/save helper and normalizes Qt's
own `shortcuts`, `history`, and `lastVisited` values before and after a dialog.
Each value is parsed as a `QUrl`, local URLs are reconstructed with
`QUrl.fromLocalFile()`, and persistence uses Qt's `FullyEncoded` formatting.
Thus the INI boundary is ASCII-only (`Im%C3%A1genes`) while Qt still exposes the
original `/home/user/Imágenes` path. The selected file paths remain ordinary
Python `str` values throughout the application.

This normalization does not enable `DontUseNativeDialog`, replace native
bookmarks, or assume that all platforms use the same dialog implementation.

## Standard Qt translations

Application catalogs (`ksnip_*.qm` and `ksnip_py_*.qm`) translate ksnip
content. Standard widget text belongs to Qt's `qtbase_*.qm` catalogs.

At startup, ksnip_py now loads `qtbase` for the selected application locale
before installing its own translators. The primary directory is obtained from
`QLibraryInfo.path(QLibraryInfo.TranslationsPath)` (or `paths()` where
available). This follows the Qt runtime actually imported by PyQt6, including
PyQt6 installed with pip and Qt deployments on Windows or macOS.

On Linux only, XDG data directories are checked as a fallback for
`qt6/translations` and `qt/translations`. Debian and Ubuntu provide these
catalogs in `qt6-translations-l10n`. Windows and macOS do not use that Debian
package; their application/runtime bundle must include the desired
`qtbase_<locale>.qm` files in the translation path reported by Qt.
