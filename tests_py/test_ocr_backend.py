from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import patch

from ksnip_py.ocr_backend import OcrBackend, OcrOptions

# HTML tags that the conversion must never leak into the final Markdown output.
_LEAKY_TAGS = (
    "<div", "</div>", "<p", "</p>", "<center", "</center>",
    "<table", "<th", "<td", "<tr", "<html", "<body",
)


def _assert_clean(self: unittest.TestCase, text: str) -> None:
    lowered = text.lower()
    for tag in _LEAKY_TAGS:
        self.assertNotIn(tag, lowered, f"leaked HTML tag {tag!r} into output")


class HtmlTableToMarkdownWrapperTest(unittest.TestCase):
    '''Regression tests: HTML wrappers around tables must be stripped.

    These lock in the fix from commit c1471458 so a future edit to
    _html_tables_to_markdown cannot silently let <div>/<p>/<center> wrappers
    (which PP-StructureV3 emits around tables) reappear in the Markdown.
    '''

    def test_div_center_wrapper_is_removed(self) -> None:
        html = (
            '<div style="text-align: center;">'
            '<table><tr><th>Referencia (Pais)</th><th>Participantes</th></tr>'
            '<tr><td>Oneset al., 2025 (Turquia)</td><td>Jugadoras</td></tr>'
            '</table></div>'
        )
        out = OcrBackend._html_tables_to_markdown(html)
        _assert_clean(self, out)
        self.assertTrue(out.strip().startswith("| Referencia (Pais)"))

    def test_p_wrapper_is_removed(self) -> None:
        html = (
            '<p><table><tr><th>A</th><th>B</th></tr>'
            '<tr><td>1</td><td>2</td></tr></table></p>'
        )
        out = OcrBackend._html_tables_to_markdown(html)
        _assert_clean(self, out)
        self.assertIn("| A | B |", out)

    def test_center_wrapper_is_removed(self) -> None:
        html = (
            '<center><table><tr><th>X</th></tr>'
            '<tr><td>y</td></tr></table></center>'
        )
        out = OcrBackend._html_tables_to_markdown(html)
        _assert_clean(self, out)

    def test_nested_div_wrapper_is_removed(self) -> None:
        html = (
            '<div class="x"><div style="text-align:center;">'
            '<table><tr><th>H1</th><th>H2</th></tr>'
            '<tr><td>a</td><td>b</td></tr></table></div></div>'
        )
        out = OcrBackend._html_tables_to_markdown(html)
        _assert_clean(self, out)

    def test_mixed_content_preserves_surrounding_text(self) -> None:
        html = (
            "Intro text.\n\n"
            '<div style="text-align: center;">'
            '<table><tr><th>Col</th></tr><tr><td>val</td></tr></table></div>'
            "\n\nOutro."
        )
        out = OcrBackend._html_tables_to_markdown(html)
        _assert_clean(self, out)
        self.assertIn("Intro text.", out)
        self.assertIn("Outro.", out)

    def test_accents_and_diacritics_are_preserved(self) -> None:
        html = (
            '<div><table>'
            '<tr><th>Referencia (Pais)</th><th>Participantes</th></tr>'
            '<tr><td>Daziroğlu et al., 2024 (Turquía)</td>'
            '<td>Mujeres con PCOS</td></tr></table></div>'
        )
        out = OcrBackend._html_tables_to_markdown(html)
        _assert_clean(self, out)
        self.assertIn("Turquía", out)
        self.assertIn("Daziroğlu", out)
        self.assertIn("PCOS", out)

    def test_inline_formatting_is_converted(self) -> None:
        html = (
            '<div><table><tr><th>H</th></tr>'
            '<tr><td>Jugadoras <b>profesionales</b></td></tr></table></div>'
        )
        out = OcrBackend._html_tables_to_markdown(html)
        _assert_clean(self, out)
        self.assertIn("**profesionales**", out)

    def test_multiple_tables_keep_separator_text(self) -> None:
        html = (
            '<div><table><tr><th>T1</th></tr><tr><td>r1</td></tr></table></div>'
            " and "
            '<center><table><tr><th>T2</th></tr><tr><td>r2</td></tr></table></center>'
        )
        out = OcrBackend._html_tables_to_markdown(html)
        _assert_clean(self, out)
        self.assertIn("| T1 |", out)
        self.assertIn("| T2 |", out)
        self.assertIn("and", out)

    def test_no_table_passes_through_unchanged(self) -> None:
        text = "Just plain markdown with a <b>bold</b> word and no tables."
        out = OcrBackend._html_tables_to_markdown(text)
        # Block-wrapper cleanup only targets div/p/center/html/body, not <b>.
        _assert_clean(self, out)
        self.assertIn("Just plain markdown", out)

    def test_fallback_strips_wrappers_without_markdownify(self) -> None:
        # Force the ImportError branch so the regex fallback runs.
        html = (
            '<div><table><tr><th>A</th></tr><tr><td>1</td></tr></table></div>'
        )
        with patch.dict(sys.modules, {"markdownify": None}):
            out = OcrBackend._html_tables_to_markdown(html)
        _assert_clean(self, out)
        self.assertIn("| A |", out)


class _FakeResult:
    def __init__(self, markdown) -> None:
        self.markdown = markdown


class _FakePipeline:
    instances: list["_FakePipeline"] = []

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.inputs: list[str] = []
        _FakePipeline.instances.append(self)

    def predict(self, image_path: str):
        return [
            _FakeResult(
                {
                    "markdown_texts": (
                        '<div style="text-align: center;">'
                        '<table><tr><th>Referencia (Pais)</th>'
                        "<th>Participantes</th></tr>"
                        '<tr><td>Oneset al., 2025 (Turquia)</td>'
                        "<td>Jugadoras</td></tr></table></div>"
                    )
                }
            )
        ]


def _fake_paddleocr(pipeline_class) -> types.ModuleType:
    module = types.ModuleType("paddleocr")
    module.PPStructureV3 = pipeline_class
    return module


class StructureBackendWrapperIntegrationTest(unittest.TestCase):
    '''End-to-end regression: the structure backend must strip wrappers too.'''

    def setUp(self) -> None:
        _FakePipeline.instances = []

    def test_structure_backend_strips_div_wrapper_end_to_end(self) -> None:
        with patch.dict(
            sys.modules, {"paddleocr": _fake_paddleocr(_FakePipeline)}
        ):
            text = OcrBackend().recognize_file(
                "/tmp/capture.png",
                OcrOptions(backend="paddleocr_structure", language="spanish"),
            )
        _assert_clean(self, text)
        self.assertIn("| Referencia (Pais) |", text)
        self.assertIn("| Jugadoras |", text)


if __name__ == "__main__":
    unittest.main()
