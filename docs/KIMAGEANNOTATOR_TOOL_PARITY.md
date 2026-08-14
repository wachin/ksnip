# kImageAnnotator tool parity matrix

## Scope and preservation rule

This is a read-only audit of the C++ code under `libraries/kImageAnnotator/`
and the current PyQt6 implementation. No annotation behavior was changed while
preparing it.

The PyQt6 editor contains intentional user-requested behavior that is now part
of the protected baseline. A difference from C++ is not automatically a bug.
Any future change affecting creation geometry, appearance, controls, selection,
editing, numbering, serialization, SVG output, or sticker behavior must first
be described to the project owner and approved.

Status terminology:

- **Complete**: the normal workflow exists in the port.
- **Customized**: complete, with intentional behavior that must be preserved.
- **Raster operation**: applied to the background rather than retained as a
  selectable overlay.
- **Review**: present, but a specific parity detail has no focused automated
  test or differs structurally from C++.

## Tool inventory

All 21 entries from the C++ `Tools` enum have a PyQt6 counterpart. `Crop` and
`Cut` are also exposed by the Python canvas as operations rather than C++ enum
annotation items.

| C++ / PyQt6 tool | Creation and preview | Selection and editing | Undo / redo | `.ksnip` | SVG | Audit status and protected details |
| --- | --- | --- | --- | --- | --- | --- |
| Select | Existing items and multi-selection | Move, resize, handles, delete, duplicate, ordering and property editing | Yes | N/A | N/A | **Customized**: multi-selection and current hit-testing/handle behavior are protected |
| Pen | Freehand point path | Move, path handles and shared properties | Yes | Vector points | Editable polyline | **Complete**; opacity and shadow have focused tests |
| Marker Pen | Translucent freehand path | Move, handles and color/width | Yes | Vector points | Editable polyline with multiply style | **Customized**: multiply composition, fixed translucency and no shadow are tested |
| Marker Rectangle | Dragged filled region | Move/resize | Yes | Vector item | Editable rectangle | **Customized**: filled, borderless, translucent multiply rendering is tested |
| Marker Ellipse | Dragged filled region | Move/resize | Yes | Vector item | Editable ellipse | **Customized**: same protected marker behavior as Marker Rectangle |
| Line | Dragged line | Endpoint handles, move, width/color/opacity/shadow | Yes | Vector item | Editable line | **Complete** |
| Arrow | Dragged arrow | Endpoint handles and shared line properties | Yes | Vector item | Editable line plus marker | **Complete**; regular head size remains derived from shaft width |
| Double Arrow | Dragged double-ended arrow | Endpoint handles and shared line properties | Yes | Vector item | Editable line plus two markers | **Complete** |
| Rectangle | Dragged shape | Move/resize, border/fill colors and fill mode | Yes | Vector item | Editable rectangle | **Complete**; separate fill color is stored in `.ksnip` |
| Ellipse | Dragged shape | Move/resize, border/fill colors and fill mode | Yes | Vector item | Editable ellipse | **Complete**; separate fill color is stored in `.ksnip` |
| Number | Click insertion beginning at 1 | Number, font, styles, colors, fill, size and move/resize | Yes | Vector item and seed | Editable ellipse/text | **Customized**: per-canvas numbering, font-driven badge resizing and seed behavior are protected and tested |
| Number Pointer | Click/drag pointer | Pointer geometry, number/font/styles/colors and handles | Yes | Vector item and seed | Editable ellipse/text | **Customized**: circle centered on initial click, both drag directions, real preview and visible-geometry hit testing are protected and tested |
| Number Arrow | Click/drag badge plus arrow | Number/font/styles/fill, independent shaft width and arrowhead size | Yes | Vector item, seed and head size | Editable badge/line/text with sized marker | **Customized**: independent shaft/head/font controls and immediate editing are protected and tested |
| Text | Click then inline multiline editor | Re-edit, font, bold/italic/underline, colors, fill, resize and spell checking | Yes | Vector text data | Editable text/shape | **Customized**: inline editor, multiline behavior and Hunspell integration are protected |
| Text Pointer | Dragged callout with inline text | Re-edit, pointer handles, fonts/styles/colors and shadow | Yes | Vector item | Editable shape/text | **Customized**: visible-geometry handles/hit testing and tool-color fill are protected and tested |
| Text Arrow | Dragged label plus arrow | Re-edit, endpoint/label selection, fonts/styles/fill/width | Yes | Vector item | Editable shape/line/text | **Customized**: multiline bounds and borderless-label arrow visibility are protected and tested |
| Blur | Dragged region | Not retained as an overlay | Yes, as background snapshot | Raster background | Rasterized in embedded background | **Raster operation**; unlike C++, it is destructive to the current background layer but undoable |
| Pixelate | Dragged region | Not retained as an overlay | Yes, as background snapshot | Raster background | Rasterized in embedded background | **Raster operation**; same structural difference as Blur |
| Image | Inserted by paste, capture cursor, watermark or embedded image workflows | Move/resize, opacity, shadow and scaling | Yes | Embedded PNG item | Embedded PNG image | **Complete**; insertion is workflow-driven rather than a standalone blank drawing tool |
| Sticker | Click insertion from themed/user collection | Move/resize, opacity, shadow, scale and replace sticker | Yes | Embedded PNG plus source path | Embedded PNG image | **Customized**: themes, favorites, user imports, last tab, smooth resizing and normalized sizes are protected and tested |
| Duplicate | Click/drag duplication of composed scene content | Move/resize and opacity | Yes | Embedded PNG item | Embedded PNG image | **Customized**: captures composed scene content and remains selected; behavior is tested |
| Crop | Dragged rectangular operation | Not retained as an overlay | Yes | Resulting background/items | Resulting background/items | **Complete operation**, not a `Tools` enum entry in current C++ kImageAnnotator |
| Cut | Dragged axis slice operation | Not retained as an overlay | Yes | Resulting background/items | Resulting background/items | **Complete operation**, with explicit horizontal/vertical behavior tested |

