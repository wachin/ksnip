#!/usr/bin/env python3
"""Print the application version declared in pyproject.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    with (root / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    print(data["project"]["version"])


if __name__ == "__main__":
    main()
