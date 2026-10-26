# Carpeta `external/`

Esta carpeta contiene clones **locales** de repositorios de OCR / análisis de
documentos que se investigaron para mejorar el reconocimiento de tablas y la
conversión imagen → Markdown dentro de **ksnip_py** (el puerto PyQt6 de ksnip).

> **Importante (git):** la carpeta `external/` está en `.gitignore`
> (sección `# Personal` → `external`). Los clones de los repositorios NO se
> suben al repo. Solo este `README.md` se fuerza a commitear con
> `git add -f external/README.md` para que cualquier usuario que clone ksnip
> sepa qué se estudió aquí y por qué.

---

## Por qué existe esta carpeta

`ksnip_py` convierte capturas de tablas a Markdown usando la pipeline
`PP-StructureV3` de PaddleOCR (ver `ksnip_py/ocr_backend.py`,
`_recognize_with_pp_structure`). La conversión a Markdown funciona, pero la
**calidad del reconocimiento** (acentos/diacríticos turcos y españoles perdidos,
espaciado de palabras) queda por debajo de la de modelos de visión tipo
DeepSeek. Se clonaron estos 6 repos para buscar código reutilizable que mejore:

1. El reconocimiento de tablas (layout + structure).
2. La conversión imagen → Markdown en general.

---

## Repositorios investigados

