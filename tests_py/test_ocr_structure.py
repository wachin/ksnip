from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import patch

from ksnip_py.ocr_backend import (
    OcrBackend,
    OcrError,
    OcrMissingDependencyError,
    OcrOptions,
)


class _DependencyError(Exception):
    """Stands in for paddlex.utils.deps.DependencyError."""


def _dependency_chain() -> RuntimeError:
    """Reproduce how PaddleOCR hides a missing PaddleX extra.

    ``paddleocr`` catches PaddleX's DependencyError and re-raises a generic
    RuntimeError with the original chained as ``__cause__``.
    """
    cause = _DependencyError(
        "`PP-StructureV3` requires additional dependencies. To install them, run "
        '`pip install "paddlex[ocr]==<PADDLEX_VERSION>"`.'
    )
    wrapper = RuntimeError(
        "A dependency error occurred during pipeline creation. Please refer to the "
        "installation documentation to ensure all required dependencies are installed."
    )
    wrapper.__cause__ = cause
    return wrapper


class _FakeResult:
    def __init__(self, markdown) -> None:
        self.markdown = markdown


class _FakePipeline:
    """Minimal stand-in for paddleocr.PPStructureV3."""

    instances: list["_FakePipeline"] = []

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.inputs: list[str] = []
        _FakePipeline.instances.append(self)

    def predict(self, image_path: str):
        self.inputs.append(image_path)
        return [
            _FakeResult(
                {
                    "markdown_texts": (
                        "| Product | Total |\n| --- | --- |\n| Mouse | 15.50 |"
                    )
                }
            )
        ]


def _fake_paddleocr(pipeline_class) -> types.ModuleType:
    module = types.ModuleType("paddleocr")
    module.PPStructureV3 = pipeline_class
    return module


class StructureBackendDispatchTest(unittest.TestCase):
    def setUp(self) -> None:
        _FakePipeline.instances = []

    def test_structure_backend_returns_markdown_with_table(self) -> None:
        with patch.dict(sys.modules, {"paddleocr": _fake_paddleocr(_FakePipeline)}):
            text = OcrBackend().recognize_file(
                "/tmp/capture.png",
                OcrOptions(backend="paddleocr_structure", language="spanish"),
            )
        self.assertIn("| Product | Total |", text)
        self.assertIn("| Mouse | 15.50 |", text)

    def test_structure_pipeline_uses_guards_and_table_recognition(self) -> None:
        with patch.dict(sys.modules, {"paddleocr": _fake_paddleocr(_FakePipeline)}):
            OcrBackend().recognize_file(
                "/tmp/capture.png",
                OcrOptions(backend="paddleocr_structure", language="english"),
            )
        kwargs = _FakePipeline.instances[-1].kwargs
        self.assertEqual(kwargs["lang"], "en")
        self.assertFalse(kwargs["enable_mkldnn"])
        self.assertFalse(kwargs["use_doc_orientation_classify"])
        self.assertFalse(kwargs["use_doc_unwarping"])
        self.assertTrue(kwargs["use_table_recognition"])
        # Formulas need an extra model, so they stay off unless requested.
        self.assertFalse(kwargs["use_formula_recognition"])

    def test_structure_backend_maps_language_code(self) -> None:
        with patch.dict(sys.modules, {"paddleocr": _fake_paddleocr(_FakePipeline)}):
            OcrBackend().recognize_file(
                "/tmp/capture.png",
                OcrOptions(backend="paddleocr_structure", language="spanish"),
            )
        self.assertEqual(_FakePipeline.instances[-1].kwargs["lang"], "es")

    def test_formula_flag_enables_formula_recognition(self) -> None:
        with patch.dict(sys.modules, {"paddleocr": _fake_paddleocr(_FakePipeline)}):
            OcrBackend().recognize_file(
                "/tmp/capture.png",
                OcrOptions(
                    backend="paddleocr_structure",
                    language="english",
                    structure_formulas=True,
                ),
            )
        self.assertTrue(_FakePipeline.instances[-1].kwargs["use_formula_recognition"])

    def test_unknown_backend_is_rejected(self) -> None:
        with self.assertRaises(OcrError):
            OcrBackend().recognize_file(
                "/tmp/capture.png", OcrOptions(backend="mystery", language="english")
            )


class StructureMissingDependencyTest(unittest.TestCase):
    def test_missing_paddlex_extra_is_reported_with_install_hint(self) -> None:
        def _explode(**kwargs):
            raise _dependency_chain()

        with patch.dict(sys.modules, {"paddleocr": _fake_paddleocr(_explode)}):
            with self.assertRaises(OcrMissingDependencyError) as caught:
                OcrBackend().recognize_file(
                    "/tmp/capture.png",
                    OcrOptions(backend="paddleocr_structure", language="english"),
                )
        self.assertIn("requirements-ocr.txt", str(caught.exception))

    def test_dependency_error_is_detected_through_cause_chain(self) -> None:
        self.assertTrue(OcrBackend._is_structure_dependency_error(_dependency_chain()))

    def test_plain_failure_is_not_a_dependency_error(self) -> None:
        self.assertFalse(OcrBackend._is_structure_dependency_error(RuntimeError("boom")))
        self.assertFalse(OcrBackend._is_structure_dependency_error(ValueError("unrelated")))

    def test_dependency_message_points_at_requirements_file(self) -> None:
        message = OcrBackend._structure_dependency_message()
        self.assertIn("requirements-ocr.txt", message)
        self.assertIn("tables + Markdown", message)


class StructureMarkdownExtractionTest(unittest.TestCase):
    def test_markdown_is_collected_from_every_page(self) -> None:
        results = [
            _FakeResult({"markdown_texts": "first page"}),
            _FakeResult({"markdown_texts": "second page"}),
        ]
        self.assertEqual(
            OcrBackend._extract_structure_markdown(results),
            "first page\n\nsecond page",
        )

    def test_empty_and_malformed_pages_are_skipped(self) -> None:
        results = [
            _FakeResult({"markdown_texts": "   "}),
            _FakeResult({"markdown_texts": ""}),
            object(),
            _FakeResult("not a dict"),
            _FakeResult({"markdown_texts": "real content"}),
        ]
        self.assertEqual(OcrBackend._extract_structure_markdown(results), "real content")

    def test_no_results_yields_empty_text(self) -> None:
        self.assertEqual(OcrBackend._extract_structure_markdown([]), "")
        self.assertEqual(OcrBackend._extract_structure_markdown(None), "")

    def test_empty_extraction_raises_instead_of_returning_blank_text(self) -> None:
        with patch.dict(sys.modules, {"paddleocr": _fake_paddleocr(_FakePipeline)}):
            with patch.object(_FakePipeline, "predict", return_value=[_FakeResult({})]):
                with self.assertRaises(OcrError) as caught:
                    OcrBackend().recognize_file(
                        "/tmp/capture.png",
                        OcrOptions(backend="paddleocr_structure", language="english"),
                    )
        self.assertIn("no recognized text", str(caught.exception))


class OcrOptionsTest(unittest.TestCase):
    def test_structure_formulas_defaults_to_off(self) -> None:
        options = OcrOptions(backend="paddleocr_structure", language="english")
        self.assertFalse(options.structure_formulas)

    def test_line_backend_keeps_empty_script_path(self) -> None:
        options = OcrOptions(backend="paddleocr", language="english")
        self.assertEqual(options.script_path, "")


if __name__ == "__main__":
    unittest.main()

