# Tray, modeless windows, OCR, uploader, and watermark parity audit

## Scope

This is a read-only comparison between the current PyQt6 port and the C++
implementation. No tray, pin-window, OCR, uploader, watermark, settings, or
window-lifecycle code was changed during this audit.

Differences marked **Decision required** must not be implemented merely to
match C++. They affect workflow, external services, dependencies, security, or
existing customized behavior and require approval first.

## Summary matrix

| Area | C++ implementation | PyQt6 implementation | Status |
| --- | --- | --- | --- |
| Tray availability | `QSystemTrayIcon`, enabled from config | Checks `QSystemTrayIcon.isSystemTrayAvailable()` and applies `tray/use` | Core parity |
| Tray capture actions | Every supported capture mode | Rect, last rect, full, current, active, under cursor, and portal | Complete |
| Tray file/actions | Open, Save, Paste, Copy, Upload, configurable Actions submenu, Quit | Open, Save, Paste, Copy, Upload, OCR, Quit | Partial: configurable Actions submenu is pending |
| Tray default activation | Show editor or configured capture mode | Same, including all Python capture modes | Complete |
| Tray lifecycle | Start/minimize/close to tray | Same settings and guarded quit behavior | Complete |
| Tray notifications | Information/warning/critical; upload URL can open its parent/content | Informational minimize/close messages; normal dialogs/status for most operations | Partial |
| Pin windows | Multiple modeless always-on-top windows | Multiple frameless always-on-top tool windows | Near parity |
| Pin interaction | Move, wheel scale, Escape/double-click close, close one/other/all, hover shadow | Same interaction set | Near parity; focused tests still needed |
| OCR processing | Plugin-driven concurrent task per modeless OCR window | Optional PaddleOCR or script worker in one `QThread` | Customized/experimental |
| OCR windows | Multiple simultaneous editable modeless result windows | One operation at a time, window-modal progress, then modal editable result dialog | **Decision required** |
| OCR cancellation | Window lifecycle around concurrent plugin work | Cooperative flag before/after backend call; cannot interrupt a blocking Paddle/script call | Partial |
| Script uploader | Asynchronous `QProcess`, temporary image, output filter, optional stderr failure/copy | Temporary PNG, output filter, optional stderr failure/copy through `subprocess.run` | Functional but synchronous |
| Imgur uploader | Native HTTP implementation and result URL handling | Settings placeholder only | Missing, **decision required** |
| FTP uploader | Native FTP implementation and settings | Settings placeholder only | Missing, **decision required** |
| Watermark storage | Configured image loaded for insertion | PNG stored under Qt `AppDataLocation` | Complete equivalent workflow |
| Watermark preparation | 15% opacity, optional 45° rotation, fit to capture | Same | Complete |
| Watermark placement | Random position inside capture | Same bounded random placement | Complete |
| Watermark editing | Inserted as kImageAnnotator image item | Inserted as editable Python `Image` overlay with undo | Complete |

## System tray details

The Python tray menu contains the complete capture set and the essential file
actions. Its configured default action matches C++: any non-context activation
either restores the editor or triggers the selected capture action. Tray use,
minimize, close, startup-minimized, notifications, default action, and default
capture mode are persisted.

Known differences:

1. C++ inserts the configurable **Actions** submenu. Python does not yet have
   the corresponding action/plugin system, so inventing this menu in isolation
   would create nonfunctional entries.
2. C++ notifications may retain a content URL and open it when the notification
   is clicked. Python currently uses tray messages for lifecycle notices and
   dialogs/status messages for upload results; it does not maintain a clickable
   notification URL.
3. Warning and critical tray-notification routing is not centralized behind a
   notification service in the port.

These differences should be addressed together with `Settings > Actions` and
the uploader decision, not as independent tray patches.

## Modeless windows

### Pin Window

`PinWindow` is a faithful Python counterpart: it is frameless, always on top,
modeless, movable, smoothly resizable with the wheel, closable by Escape or
double click, and supports Close, Close Other, and Close All. `MainWindow`
retains the live windows and removes destroyed instances.

No behavioral change is recommended from this audit. Characterization tests
for window flags, scale limits, and close-one/other/all lifecycle would be safe.

### OCR result window

The C++ modeless handler can own multiple OCR windows concurrently. Each starts
plugin recognition and later replaces its progress indicator with editable
text. The Python port intentionally has a different experimental workflow:

- only one OCR job is accepted at a time;
- work is moved to a `QThread`;
- a window-modal progress dialog is shown;
- the editable result is displayed with `exec()` in a modal dialog;
- optional automatic clipboard copy and a manual Copy button are provided.

Changing this to multiple modeless windows affects ownership, cancellation,
shutdown, resource usage, and result management. It therefore requires an
explicit product decision and lifecycle tests before implementation.

The present cancel action is cooperative. It can prevent work before the
backend starts, but `subprocess.run()` and PaddleOCR recognition are blocking
calls and are not interrupted once running.

## Uploaders

### Script uploader

The functional surface is close to C++:

- validate the configured executable;
- save a temporary PNG;
- pass its path as the script argument;
- capture standard output/error;
- optionally fail when stderr is nonempty;
- optionally extract output with a regular expression;
- optionally copy successful output to the clipboard;
- remove the temporary file.

The architectural difference is important: C++ uses asynchronous `QProcess`,
whereas Python calls synchronous `subprocess.run()` from the GUI action. A slow
upload script can freeze the interface and cannot be canceled. Moving it to a
worker is a contained future improvement, but still changes observable
lifecycle and needs approval plus tests.

### Native Imgur and FTP

Both are implemented in C++ but remain explicit disabled placeholders in the
Python settings. Adding them introduces network behavior, credentials or API
policy, error handling, privacy implications, and Debian dependency/security
review. The roadmap correctly treats each as a decision rather than automatic
porting work.

## Watermark

Watermark preparation matches the C++ constants and sequence: optional smooth
45-degree rotation, rendering at 15% opacity, proportional downscaling only
when it exceeds the canvas, and a random valid position. The result is inserted
as an editable image overlay, so move, resize, shadow, opacity, serialization,
SVG embedding, and undo follow the normal image-item workflow.

Python stores the chosen source as `watermark_image.png` in Qt's writable
application-data directory instead of depending on a fixed system path. This is
a portable implementation detail, not a parity defect.

## Safe next steps

Without changing behavior, the following characterization tests can be added:

1. tray default-action routing and visibility predicates;
2. Pin Window flags, scaling lower bound, and close-one/other/all bookkeeping;
3. script-uploader success, regex fallback, stderr policy, nonzero exit, and
   temporary-file cleanup using local test scripts;
4. watermark opacity/rotation/fit bounds and random-position bounds;
5. OCR backend extraction/error mapping and worker signals with fake backends.

Behavioral proposals requiring approval are, in priority order:

1. asynchronous/cancelable script uploading;
2. modeless OCR result lifecycle;
3. native Imgur support or an explicit decision not to include it;
4. native FTP support or an explicit decision not to include it;
5. configurable Actions and clickable tray-notification content.
