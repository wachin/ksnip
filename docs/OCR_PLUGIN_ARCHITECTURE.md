# OCR plugin architecture

Status: core discovery implemented in 0.2.2-3; the optional plugin and managed
environment are being implemented in the separate `ksnip-pyqt6-ocr` repository.

This document describes the planned separation of ksnip-pyqt6's optional OCR
support into an independent plugin package. It explains the technical design,
the packaging split, and why the project is deliberately moving away from
shipping a PaddleOCR installer in the core Debian package.

## 1. Goals

The design has four goals:

1. Keep the core `ksnip-pyqt6` package self-contained and suitable for Debian
   main.
2. Keep PaddlePaddle, PaddleOCR, `pip`, and virtual-environment management out
   of the core application and its Debian binary package.
3. Keep the convenient “install OCR from the Model Manager” workflow available
   for users who install the upstream GitHub package.
4. Make the optional OCR implementation independently versioned, installable,
   and removable.

The core application must remain fully usable when the OCR plugin is not
installed.

## 2. Why a plugin instead of a submodule

A Git submodule such as `libs/ksnip_py_ocr/` would couple the OCR code to the
core source tree. That creates several problems:

- Debian source packages must build offline. A build cannot run
  `git submodule update` or fetch a network dependency.
- The Debian source tarball would need to carry the plugin code, licensing, and
  metadata even when the Debian package does not ship OCR.
- The plugin would not have an independent release cycle.
- A broken or unavailable plugin could affect the core build.
- The core tree would still contain Paddle-specific code, even if disabled at
  build time.

An entry-point plugin avoids those problems:

- The plugin is a separate source and binary package.
- The core source tree contains only the discovery contract.
- Debian can package the core without the plugin.
- GitHub releases can distribute the optional plugin package separately.
- The plugin can be updated without rebuilding the core.

## 3. Debian policy constraints

The separation is not only an architectural preference. It is required for a
package intended for Debian main.

### 3.1 Debian main must be self-contained

Debian Policy section 2.2.1 says that packages in `main` must not require
software outside `main` for execution:

- <https://www.debian.org/doc/debian-policy/ch-archive.html#the-main-archive-area>

The core package must not require PaddlePaddle, PaddleOCR, or packages from
PyPI. OCR is optional, but an application that installs external code at
runtime still bypasses the archive's dependency tracking and reproducibility.

### 3.2 Debian Python Policy

Debian Python Policy requires applications to use the Debian Python
interpreter and Debian-packaged Python modules:

- <https://www.debian.org/doc/packaging-manuals/python-policy/>

Relevant sections include:

- 3.5.2 Interpreter Location: use `/usr/bin/python3`, not an unversioned
  `env` interpreter or an arbitrary environment.
- 4.5 Dependencies: Python module dependencies must be packaged modules.
- 5.2 Programs using the default Python: programs must depend on the packages
  that provide the modules they use.

Creating a private virtual environment and installing code from PyPI is not a
substitute for Debian dependencies.

### 3.3 PEP 668 and externally managed Python

Debian marks its system Python as externally managed. `pip install` outside a
virtual environment is intentionally blocked:

- <https://peps.python.org/pep-0668/>
- <https://sources.debian.org/src/python3.13/3.13.5-2+deb13u5/debian/README.venv/>

The `pipx` and virtual-environment advice in Debian's documentation is aimed at
users installing applications, not at Debian packages that install their own
dependencies at runtime.

### 3.4 Runtime package installers are not acceptable

Debian has treated runtime `pip` installs as violations of the main-area
self-containment rule. See, for example:

- <https://bugs.debian.org/954154>

A Debian package must not silently become a package manager for code outside
the archive.

## 4. Package split

### 4.1 Core package: `ksnip-pyqt6`

The core package will contain:

- the application, UI, capture, annotation, project, and upload features;
- the generic external OCR **Script** backend;
- plugin discovery for the `ksnip_py.ocr` entry-point group;
- no PaddlePaddle imports;
- no PaddleOCR imports;
- no `pip` calls;
- no virtual-environment creation;
- no Model Manager that installs Python packages.

The core package continues to support OCR through a script that the user
configures. This is the version intended for Debian main.

### 4.2 Plugin package: `ksnip-pyqt6-ocr`

The optional plugin will contain:

- the Model Manager UI;
- creation of a managed OCR virtual environment;
- installation of PaddlePaddle/PaddleOCR into that environment;
- creation of the OCR launcher;
- configuration of the core `Script` backend;
- optional status checks and diagnostics.

The plugin is distributed through GitHub Releases and is not part of the
Debian main package.

### 4.3 Distribution matrix

| Artifact | Debian main | GitHub Releases | Contains Paddle | Creates venv / uses pip |
| --- | --- | --- | --- | --- |
| `ksnip-pyqt6` | yes | yes | no | no |
| `ksnip-pyqt6-ocr` | no | yes | no (installed at runtime) | yes |

