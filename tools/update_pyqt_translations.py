#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY_TRANSLATIONS = ROOT / "ksnip_py" / "translations"
KSNIP_TRANSLATIONS = ROOT / "translations"
ANNOTATOR_TRANSLATIONS = ROOT / "libraries" / "kImageAnnotator" / "translations"
TEMPLATE = PY_TRANSLATIONS / "ksnip_py_es.ts"


def translated_strings(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    translations: dict[str, str] = {}
    for message in ET.parse(path).getroot().iter("message"):
        source = message.findtext("source")
        translation = message.find("translation")
        if not source or translation is None or translation.get("type") in {"unfinished", "obsolete", "vanished"}:
            continue
        if list(translation):
            continue
        value = translation.text or ""
        if value:
            translations.setdefault(source, value)
    return translations


def locales() -> list[str]:
    values = {path.stem.removeprefix("ksnip_") for path in KSNIP_TRANSLATIONS.glob("ksnip_*.ts")}
    values.update(path.stem.removeprefix("kImageAnnotator_") for path in ANNOTATOR_TRANSLATIONS.glob("kImageAnnotator_*.ts"))
    values.discard("es")
    return sorted(values)


def build_catalog(locale: str) -> tuple[int, int]:
    tree = ET.parse(TEMPLATE)
    root = tree.getroot()
    root.set("language", locale)
    available = translated_strings(KSNIP_TRANSLATIONS / f"ksnip_{locale}.ts")
    for source, translation in translated_strings(ANNOTATOR_TRANSLATIONS / f"kImageAnnotator_{locale}.ts").items():
        available.setdefault(source, translation)

    translated = 0
    total = 0
    for message in root.iter("message"):
        source = message.findtext("source") or ""
        translation = message.find("translation")
        if translation is None:
            translation = ET.SubElement(message, "translation")
        if translation.get("type") in {"obsolete", "vanished"}:
            continue
        translation.clear()
        total += 1
        value = available.get(source)
        if value:
            translation.text = value
            translated += 1
        else:
            translation.set("type", "unfinished")

    ts_path = PY_TRANSLATIONS / f"ksnip_py_{locale}.ts"
    payload = ET.tostring(root, encoding="utf-8")
    ts_path.write_bytes(b'<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE TS>\n' + payload + b"\n")
    subprocess.run(
        ["lrelease", str(ts_path), "-qm", str(ts_path.with_suffix(".qm"))],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return translated, total


def main() -> int:
    subprocess.run(
        ["pylupdate6", *[str(path) for path in sorted((ROOT / "ksnip_py").glob("*.py"))], "-ts", str(TEMPLATE)],
        check=True,
    )
    for locale in locales():
        translated, total = build_catalog(locale)
        print(f"{locale}: {translated}/{total}")
    subprocess.run(["lrelease", str(TEMPLATE), "-qm", str(TEMPLATE.with_suffix(".qm"))], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
