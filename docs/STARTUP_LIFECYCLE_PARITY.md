# Startup, single-instance, and shutdown parity

This matrix compares the C++ bootstrap path (`src/main.cpp`,
`StandAloneBootstrapper`, the single-instance bootstrappers, and
`MainWindow.cpp`) with `ksnip_py/app.py`, `single_instance.py`, and
`main_window.py`.

| Behavior | C++ reference | PyQt6 status |
|---|---|---|
| QApplication identity and version | Configured before bootstrap | Complete; Python uses its own package/application identity. |
| High-DPI support | Explicit Qt5-era attributes | Complete through Qt6's default high-DPI behavior. |
| Quit when last window closes | Disabled to support tray operation | Complete; tray-aware close handling keeps the process alive. |
| Start without arguments | Create window, then apply capture-on-startup/start-minimized settings | Complete. |
| Edit image path | Validate/load and open editor | Complete, including `.ksnip` projects. |
| Edit image from stdin | Transfer bytes and open editor | Complete, including IPC transfer. |
| Capture requested by CLI | Capture selected mode and open editor | Complete. |
| Direct save/upload | Process capture without showing editor | Complete; Python additionally supports save and upload together. |
| Capture-on-startup | Use configured default capture mode | Complete. |
| Start minimized to tray | Hide only when a visible tray is available | Complete. |
| Restore geometry | Validate and restore persisted window state | Complete through Qt geometry restoration. |
| Single-instance election | Shared-memory lock plus local IPC | Equivalent local-socket election with stale-endpoint recovery. |
| Simultaneous startup race | Lock selects exactly one server | Corrected: a contender now probes a failed endpoint and never removes a live server; the losing process retries forwarding and exits. |
| Empty secondary invocation | Raise/show existing editor | Complete. |
| Secondary edit request | Open image in existing editor and show it | Complete. |
| Secondary capture request | Capture without forcing a hidden editor to the foreground | Corrected to match C++ behavior. |
| Secondary direct save/upload | Process in primary without terminating primary | Complete Python extension. |
| Close with tray enabled | Hide instead of exiting | Complete. |
| Explicit Quit with unsaved content | Exit only after close confirmation succeeds | Corrected: cancel now retains the process and tray icon. |
| Minimize to tray | Hide on minimize when configured | Complete. |
| Session-manager shutdown | Dedicated `commitDataRequest` path | Not yet ported; retained as an explicit remaining difference. |

## Intentional differences

- Qt6 enables high-DPI scaling by default, so the removed Qt5 application
  attributes should not be copied into PyQt6.
- The Python IPC protocol is length-delimited JSON plus optional base64 image
  bytes rather than the C++ delimiter format. It preserves the same public
  startup operations and safely transports arbitrary Unicode arguments.
- Python can process remote `--save` and `--upload` requests in the primary
  process without closing that long-running instance.

## Automated coverage

`tests_py/test_startup_lifecycle.py` verifies remote show/capture policy,
single-instance endpoint ownership, canceled explicit quit, and confirmed
quit. CLI request mapping remains covered by `tests_py/test_app_cli.py`.

## Remaining bounded work

The only startup/shutdown behavior from this audit that remains deliberately
open is desktop session-manager shutdown (`QGuiApplication.commitDataRequest`).
It should be implemented together with a non-interactive policy for unsaved
tabs rather than by displaying a modal prompt during logout.
