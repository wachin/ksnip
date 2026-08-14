# Global hotkeys on X11 and Wayland

## Audit result

The current PyQt6 settings used the labels **Global HotKeys** and **Enable
Global HotKeys**, but the corresponding `QAction` objects use
`Qt.ApplicationShortcut`. Those key sequences are application-wide, not
desktop-wide: they work in any ksnip window, but not while another application
has keyboard focus. The settings labels now describe their real scope.

The original C++ implementation registers native keys with `XGrabKey` on X11
and a Windows-specific API. Its `WaylandConfig` deliberately makes global
hotkeys read-only and disabled, so native Wayland support is not functionality
that can simply be translated from the existing C++ source.

Wayland now has the
[`GlobalShortcuts` portal](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.GlobalShortcuts.html),
but an application must create a portal session, request user-approved
bindings, keep the session alive, and handle backend availability. Support and
desktop integration still depend on the compositor and portal backend. An X11
`XGrabKey` implementation would therefore create a second configuration path
without solving the cross-desktop requirement.

## Portable method available now

ksnip_py already has a single-instance command-line protocol. A desktop or
window-manager shortcut can launch any command below; if ksnip is already
running, the request is forwarded to that process:

```text
ksnip-pyqt6 --rectarea
ksnip-pyqt6 --lastrectarea
ksnip-pyqt6 --fullscreen
ksnip-pyqt6 --current
ksnip-pyqt6 --active
ksnip-pyqt6 --windowundercursor
ksnip-pyqt6 --portal
```

This works with desktop keyboard-shortcut settings and with lightweight window
managers such as Fluxbox, Openbox, and IceWM. It also lets the compositor own
the key binding on Wayland, which is the reliable security model there.

Example Openbox binding:

```xml
<keybind key="A-S-r">
  <action name="Execute">
    <command>ksnip-pyqt6 --rectarea</command>
  </action>
</keybind>
```

## Future native implementation criteria

A built-in backend remains a valid future enhancement, but it should be added
only when all of the following are covered:

1. X11 registration reports key conflicts instead of failing silently.
2. Wayland uses the official `GlobalShortcuts` portal and exposes consent or
   backend failures clearly.
3. Registrations are rebuilt safely after settings changes and released during
   shutdown.
4. Application shortcuts and desktop-wide bindings have separate settings.
5. Automated unit tests cover parsing and lifecycle, followed by live tests on
   X11 and at least Plasma and GNOME Wayland sessions.

Until then, desktop-managed CLI bindings are the maintained cross-platform
fallback rather than an unsafe or misleading partial native implementation.