The plugin package itself does not contain Paddle wheels. It downloads and
installs them into the user's managed environment after an explicit user
action.

## 5. Entry-point contract

The plugin is discovered through Python package metadata:

```toml
# ksnip-pyqt6-ocr/pyproject.toml
[project]
name = "ksnip-pyqt6-ocr"
version = "0.1.0"
dependencies = [
  "ksnip-pyqt6>=0.2.2,<0.3",
]

[project.entry-points."ksnip_py.ocr"]
paddle = "ksnip_py_ocr.plugin:PaddleOcrPlugin"
```

The entry-point group is `ksnip_py.ocr`. The plugin implementation class lives
in a separate import package (`ksnip_py_ocr`) and exposes a small, stable API.

### 5.1 Discovery in the core

The core must discover plugins lazily and without importing Paddle:

```python
from importlib.metadata import entry_points


def discover_ocr_plugins():
    plugins = []
    for entry_point in entry_points(group="ksnip_py.ocr"):
        try:
            plugin_class = entry_point.load()
            plugin = plugin_class()
            if plugin.api_version != 1:
                continue
            plugins.append(plugin)
        except Exception as exc:
            # A broken plugin must not prevent the core from starting.
            log.warning("OCR plugin %s failed: %s", entry_point.name, exc)
    return plugins
```

The plugin module must be lightweight. It must not import `paddle`,
`paddleocr`, or `paddlex` at module import time. Those imports belong inside
the installer or OCR runner, after the user starts an OCR operation.

### 5.2 Plugin API

The initial API version is `1`. The plugin exposes:

```python
class PaddleOcrPlugin:
    api_version = 1
    plugin_id = "paddleocr"
    plugin_name = "PaddleOCR"

    def is_available(self) -> bool:
        """Return True if the managed OCR environment exists."""
        ...

    def open_model_manager(self, parent, settings) -> bool:
        """Open the Model Manager and return True when it was accepted."""
        ...

    def configure_script(self, settings) -> bool:
        """Configure the core Script backend to use the managed launcher."""
        ...
```

The core only relies on this interface. It does not import the plugin's
internal modules.

### 5.3 Settings contract

The plugin communicates with the core through the existing OCR settings:

```text
ocr/backend     = "script"
ocr/script_path = "<managed launcher path>"
```

The core's Script backend continues to pass the image path as the first
argument and read the recognized text from stdout. No Paddle-specific code is
needed in the core.

The plugin may store its own state under a namespaced key, for example:

```text
ocr_plugin/paddle/venv_path
ocr_plugin/paddle/last_check
```

## 6. Managed OCR environment

The plugin manages a private environment under the user's data directory:

```text
${XDG_DATA_HOME:-$HOME/.local/share}/ksnip-pyqt6/ocr-venv/
```

The environment contains:

```text
ocr-venv/
  bin/
    python
    pip
    ksnip-ocr
```

The `ksnip-ocr` launcher has an absolute shebang pointing into the environment
and runs a small runner module:

```sh
#!/bin/sh
exec "$HOME/.local/share/ksnip-pyqt6/ocr-venv/bin/python" \
     -m ksnip_py_ocr.runner "$@"
```

The runner accepts one image path, invokes PaddleOCR, and prints recognized
text to stdout. Errors go to stderr and a nonzero exit status.

The plugin must not hard-code `/home/wachin` or any other developer path. Paths
are derived at runtime from `$HOME`, `XDG_DATA_HOME`, and the plugin's own
location.

### 6.1 Model cache

PaddleOCR models are not stored in the virtual environment. They are cached in:

```text
~/.paddlex/official_models/
```

PaddleOCR finds that cache automatically. The launcher does not need a model
path setting. Models are data and are downloaded only after the user starts the
install or first OCR operation.

### 6.2 Installation flow

The plugin performs these steps only after an explicit user action:

1. Verify that `python3-venv` and `python3-pip` are available.
2. Create the managed virtual environment.
3. Install pinned PaddlePaddle, PaddleOCR, PaddleX, Protobuf, and Markdownify
   versions.
4. Run a small import/initialization check.
5. Write the launcher atomically.
6. Configure `ocr/backend=script` and `ocr/script_path=<launcher>`.
7. Report success.

If any step fails, the plugin must not leave the core configured with a broken
launcher. A temporary directory or a staging environment should be used, and
the final launcher/config updates should happen only after verification.

### 6.3 Uninstallation

The plugin must distinguish between:

- removing the managed virtual environment;
- removing downloaded models;
- removing the OCR script configuration.

The plugin should not silently delete `~/.paddlex` because the same models may
be used by other applications.

## 7. UI integration

When the plugin is installed:

- `Options → Model Manager…` is visible and opens the plugin's manager.
- `Settings → OCR` may show the plugin's status.
- The core Script backend remains selectable.
- The plugin configures Script after a successful installation.

