#!/usr/bin/env python3
"""Create a portable ZIP with forward-slash entry names and verify it.

PowerShell 5.1 writes backslash separators through both Compress-Archive and
ZipFile::CreateFromDirectory, which collapses the tree when the archive is
extracted on Linux or macOS. CPython normalises separators in zipfile, so this
script is used instead of the PowerShell cmdlets.

Usage:
    make_portable_zip.py SOURCE OUTPUT --prefix NAME --require FILE ...
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path


def entry_name(path: Path, root: Path, prefix: str) -> str:
    parts = path.relative_to(root).parts
    if any("\\" in part for part in parts):
        raise ValueError(f"path component contains a backslash: {path}")
    name = "/".join(parts)
    return f"{prefix}/{name}" if prefix else name


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--prefix", default="")
    parser.add_argument("--require", action="append", default=[])
    args = parser.parse_args(argv)

    source = args.source.resolve()
    if not source.is_dir():
        parser.error(f"source is not a directory: {source}")
    if args.prefix and ("/" in args.prefix or "\\" in args.prefix):
        parser.error("--prefix must be a single path component")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.unlink(missing_ok=True)

    files = sorted(path for path in source.rglob("*") if path.is_file())
    if not files:
        parser.error(f"source directory is empty: {source}")

    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, entry_name(path, source, args.prefix))

    with zipfile.ZipFile(args.output) as archive:
        names = archive.namelist()
    bad = [name for name in names if "\\" in name]
    if bad:
        args.output.unlink(missing_ok=True)
        print(f"archive contains backslash entry names: {bad[:3]}", file=sys.stderr)
        return 1
    expected = [
        f"{args.prefix}/{name}" if args.prefix else name
        for name in args.require
    ]
    missing = [name for name in expected if name not in names]
    if missing:
        args.output.unlink(missing_ok=True)
        print(f"archive is missing required files: {missing}", file=sys.stderr)
        return 1

    print(f"{args.output} ({len(names)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
