# Capture backend parity audit

This document records the PyQt6 capture paths compared with the C++ ksnip
implementation. It separates implemented behavior from checks that still need
to be performed in real X11 and Wayland sessions.

| Capture path | PyQt6 implementation | Current status |
| --- | --- | --- |
| X11 full desktop | Composes all `QScreen.grabWindow(0)` results using their virtual geometries | Implemented |
| X11 current screen | Uses the screen under `QCursor.pos()`, falling back to the primary screen | Implemented |
| X11 active window | Resolves `_NET_ACTIVE_WINDOW` and captures the X11 window | Implemented |
| X11 window under cursor | Resolves the X11 child window beneath the pointer | Implemented |
| X11 cursor | Reads XFixes cursor pixels and inserts them as an editable image item | Implemented, optional fallback |
| Wayland | Automatically redirects normal actions to the screenshot portal | Implemented |
| Generic portal | Calls `org.freedesktop.portal.Screenshot`, handles success, cancellation, errors and a 120-second timeout | Implemented |
| Portal full screen | Sends `interactive=false` | Implemented |
| Other portal modes | Sends `interactive=true`; the compositor/portal owns the chooser | Implemented |

## Generic Wayland scaling

The C++ `WaylandImageGrabber::createPixmapFromPath()` loads the returned image
and, when the setting is enabled, assigns `HdpiScaler::scaleFactor()` as its
device pixel ratio. Under Qt 6 that factor is the primary screen DPR.

The PyQt6 port now has the same explicit, tested rule. It changes only Qt's
high-DPI metadata with `QPixmap.setDevicePixelRatio()`; it does not resize or
resample the screenshot. Tests verify that the physical pixel dimensions stay
unchanged and the device-independent size reflects fractional DPR values.

The screenshot portal response contains an image URI but no source-monitor
identifier. Consequently neither implementation can infer the selected
monitor's DPR reliably in a mixed-DPI setup. Using the primary screen is an
intentional compatibility rule, not a claim that the portal selected it. Users
should leave scaling disabled if their portal already returns the desired
logical sizing or if primary-screen scaling is unsuitable.

Portal result locations are converted through `QUrl.toLocalFile()`. This
correctly handles percent-encoded Unicode paths without manual UTF-8,
quoting, or unquoting code.

## Remaining live validation

Automated tests cover routing helpers, URI conversion and DPR semantics, but a
headless test runner cannot validate compositor-owned dialogs or X11 server
properties. Before declaring complete backend parity, run the capture matrix on
Debian 13/MX Linux 25 in at least one X11 session and one Wayland session, and
include a fractional/mixed-DPI Wayland check when suitable hardware is
available.