When the plugin is not installed:

- the core starts normally;
- the Model Manager entry is hidden or disabled with an explanation;
- Settings still offers the generic Script backend;
- no Paddle-related error is emitted at startup.

The core must never require the plugin for normal screenshot or annotation
features.

## 8. Packaging

### 8.1 Core Debian package

The `debian/control` for the core must not include Paddle or PyPI
dependencies:

```text
Depends: python3-pyqt6, python3-pyqt6.qtsvg, qt6-translations-l10n
```

The core build must not install the plugin. The plugin entry point is absent
from the Debian system Python, so discovery returns no plugins.

The core package can recommend an external OCR provider or document that users
may install one separately, but it must not download code itself.

### 8.2 Upstream GitHub packages

The GitHub release can provide:

- `ksnip-pyqt6` core package;
- `ksnip-pyqt6-ocr` optional package.

The OCR package depends on the core package and installs the plugin module and
entry point into the same Python environment as the core. It does not bundle
Paddle wheels; the managed environment is created at runtime.

### 8.3 Build commands

Core only:

```bash
git clone https://github.com/wachin/ksnip.git
cd ksnip
dpkg-buildpackage -b -us -uc
```

Optional OCR package (upstream distribution):

```bash
git clone https://github.com/wachin/ksnip-pyqt6-ocr.git
cd ksnip-pyqt6-ocr
dpkg-buildpackage -b -us -uc
```

The OCR package must declare a dependency on the matching core package.

### 8.4 Debian source package

Do not use a Git submodule for the plugin. If the plugin is ever proposed for
Debian, it must be a separate source package and must use Debian-packaged
dependencies. A Debian package that creates a venv and runs `pip` is not
acceptable, even in `contrib`.

## 9. Failure isolation and security

- Plugin discovery catches all exceptions and logs them.
- A missing or broken plugin does not prevent core startup.
- The plugin is trusted installed code; the core must not load arbitrary files
  from the working directory as plugins.
- The managed environment is private to the user.
- The plugin installs only after an explicit user action.
- Package versions should be pinned and recorded in the plugin's metadata.
- The core must provide an escape hatch, such as
  `KSNIP_DISABLE_OCR_PLUGINS=1`, for troubleshooting.

## 10. Testing plan

Core without plugin:

- starts normally;
- Script backend remains available;
- no Model Manager that runs `pip`;
- no Paddle imports;
- OCR reports a clear “no backend configured” error only when invoked.

Plugin installed:

- entry point is discovered;
- Model Manager appears;
- managed environment can be created and removed;
- launcher runs independently of the core interpreter;
- core Script settings are written only after verification;
- OCR returns text through stdout.

Failure cases:

- plugin import raises an exception;
- Paddle install fails;
- launcher is missing;
- managed environment is deleted after configuration;
- core must not crash in any of these cases.

Packaging tests:

- core `.deb` has no Paddle dependencies;
- core `.deb` contains no plugin entry point;
- OCR `.deb` depends on core and installs the entry point;
- `dpkg -c` and `lintian` are checked for both.

## 11. Repository naming

Recommended names:

```text
GitHub repository:   ksnip-pyqt6-ocr
Python distribution: ksnip-pyqt6-ocr
Python import:       ksnip_py_ocr
Entry-point group:   ksnip_py.ocr
```

`ksnip-py-ocr` is understandable but less specific. It does not identify the
PyQt6 core and can be confused with a generic Python helper. Python packaging
normalizes hyphens and underscores, so the distribution name
`ksnip-pyqt6-ocr` and the import package `ksnip_py_ocr` can coexist without
ambiguity.

## 12. Migration plan

1. Define the plugin API and discovery module in the core.
2. Add an internal build/runtime switch that disables plugin discovery for
   Debian builds.
3. Move the Model Manager and Paddle-specific OCR code into the separate
   `ksnip-pyqt6-ocr` repository.
4. Keep only the generic Script backend in the core.
5. Add the entry point to the plugin package.
6. Add tests for “plugin absent” and “plugin present”.
7. Build and publish the optional OCR package from GitHub.
8. Submit only the core package to Debian mentors.

The migration must not break existing users: if an existing script backend is
configured, it continues to work even when the plugin is not installed.

## 13. References

- Debian Policy, main archive area:
  <https://www.debian.org/doc/debian-policy/ch-archive.html#the-main-archive-area>
- Debian Python Policy:
  <https://www.debian.org/doc/packaging-manuals/python-policy/>
- PEP 668:
  <https://peps.python.org/pep-0668/>
- Debian `README.venv`:
  <https://sources.debian.org/src/python3.13/3.13.5-2+deb13u5/debian/README.venv/>
- Debian bug #954154, runtime pip and Policy 2.2.1:
  <https://bugs.debian.org/954154>