## Shared editing and persistence audit

The following cross-tool functionality is already present:

- single and multiple selection;
- move and tool-specific resize handles;
- delete, duplicate, copy/paste item, bring to front, and send to back;
- undo/redo snapshots for creation and property changes;
- color, text color, width, font family/size, bold, italic, underline,
  opacity, fill mode, shadow, scaling, sticker replacement, and number changes
  where applicable;
- `.ksnip` serialization of kind, geometry, colors, width, independent number
  arrowhead size, text/font/styles, opacity, fill mode, shadow, scaling, sticker
  path, embedded image, and freehand points;
- SVG vector output for lines, paths, shapes, text/number variants and arrows,
  with raster embedding for image-like items.

The existing project round-trip test verifies background, item metadata and
canvas state. Focused tests cover the most heavily customized number, pointer,
text, marker, sticker, crop/cut, image-effect, scaling and geometry behavior.

## Findings requiring approval before any implementation

These are audit observations only. Nothing below was changed:

1. **Blur and Pixelate architecture** — C++ keeps selectable obfuscation items;
   PyQt6 applies undoable raster changes to the background. Converting them to
   overlays would alter projects, editing and rendering.
2. **Pen smoothing** — C++ exposes smooth-path configuration and a smoothing
   factor. PyQt6 preserves the captured points directly. Adding smoothing would
   change existing strokes visually.
3. **SVG fidelity** — the exporter preserves the main editable geometry, but
   item shadows are not represented as SVG filters; multiline text does not use
   per-line `tspan` elements; and rectangle/ellipse SVG fill should be audited
   visually against their separately stored fill color.
4. **Regular arrow heads** — regular Arrow and Double Arrow derive head size
   from shaft width. Only the customized Number Arrow has an independent head
   control.
5. **Focused coverage** — several basic tools are exercised indirectly rather
   than by one creation/edit/round-trip test per matrix row. Tests can be added
   without changing behavior and should precede any implementation work.

## Safe next step

The next safe activity is test-only: add characterization tests that freeze the
current appearance, geometry, selection, editing, `.ksnip`, and SVG behavior of
each tool. Any behavioral proposal from the findings above must remain a
separate, explicitly approved task.
