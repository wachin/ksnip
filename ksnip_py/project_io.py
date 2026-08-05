from __future__ import annotations

import base64
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice
from PyQt6.QtGui import QColor, QImage


PROJECT_SCHEMA = "org.ksnip.ksnip-py.project"
PROJECT_VERSION = 1
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)


def _image_png_bytes(image: QImage) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise ValueError("Unable to encode project image as PNG")
    return bytes(data)


def save_project(path: str, canvas) -> None:
    metadata = canvas.project_metadata()
    metadata.update({"schema": PROJECT_SCHEMA, "version": PROJECT_VERSION})
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("project.json", json.dumps(metadata, ensure_ascii=False, indent=2))
        archive.writestr("background.png", _image_png_bytes(canvas.background_image()))


def load_project(path: str) -> tuple[QImage, dict]:
    try:
        with ZipFile(path, "r") as archive:
            metadata = json.loads(archive.read("project.json").decode("utf-8"))
            image_data = archive.read("background.png")
    except (BadZipFile, KeyError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("Invalid or damaged Ksnip project") from error
    if metadata.get("schema") != PROJECT_SCHEMA or metadata.get("version") != PROJECT_VERSION:
        raise ValueError("Unsupported Ksnip project version")
    image = QImage.fromData(image_data, "PNG")
    if image.isNull():
        raise ValueError("The Ksnip project background is invalid")
    return image, metadata


def _color(value: str | None, fallback: str = "#000000") -> tuple[str, float]:
    color = QColor(value or fallback)
    return color.name(QColor.NameFormat.HexRgb), color.alphaF()


def _png_data_uri(payload: str | None) -> str | None:
    return f"data:image/png;base64,{payload}" if payload else None


def export_svg(path: str, canvas) -> None:
    image = canvas.background_image()
    metadata = canvas.project_metadata()
    root = ET.Element(f"{{{SVG_NS}}}svg", {
        "width": str(image.width()), "height": str(image.height()),
        "viewBox": f"0 0 {image.width()} {image.height()}", "version": "1.1",
    })
    defs = ET.SubElement(root, f"{{{SVG_NS}}}defs")
    for marker_id, orient in (("arrow-end", "auto"), ("arrow-start", "auto-start-reverse")):
        marker = ET.SubElement(defs, f"{{{SVG_NS}}}marker", {
            "id": marker_id, "viewBox": "0 0 10 10", "refX": "9", "refY": "5",
            "markerWidth": "4", "markerHeight": "4", "orient": orient,
        })
        ET.SubElement(marker, f"{{{SVG_NS}}}path", {"d": "M 0 0 L 10 5 L 0 10 z", "fill": "context-stroke"})
    background_uri = "data:image/png;base64," + base64.b64encode(_image_png_bytes(image)).decode("ascii")
    ET.SubElement(root, f"{{{SVG_NS}}}image", {
        "x": "0", "y": "0", "width": str(image.width()), "height": str(image.height()),
        f"{{{XLINK_NS}}}href": background_uri,
    })

    for item in metadata.get("items", []):
        kind = item.get("kind", "")
        x1, y1 = item["start"]
        x2, y2 = item["end"]
        stroke, stroke_alpha = _color(item.get("color"))
        text_color, text_alpha = _color(item.get("text_color"), "#ffffff")
        width = max(1, int(item.get("pen_width", 1)))
        opacity = float(item.get("opacity", 1.0))
        fill_mode = item.get("fill_mode", "border_and_fill")
        has_border = fill_mode in {"border_and_fill", "border_and_no_fill"}
        has_fill = fill_mode in {"border_and_fill", "no_border_and_fill"}
        common = {"opacity": str(opacity)}
        line_style = {**common, "stroke": stroke, "stroke-opacity": str(stroke_alpha), "stroke-width": str(width), "fill": "none", "stroke-linecap": "round", "stroke-linejoin": "round"}
        if kind in {"line", "arrow", "double_arrow"}:
            attrs = {**line_style, "x1": str(x1), "y1": str(y1), "x2": str(x2), "y2": str(y2)}
            if kind in {"arrow", "double_arrow"}:
                attrs["marker-end"] = "url(#arrow-end)"
            if kind == "double_arrow":
                attrs["marker-start"] = "url(#arrow-start)"
            ET.SubElement(root, f"{{{SVG_NS}}}line", attrs)
        elif kind in {"pen", "marker_pen"} and item.get("points"):
            attrs = {**line_style, "points": " ".join(f"{x},{y}" for x, y in item["points"])}
            if kind == "marker_pen":
                attrs["stroke-opacity"] = "0.43"
                attrs["style"] = "mix-blend-mode:multiply"
            ET.SubElement(root, f"{{{SVG_NS}}}polyline", attrs)
        elif kind in {"rect", "marker_rect", "ellipse", "marker_ellipse"}:
            left, top, w, h = min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)
            attrs = {**common, "stroke": stroke if has_border else "none", "stroke-width": str(width), "fill": stroke if has_fill or kind.startswith("marker_") else "none"}
            if kind.startswith("marker_"):
                attrs.update({"fill-opacity": "0.43", "stroke": "none", "style": "mix-blend-mode:multiply"})
            if "ellipse" in kind:
                attrs.update({"cx": str(left + w / 2), "cy": str(top + h / 2), "rx": str(w / 2), "ry": str(h / 2)})
                ET.SubElement(root, f"{{{SVG_NS}}}ellipse", attrs)
            else:
                attrs.update({"x": str(left), "y": str(top), "width": str(w), "height": str(h)})
                ET.SubElement(root, f"{{{SVG_NS}}}rect", attrs)
        elif kind in {"text", "text_arrow", "text_pointer", "number", "number_pointer", "number_arrow"}:
            bounds = item.get("svg_bounds") or [min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)]
            bx, by, bw, bh = bounds
            if kind.endswith("arrow"):
                ET.SubElement(root, f"{{{SVG_NS}}}line", {**line_style, "x1": str(x1), "y1": str(y1), "x2": str(x2), "y2": str(y2), "marker-end": "url(#arrow-end)"})
            shape = "ellipse" if kind.startswith("number") else "rect"
            shape_attrs = {**common, "stroke": stroke if has_border else "none", "stroke-width": str(width), "fill": stroke if has_fill else "none"}
            if shape == "ellipse":
                shape_attrs.update({"cx": str(bx + bw / 2), "cy": str(by + bh / 2), "rx": str(bw / 2), "ry": str(bh / 2)})
            else:
                shape_attrs.update({"x": str(bx), "y": str(by), "width": str(bw), "height": str(bh), "rx": "6"})
            ET.SubElement(root, f"{{{SVG_NS}}}{shape}", shape_attrs)
            text_attrs = {
                **common, "x": str(bx + bw / 2), "y": str(by + bh / 2), "fill": text_color,
                "fill-opacity": str(text_alpha), "font-family": item.get("font_family") or "sans-serif",
                "font-size": str(item.get("font_point_size") or 15), "text-anchor": "middle",
                "dominant-baseline": "middle", "font-weight": "bold" if item.get("bold") else "normal",
                "font-style": "italic" if item.get("italic") else "normal",
            }
            if item.get("underline"):
                text_attrs["text-decoration"] = "underline"
            ET.SubElement(root, f"{{{SVG_NS}}}text", text_attrs).text = item.get("text") or ""
        elif kind in {"image", "sticker", "duplicate"}:
            uri = _png_data_uri(item.get("image_png_base64"))
            if uri:
                ET.SubElement(root, f"{{{SVG_NS}}}image", {
                    **common, "x": str(min(x1, x2)), "y": str(min(y1, y2)),
                    "width": str(abs(x2 - x1)), "height": str(abs(y2 - y1)), f"{{{XLINK_NS}}}href": uri,
                })

    Path(path).write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))
