import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = REPO_ROOT / "tools" / "update_pyqt_translations.py"
BACKUP_CATALOGS = REPO_ROOT / "Temp" / "ksnip-master" / "translations"


def _load_module():
    spec = importlib.util.spec_from_file_location("update_pyqt_translations_ut", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_ts(path, messages, language="de"):
    """Create a minimal Qt .ts catalog from a list of message dicts.

    Each dict may contain: source, text, type (unfinished/obsolete/vanished),
    nested (adds a child element to the translation).
    """
    root = ET.Element("TS", {"version": "2.1", "language": language})
    context = ET.SubElement(root, "context")
    ET.SubElement(context, "name").text = "TestContext"
    for entry in messages:
        message = ET.SubElement(context, "message")
        ET.SubElement(message, "source").text = entry["source"]
        translation = ET.SubElement(message, "translation")
        if entry.get("type"):
            translation.set("type", entry["type"])
        if entry.get("nested"):
            ET.SubElement(translation, "numerus")
        if entry.get("text") is not None:
            translation.text = entry["text"]
    path.write_text(ET.tostring(root, encoding="unicode"), encoding="utf-8")


def _translations_by_source(ts_path):
    root = ET.parse(ts_path).getroot()
    result = {}
    for message in root.iter("message"):
        translation = message.find("translation")
        result[message.findtext("source")] = (translation.text, translation.get("type"))
    return result


@pytest.fixture()
def tool(tmp_path, monkeypatch):
    module = _load_module()
    py_tr = tmp_path / "ksnip_py" / "translations"
    py_tr.mkdir(parents=True)
    monkeypatch.setattr(module, "PY_TRANSLATIONS", py_tr)
    monkeypatch.setattr(module, "KSNIP_TRANSLATIONS", tmp_path / "translations")
    monkeypatch.setattr(module, "ANNOTATOR_TRANSLATIONS", tmp_path / "libraries" / "kImageAnnotator" / "translations")
    monkeypatch.setattr(module, "TEMPLATE", py_tr / "ksnip_py_es.ts")
    return module


# --------------------------------------------------------------------------
# translated_strings
# --------------------------------------------------------------------------
def test_translated_strings_reads_only_finished(tool, tmp_path):
    path = tmp_path / "catalog.ts"
    _write_ts(path, [
        {"source": "Hello", "text": "Hallo"},
        {"source": "Unfinished", "text": "", "type": "unfinished"},
        {"source": "Obsolete", "text": "Alt", "type": "obsolete"},
        {"source": "Vanished", "text": "Weg", "type": "vanished"},
        {"source": "Nested", "text": "X", "nested": True},
        {"source": "Empty", "text": ""},
    ])
    assert tool.translated_strings(path) == {"Hello": "Hallo"}


def test_translated_strings_missing_file_returns_empty(tool, tmp_path):
    assert tool.translated_strings(tmp_path / "missing.ts") == {}


def test_translated_strings_first_occurrence_wins(tool, tmp_path):
    path = tmp_path / "dup.ts"
    _write_ts(path, [
        {"source": "A", "text": "first"},
        {"source": "A", "text": "second"},
    ])
    assert tool.translated_strings(path)["A"] == "first"


# --------------------------------------------------------------------------
# locales
# --------------------------------------------------------------------------
def test_locales_from_port_catalogs(tool):
    for loc in ["de", "fr", "es", "ta"]:
        (tool.PY_TRANSLATIONS / ("ksnip_py_%s.ts" % loc)).write_text("<TS/>", encoding="utf-8")
    (tool.PY_TRANSLATIONS / "notes.txt").write_text("x", encoding="utf-8")
    assert tool.locales() == ["de", "fr", "ta"]


def test_locales_empty_when_no_catalogs(tool):
    assert tool.locales() == []


# --------------------------------------------------------------------------
# build_catalog
# --------------------------------------------------------------------------
def _template(tool):
    _write_ts(tool.TEMPLATE, [
        {"source": "A", "text": "A-es"},
        {"source": "B", "text": "B-es"},
        {"source": "C", "text": "C-es"},
    ], language="es")


def test_build_catalog_preserves_existing_translations(tool, monkeypatch):
    _template(tool)
    _write_ts(tool.PY_TRANSLATIONS / "ksnip_py_de.ts", [
        {"source": "A", "text": "Hallo"},
        {"source": "B", "text": "", "type": "unfinished"},
    ])
    calls = []
    monkeypatch.setattr(tool.subprocess, "run", lambda args, *a, **k: calls.append(args))

    translated, total = tool.build_catalog("de")

    assert (translated, total) == (1, 3)
    assert calls and calls[0][0] == "lrelease"
    values = _translations_by_source(tool.PY_TRANSLATIONS / "ksnip_py_de.ts")
    assert values["A"] == ("Hallo", None)
    assert values["B"][1] == "unfinished"
    assert values["C"][1] == "unfinished"


def test_build_catalog_imports_cpp_catalog_when_present(tool, monkeypatch):
    _template(tool)
    _write_ts(tool.PY_TRANSLATIONS / "ksnip_py_de.ts", [{"source": "A", "text": "Hallo"}])
    tool.KSNIP_TRANSLATIONS.mkdir(parents=True)
    _write_ts(tool.KSNIP_TRANSLATIONS / "ksnip_de.ts", [{"source": "B", "text": "Bee"}])
    monkeypatch.setattr(tool.subprocess, "run", lambda args, *a, **k: None)

    translated, total = tool.build_catalog("de")

    assert (translated, total) == (2, 3)


def test_build_catalog_port_translations_take_precedence(tool, monkeypatch):
    _template(tool)
    _write_ts(tool.PY_TRANSLATIONS / "ksnip_py_de.ts", [{"source": "A", "text": "Port"}])
    tool.KSNIP_TRANSLATIONS.mkdir(parents=True)
    _write_ts(tool.KSNIP_TRANSLATIONS / "ksnip_de.ts", [{"source": "A", "text": "Cpp"}])
    monkeypatch.setattr(tool.subprocess, "run", lambda args, *a, **k: None)

    tool.build_catalog("de")

    values = _translations_by_source(tool.PY_TRANSLATIONS / "ksnip_py_de.ts")
    assert values["A"][0] == "Port"


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def test_main_builds_every_locale_and_template(tool, monkeypatch):
    _template(tool)
    for loc in ["de", "fr"]:
        _write_ts(tool.PY_TRANSLATIONS / ("ksnip_py_%s.ts" % loc), [{"source": "A", "text": "x"}])
    calls = []
    monkeypatch.setattr(tool.subprocess, "run", lambda args, *a, **k: calls.append(args))

    assert tool.main() == 0

    assert calls[0][0] == "pylupdate6"
    lrelease_targets = [call[1] for call in calls if call[0] == "lrelease"]
    assert str(tool.PY_TRANSLATIONS / "ksnip_py_de.ts") in lrelease_targets
    assert str(tool.PY_TRANSLATIONS / "ksnip_py_fr.ts") in lrelease_targets
    assert str(tool.TEMPLATE) in lrelease_targets


# --------------------------------------------------------------------------
# Integration with the real backup catalogs (skipped when not present)
# --------------------------------------------------------------------------
@pytest.mark.skipif(
    not (BACKUP_CATALOGS / "ksnip_de.ts").exists(),
    reason="local C++ backup catalogs not available",
)
def test_real_cpp_catalog_can_be_parsed():
    module = _load_module()
    data = module.translated_strings(BACKUP_CATALOGS / "ksnip_de.ts")
    assert len(data) > 100
