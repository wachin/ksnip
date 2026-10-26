# The `external/` folder

This folder holds **local clones** of OCR / document-analysis repositories that
were investigated to improve table recognition and image to Markdown conversion
inside **ksnip_py** (the PyQt6 port of ksnip).

> **Git note:** the `external/` folder is listed in `.gitignore` (the
> `# Personal` section points to `external`). The cloned repositories are NOT
> pushed to the repo. Only this `README.md` is force-added with
> `git add -f external/README.md` so that anyone who clones ksnip knows what was
> studied here and why.

---

## Why this folder exists

`ksnip_py` converts table screenshots to Markdown using the `PP-StructureV3`
pipeline from PaddleOCR (see `ksnip_py/ocr_backend.py`,
`_recognize_with_pp_structure`). The Markdown conversion works, but the
**recognition quality** (lost Turkish/Spanish accents and diacritics, broken word
spacing) falls short of vision models such as DeepSeek. These 6 repositories were
cloned to find reusable code that improves:

1. Table recognition (layout + structure).
2. Image to Markdown conversion in general.

---

## Investigated repositories

| Repo | License | Approach | What it offers ksnip_py | Integration cost |
|------|---------|----------|--------------------------|------------------|
| [Folio-OCR](#1-folio-ocr) | MIT | GLM-OCR (VLM via Ollama) + PP-DocLayoutV3 | Robust reusable post-processing | Medium (Ollama + model) |
| [PaddleOCR](#2-paddleocr) | Apache-2.0 | Already the current backend | Confirms tables come out as HTML | Low (already integrated) |
| [surya](#3-surya) | Apache-2.0 | Single VLM (layout+OCR+table) | HTML to structure parser (BeautifulSoup) | High (torch>=2.7) |
| [marker](#4-marker) | Apache-2.0 | Surya wrapper + MD render | `markdownify` for reliable HTML to MD + LLM correction | High (torch + Surya) |
| [docling](#5-docling) | MIT | VLM pipelines (incl. DeepSeek OCR) | DeepSeek table HTML parser | High (torch/onnx) |
| [OCRmyPDF](#6-ocrmypdf) | MPL-2.0 (copyleft) | Tesseract on PDF layer | Not applicable (no table to MD) | -- |

---

## 1. Folio-OCR

- **URL:** https://github.com/vorojar/Folio-OCR
- **License:** MIT (freely reusable).
- **Approach:** Document OCR using `PP-DocLayoutV3` for layout and **GLM-OCR**
  (a large vision model) served via **Ollama** for the actual OCR. Converts to
  Markdown / TXT / DOCX / EPUB.

**Reusable code in `folio_ocr/server.py`:**

- `_postprocess()` (server.py:677) orchestrates cleanup of the resulting Markdown.
- `_latex_to_unicode()` / `_convert_math_interior()` (server.py:820+) convert
  LaTeX commands and accents to plain Unicode. **Useful for the lost-diacritics
  problem** (a, i, c, i, g...).
- `class _TableParser(HTMLParser)` (server.py:1319) extracts rows/cells from an
  HTML `<table>` while treating `<th>` as a header row robustly (better than
  ksnip_py current regex).
- `_preserve_html_tables()` (server.py:708) applies transformations only outside
  `<table>` blocks, and `_remove_empty_html_tables()` (server.py:690) drops
  empty "shell" tables the model hallucinates.
- `_dedup_lines()` (server.py:735+) removes duplicated lines.

**Conclusion:** the OCR itself (GLM-OCR) needs Ollama + a heavy model, but its
**post-processing can be copied as-is** into `ksnip_py` to improve Markdown
cleanup and `<th>` handling.

---

## 2. PaddleOCR

- **URL:** https://github.com/PaddlePaddle/PaddleOCR
- **License:** Apache-2.0.
- **Approach:** This is the backend **ksnip_py already uses**.

**Key finding (`ppstructure/recovery/recovery_to_markdown.py`):**

- `convert_info_markdown()` (line 129) inserts the table directly as HTML:
  `markdown_string.append(region["res"]["html"])`. In other words: **the table
  comes out as HTML and converting it to Markdown is the caller's job**.
- `replace_special_char()` (line 141) escapes `*`, `` ```, `~`, `$` so the
  Markdown does not break.

**Conclusion:** this confirms the weak link in ksnip_py is its own
`_html_tables_to_markdown` / `_simple_html_table_to_markdown` functions
(`ksnip_py/ocr_backend.py`), not PaddleOCR. Improving that conversion (see
marker below) and, above all, the **recognition model quality**, is the path.
The table structure (including the header row) is preserved well; what fails is
the OCR of accented characters.

---

## 3. surya

- **URL:** https://github.com/datalab-to/surya
- **License:** Apache-2.0.
- **Approach:** Surya 2 runs layout, OCR and table recognition with a **single
  vision model** (VLM). Heavy dependencies: `torch>=2.7.0,<3`,
  `transformers>=5.12.1` (pyproject.toml).

**Reusable code in `surya/inference/parsers.py`:**

- `parse_full_page_html()` (uses BeautifulSoup) parses the `<div data-bbox
  data-label>` blocks the model emits and extracts each block's inner HTML.
- `clean_block_html()` strips code fences from the emitted HTML.
- `parse_table_rec()` / `parse_layout()` tolerate malformed JSON.

Tables come out as HTML `<table>...</table>`; an HTML to Markdown converter is
still needed.

**Conclusion:** an alternative high-fidelity backend (close to DeepSeek) but
requires heavy torch + transformers. Its BeautifulSoup parsers are reusable if a
VLM backend is desired.

---

## 4. marker

- **URL:** https://github.com/datalab-to/marker
- **License:** Apache-2.0.
- **Approach:** A wrapper over **Surya** with a very polished
  document to Markdown conversion pipeline (PDFs, but its table logic is
  exportable).

**Reusable code:**

- `marker/renderers/markdown.py` -> `class Markdownify(MarkdownConverter)`
  extends the **`markdownify`** library (BeautifulSoup to Markdown). This is a
  **robust HTML to Markdown conversion that respects `<th>`/`rowspan`/`colspan`**
  and produces correct pipe-Markdown tables. It would replace ksnip_py current
  regex/pandoc conversion with advantage. (ksnip_py already adopted this approach
  in `_html_tables_to_markdown`.)
- `marker/processors/table.py` -> `clean_table_html()` (re-serializes with
  BeautifulSoup to balance truncated tags) and `reconstruct_table_html()`
  (CPU heuristic to rebuild a table grid).
- `marker/processors/llm/llm_table.py` -> `LLMTableProcessor` sends the table
  image and its HTML to an **LLM (Gemini)** to correct errors and align headers
  with columns. **This is exactly the DeepSeek approach**: the VLM corrects the
  OCR against the image.

**Conclusion:** two immediate takeaways -- (a) use `markdownify` for reliable
HTML to Markdown conversion, and (b) an "LLM correction" pattern to bring
accuracy up to DeepSeek level.

---

## 5. docling

- **URL:** https://github.com/docling-project/docling
- **License:** MIT.
- **Approach:** Conversion pipelines; includes VLM backends (Granite Vision,
  Nemotron-Parse, **DeepSeek OCR**, PaddleOCR-VL). Dependencies:
  `torch>=2.2.2`, `onnxruntime`, `transformers>=5.16`.

**Reusable code in `docling/utils/deepseekocr_utils.py`:**

- `_parse_table_html()` parses the annotated Markdown format returned by
  **DeepSeek OCR** and converts it into a `TableData` structure (uses `lxml`).
  Directly relevant: it shows how to robustly parse the HTML of a table (rows,
  cells, headers) produced by a DeepSeek-style VLM.
- Also present: `docling/utils/paddleocr_vl_utils.py` and
  `docling/models/stages/table_structure/table_structure_model_granite_vision.py`.

**Conclusion:** the DeepSeek OCR table parser is the reference example for
integrating a high-precision VLM and converting its output to Markdown/Table.

---

## 6. OCRmyPDF

- **URL:** https://github.com/ocrmypdf/OCRmyPDF
- **License:** **MPL-2.0 (strong file-level copyleft)** -- caution if copying
  code into ksnip (GPL-friendly, but the copied file must remain MPL-2.0).
- **Approach:** A command-line tool that adds an OCR text layer (Tesseract) to
  existing PDFs. **It does not do table recognition or Markdown conversion**; its
  notion of "table" is only text-box positioning for rendering over the PDF.

**Conclusion:** the least relevant to ksnip_py goal. Kept here only for
completeness of the investigation.

---

## Diagnosis and recommendations for ksnip_py

The accuracy gap versus DeepSeek **is not in the Markdown conversion** (the table
structure, including the header row, is preserved well in ksnip_py). The problem
is the **recognition model quality**: `PP-OCRv5_mobile_rec` loses diacritics
such as i, c, g, o, u and word spacing (e.g. "Ones et al." -> "Oneset al.",
"Altinkilic" -> "Altinkls").

Three paths, from least to most effort:

1. **Strengthen the HTML to Markdown conversion (done).** `_html_tables_to_markdown`
   now uses the **`markdownify`** library (the same one marker uses), which
   respects `<th>` and table structure, and also strips `<div>`/`<p>`/`<center>`
   wrappers that PP-StructureV3 emits around tables. Regression tests live in
   `tests_py/test_ocr_backend.py`.

2. **Improve the PaddleOCR recognition model (medium effort).** Switch the mobile
   models for the **server** ones (`*_server_rec` / `*_server_det`) in
   `PPStructureV3(...)` inside `ocr_backend.py`, and add Folio-OCR
   post-processing (`_latex_to_unicode`, `_dedup_lines`) to clean accents.

3. **DeepSeek-style VLM backend (highest fidelity, highest cost).** Add an optional
   backend based on Surya, docling (DeepSeek OCR) or Folio/GLM-OCR, or implement
   the **LLM correction** pattern from marker (`LLMTableProcessor`): rough OCR
   -> send image + HTML to the LLM -> correct. This is what produces "perfect"
   results like DeepSeek's. See the next section for agent instructions.

**Suggested implementation order:** (1) markdownify conversion (done) ->
(2) PaddleOCR server model + Folio post-processing -> (3) optional VLM backend
for those who want maximum quality.


---

## Instructions for an AI Agent: implement the "VLM backend for ocr_backend.py"

This section is written for an AI coding agent (e.g. CodeBuddy, Copilot, or a
fork contributor) in case a developer wants to add a VLM-based OCR backend to
ksnip_py. The goal is to reach DeepSeek-level fidelity for table/Markdown OCR by
letting a vision-language model read the screenshot directly, instead of (or as a
correction step on top of) the PaddleOCR mobile recognition model.

### Goal

Add a new **optional** backend (e.g. `vlm`) to `OcrBackend.recognize_file` that
sends the screenshot image and returns Markdown. It must be opt-in and must never
break the app when its (heavy) dependencies are absent.

### Where to hook in

- `ksnip_py/ocr_backend.py`:
  - `OcrOptions` dataclass: add a field only if the backend needs config (API key,
    base URL, model name, prompt). Keep sensible defaults so existing callers are
    unaffected.
  - The backend dispatch constants near the top
    (`_PRIMARY_BACKEND`, `_STRUCTURE_BACKEND`, `_STRUCTURE_HTML_BACKEND`,
    `_SCRIPT_BACKEND`) -- add `_VLM_BACKEND = "vlm"` and a branch in
    `recognize_file`.
  - Add a `_recognize_with_vlm(image_path, options)` method. Use **lazy imports**
    inside it so the module imports cleanly even when the VLM SDK is not installed.
- `ksnip_py/settings_dialog.py`: expose the new backend in the OCR backend
  selector (and any new options). Mirror how `paddleocr_structure` is surfaced.
- `requirements-ocr.txt`: add the optional dependency under a clearly marked
  optional group (e.g. a comment `# Optional VLM backend`), so the default install
  keeps working without it.

### Implementation options (reuse the research in this folder)

1. **External API (closest to DeepSeek).** POST the image to a vision OCR API
   (e.g. DeepSeek OCR) and parse the Markdown/HTML it returns. Reference:
   `docling/utils/deepseekocr_utils.py::_parse_table_html` shows how to robustly
   parse DeepSeek OCR's annotated Markdown/HTML table output (uses `lxml`).
   - Pros: highest fidelity, small local footprint.
   - Cons: needs an API key and network access; the image leaves the machine.
2. **Local via Ollama (Folio-OCR pattern).** Run GLM-OCR (or any Ollama VLM)
   locally and send the screenshot; parse its Markdown. See `folio_ocr/server.py`
   (`_postprocess`, `_latex_to_unicode`, `_TableParser`) for reusable
   post-processing.
   - Pros: offline / private.
   - Cons: large model download; Ollama must be installed.
3. **Local VLM (Surya / docling).** Load a VLM with `torch>=2.7` /
   `transformers>=5.12`. See `surya/inference/parsers.py`
   (`parse_full_page_html`, `clean_block_html`) and docling's VLM pipelines.
   - Pros: offline.
   - Cons: heavy dependencies and GPU/CPU cost.
4. **LLM-correction pattern (marker).** Keep PaddleOCR for the rough table, then
   send the image + its HTML to an LLM (e.g. Gemini) to correct it -- this is
   exactly how DeepSeek "fixes" the OCR. See
   `marker/processors/llm/llm_table.py::LLMTableProcessor`.

### Hard requirements

- **Lazy imports:** every VLM-specific import must live inside the new method (or be
  guarded) so `import ksnip_py.ocr_backend` never fails on a machine without the
  VLM SDK.
- **Graceful failure:** if the dependency or API is missing, raise
  `OcrMissingDependencyError` (already defined in `ocr_backend.py`) with an
  install hint, or fall back to an existing backend. Do NOT crash the UI.
- **Markdown hygiene:** returned Markdown still passes through
  `_html_tables_to_markdown` when it contains HTML tables, so the wrapper-stripping
  and `markdownify` conversion already in place will clean it.
- **Licenses:** Folio-OCR (MIT), PaddleOCR/surya/marker (Apache-2.0) and docling
  (MIT) code may be reused. **Do NOT copy OCRmyPDF code** -- it is MPL-2.0
  (file-level copyleft); it is irrelevant here anyway.

### Tests

- Add backend tests under `tests_py/test_ocr_backend.py` (alongside the existing
  wrapper regression tests). Use the same `unittest` style and the `_FakeResult`
  / `patch.dict(sys.modules, {...})` pattern used by `test_ocr_structure.py`, so
  the new backend can be tested without the real VLM SDK installed (mock the SDK
  import or the network call).
- Ensure `python3 -m pytest tests_py/` still passes on a machine without the VLM
  dependencies.

### Suggested first cut

Start with option 1 (API) behind a clearly optional setting, because it needs the
least local machinery and demonstrates the fidelity gain fastest. Then, if offline
support is desired, layer in option 2 or 3.