| Repo | Licencia | Enfoque | ¿Qué aporta a ksnip_py? | Costo de integración |
|------|----------|---------|-------------------------|----------------------|
| [Folio-OCR](#1-folio-ocr) | MIT | GLM-OCR (VLM vía Ollama) + PP-DocLayoutV3 | Post-procesado robusto reutilizable | Medio (Ollama + modelo) |
| [PaddleOCR](#2-paddleocr) | Apache-2.0 | Ya es el backend actual | Confirma que la tabla sale en HTML | Bajo (ya integrado) |
| [surya](#3-surya) | Apache-2.0 | VLM único (layout+OCR+tabla) | Parser HTML→estructura (BeautifulSoup) | Alto (torch>=2.7) |
| [marker](#4-marker) | Apache-2.0 | Wrapper de Surya + render MD | `markdownify` para HTML→MD fiable + corrección LLM | Alto (torch + Surya) |
| [docling](#5-docling) | MIT | Pipelines VLM (incl. DeepSeek OCR) | Parser de HTML de tabla de DeepSeek | Alto (torch/onnx) |
| [OCRmyPDF](#6-ocrmypdf) | MPL-2.0 (copyleft) | Tesseract sobre capa PDF | No aplica (no hace tabla→MD) | — |

---

## 1. Folio-OCR

- **URL:** https://github.com/vorojar/Folio-OCR
- **Licencia:** MIT (reutilizable libremente).
- **Enfoque:** OCR de documentos con `PP-DocLayoutV3` para layout y **GLM-OCR**
  (un modelo de visión grande) servido vía **Ollama** para el OCR real.
  Convierte a Markdown/TXT/DOCX/EPUB.

**Código reutilizable en `folio_ocr/server.py`:**

- `_postprocess()` (server.py:677) orquesta la limpieza del Markdown resultante.
- `_latex_to_unicode()` / `_convert_math_interior()` (server.py:820+) convierte
  comandos LaTeX y acentos a Unicode plano. **Útil para el problema de
  diacríticos perdidos** (á, í, ç, ı, ğ…).
- `class _TableParser(HTMLParser)` (server.py:1319) extrae filas/celdas de un
  `<table>` HTML respetando `<th>` como fila de encabezado de forma robusta
  (mejor que los regex actuales de ksnip_py).
- `_preserve_html_tables()` (server.py:708) aplica transformaciones solo fuera
  de los bloques `<table>`, y `_remove_empty_html_tables()` (server.py:690)
  elimina "conchas" de tabla vacías que alucina el modelo.
- `_dedup_lines()` (server.py:735+) quita líneas duplicadas.

**Conclusión:** el OCR en sí (GLM-OCR) requiere Ollama + un modelo pesado, pero
su **post-procesado es copiable tal cual** a `ksnip_py` para mejorar la
limpieza de Markdown y el manejo de `<th>`.

---

## 2. PaddleOCR

- **URL:** https://github.com/PaddlePaddle/PaddleOCR
- **Licencia:** Apache-2.0.
- **Enfoque:** Es el backend que **ya usa ksnip_py**.

**Hallazgo clave (`ppstructure/recovery/recovery_to_markdown.py`):**

- `convert_info_markdown()` (línea 129) inserta la tabla directamente como
  HTML: `markdown_string.append(region["res"]["html"])`. O sea: **la tabla
  sale en HTML y la conversión a Markdown es responsabilidad del llamador**.
- `replace_special_char()` (línea 141) escapa `*`, `` ` ``, `~`, `$` para que el
  Markdown no se rompa.

**Conclusión:** esto confirma que el eslabón débil de ksnip_py está en su
propia función `_html_tables_to_markdown` / `_simple_html_table_to_markdown`
(`ksnip_py/ocr_backend.py`), no en PaddleOCR. Mejorar esa conversión (ver
marker abajo) y, sobre todo, la **calidad del modelo de reconocimiento**, es el
camino. La estructura de la tabla (incluida la fila de encabezado) se conserva
bien; lo que falla es el OCR de los caracteres con tilde.

---

## 3. surya

- **URL:** https://github.com/datalab-to/surya
- **Licencia:** Apache-2.0.
- **Enfoque:** Surya 2 corre layout, OCR y reconocimiento de tablas con un
  **único modelo de visión** (VLM). Dependencias pesadas:
  `torch>=2.7.0,<3`, `transformers>=5.12.1` (pyproject.toml).

**Código reutilizable en `surya/inference/parsers.py`:**

- `parse_full_page_html()` (usa BeautifulSoup) parsea los `<div data-bbox
  data-label>` que emite el modelo y extrae el HTML interno de cada bloque.
- `clean_block_html()` limpia cercas de código del HTML emitido.
- `parse_table_rec()` / `parse_layout()` toleran JSON mal formado.

Las tablas salen como `<table>...</table>` HTML; aún haría falta un
conversor HTML→Markdown.

**Conclusión:** backend alternativo de alta fidelidad (cercano a DeepSeek) pero
requiere torch + transformers pesados. Sus parsers BeautifulSoup son reutilizables
si se quiere un backend VLM.

---

## 4. marker

- **URL:** https://github.com/datalab-to/marker
- **Licencia:** Apache-2.0.
- **Enfoque:** Wrapper sobre **Surya** con un pipeline de conversión
  documento→Markdown muy pulido (PDFs, pero su lógica de tabla es exportable).

**Código reutilizable:**

- `marker/renderers/markdown.py` → `class Markdownify(MarkdownConverter)`
  hereda de la librería **`markdownify`** (BeautifulSoup → Markdown). Esta es
  una conversión HTML→Markdown **robusta que respeta `<th>`/`rowspan`/`colspan`
  y produce tablas pipe-Markdown correctas**. Reemplazaría con ventaja la
  conversión regex/pandoc actual de ksnip_py.
- `marker/processors/table.py` → `clean_table_html()` (re-serializa con
  BeautifulSoup para balancear etiquetas truncadas) y `reconstruct_table_html()`
  (heurística CPU para reconstruir la rejilla de una tabla).
- `marker/processors/llm/llm_table.py` → `LLMTableProcessor` envía la imagen de
  la tabla y su HTML a un **LLM (Gemini)** para corregir errores y que las
  cabeceras coincidan con las columnas. **Este es exactamente el enfoque de
  DeepSeek**: el VLM corrige el OCR contra la imagen.

**Conclusión:** dos aportes inmediatos — (a) usar `markdownify` para la
conversión HTML→Markdown fiable, y (b) un patrón de "corrección por LLM" para
llevar la precisión al nivel de DeepSeek.

---

## 5. docling

- **URL:** https://github.com/docling-project/docling
- **Licencia:** MIT.
- **Enfoque:** Pipelines de conversión; incluye backends VLM (Granite Vision,
  Nemotron-Parse, **DeepSeek OCR**, PaddleOCR-VL). Dependencias:
  `torch>=2.2.2`, `onnxruntime`, `transformers>=5.16`.

**Código reutilizable en `docling/utils/deepseekocr_utils.py`:**

- `_parse_table_html()` parsea el formato Markdown anotado que devuelve
  **DeepSeek OCR** y lo convierte a una estructura `TableData` (usa `lxml`).
  Directamente relevante: muestra cómo parsear de forma robusta el HTML de una
  tabla (filas, celdas, cabeceras) que produce un VLM tipo DeepSeek.
- También existen `docling/utils/paddleocr_vl_utils.py` y
  `docling/models/stages/table_structure/table_structure_model_granite_vision.py`.

**Conclusión:** el parser de tablas de DeepSeek OCR es el ejemplo de referencia
para integrar un VLM de alta precisión y convertir su salida a Markdown/Tabla.

---

## 6. OCRmyPDF

- **URL:** https://github.com/ocrmypdf/OCRmyPDF
- **Licencia:** **MPL-2.0 (copyleft fuerte a nivel de archivo)** — precaución si
  se copia código dentro de ksnip (GPL-friendly, pero el archivo copiado debe
  seguir siendo MPL-2.0).
- **Enfoque:** herramienta de línea de comandos que añade una capa de texto
  OCR (Tesseract) a PDFs existentes. **No hace reconocimiento de tablas ni
  conversión a Markdown**; su noción de "tabla" es solo posicionamiento de
  cajas de texto para renderizar sobre el PDF.

**Conclusión:** el menos relevante para el objetivo de ksnip_py. Se mantiene
aquí solo por completitud de la investigación.

---

## Diagnóstico y recomendaciones para ksnip_py

El gap de precisión frente a DeepSeek **no está en la conversión a Markdown**
(la estructura de la tabla, incluida la fila de encabezado, se conserva bien en
ksnip_py). El problema es la **calidad del modelo de reconocimiento**
(`PP-OCRv5_mobile_rec` pierde diacríticos como ı, ç, ğ, ö, ü y el espaciado de
palabras, p.ej. "Ones et al." → "Oneset al.", "Altınkılıç" → "Altinkls").

Tres caminos, de menor a mayor esfuerzo:

1. **Robustecer la conversión HTML→Markdown (bajo esfuerzo).** Reemplazar
   `_html_tables_to_markdown` / `_simple_html_table_to_markdown` en
   `ocr_backend.py` por la librería **`markdownify`** (misma que usa marker),
   que respeta `<th>` y estructura de tabla. Elimina casos borde de la fila de
   encabezado y no depende de `pandoc`.

2. **Mejorar el modelo de reconocimiento PaddleOCR (esfuerzo medio).** Cambiar
   los modelos móviles por los **server** (`*_server_rec` / `*_server_det`) en
   `PPStructureV3(...)` dentro de `ocr_backend.py`, y añadir el post-procesado
   de Folio-OCR (`_latex_to_unicode`, `_dedup_lines`) para limpiar acentos.

3. **Backend VLM tipo DeepSeek (mayor fidelidad, mayor costo).** Añadir un
   backend opcional basado en Surya, docling (DeepSeek OCR) o Folio/GLM-OCR, o
   implementar el patrón de **corrección por LLM** de marker
   (`LLMTableProcessor`): OCR tosco → enviar imagen + HTML al LLM → corregir.
   Esto es lo que produce resultados "perfectos" como los de DeepSeek.

**Orden sugerido de implementación:** (1) `markdownify` para la conversión →
(2) modelo server de PaddleOCR + post-procesado de Folio → (3) backend VLM
opcional para quien quiera calidad máxima.

