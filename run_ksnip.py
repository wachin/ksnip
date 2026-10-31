"""Entry point for the frozen (PyInstaller and Nuitka) builds.

The application package uses relative imports, so ksnip_py/app.py cannot be
handed to a freezer as a top-level script: it would run with no parent package
and fail with "attempted relative import with no known parent package". This
module is a normal top-level script that imports the package properly.

It is also usable directly from a source checkout:

    python run_ksnip.py
"""

from __future__ import annotations

from ksnip_py.app import main

if __name__ == "__main__":
    raise SystemExit(main())
