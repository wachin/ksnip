#!/usr/bin/env python3
"""Extract the Konqi & Katie contact sheet into transparent sticker PNGs."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


X_CENTERS = (100, 270, 440, 610, 780, 950, 1120, 1290, 1450)
Y_RANGES = ((0, 195), (195, 385), (385, 565), (565, 730), (730, 900), (900, 1024))
ROW_COLUMNS = (9, 9, 9, 9, 9, 2)
STICKER_NAMES = (
    "konqi_artist",
    "katie_fairy",
    "katie_sitting",
    "konqi_thumbs_up",
    "konqi_double_thumbs_up",
    "katie_angel",
    "konqi_clown",
    "konqi_welcoming",
    "konqi_injured",
    "katie_squirrel",
    "katie_in_love",
    "konqi_confident",
    "konqi_devil",
    "katie_blushing",
    "katie_hugging_heart",
    "katie_holding_heart",
    "konqi_ninja",
    "konqi_pirate",
    "konqi_shushing",
    "konqi_eating_burger",
    "konqi_sick",
    "katie_sleeping",
    "konqi_laughing",
    "konqi_thinking",
    "konqi_presenting",
    "konqi_confused",
    "katie_confused",
    "konqi_swearing",
    "konqi_sitting",
    "konqi_standing",
    "konqi_laughing_seated",
    "katie_winking",
    "konqi_cool",
    "katie_surrounded_by_hearts",
    "konqi_hugging_heart",
    "konqi_crying",
    "konqi_approval",
    "konqi_rejection",
    "konqi_cursor",
    "konqi_keyboard",
    "konqi_warning",
    "konqi_next_step",
    "konqi_information",
    "katie_question",
    "konqi_tip",
    "konqi_drawing_tablet",
    "konqi_terminal",
)
CANVAS_SIZE = 256
ARTWORK_SIZE = 232
ALPHA_THRESHOLD = 8
MIN_COMPONENT_PIXELS = 8


def _fit_on_canvas(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    bounds = alpha.getbbox()
    if bounds is None:
        raise ValueError("Extracted sticker is empty")
    cropped = image.crop(bounds)
    scale = min(ARTWORK_SIZE / cropped.width, ARTWORK_SIZE / cropped.height)
    size = (max(1, round(cropped.width * scale)), max(1, round(cropped.height * scale)))
    cropped = cropped.resize(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    canvas.alpha_composite(cropped, ((CANVAS_SIZE - size[0]) // 2, (CANVAS_SIZE - size[1]) // 2))
    return canvas


def extract(source: Path, output_dir: Path) -> list[Path]:
    sheet = Image.open(source).convert("RGBA")
    if sheet.size != (1536, 1024):
        raise ValueError(f"Expected a 1536x1024 contact sheet, got {sheet.width}x{sheet.height}")
    pixels = np.asarray(sheet)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    sticker_number = 1
    for (top, bottom), column_count in zip(Y_RANGES, ROW_COLUMNS):
        row = pixels[top:bottom]
        labels, component_count = ndimage.label(row[:, :, 3] > ALPHA_THRESHOLD)
        assignments: list[list[int]] = [[] for _ in range(column_count)]
        for label in range(1, component_count + 1):
            _, xs = np.where(labels == label)
            if xs.size < MIN_COMPONENT_PIXELS:
                continue
            column = min(
                range(column_count),
                key=lambda index: abs(float(xs.mean()) - X_CENTERS[index]),
            )
            assignments[column].append(label)

        for component_labels in assignments:
            mask = np.isin(labels, component_labels)
            sticker = np.zeros_like(row)
            sticker[mask] = row[mask]
            sticker[:, :, 3] = np.where(
                sticker[:, :, 3] <= ALPHA_THRESHOLD, 0, sticker[:, :, 3]
            )
            image = _fit_on_canvas(Image.fromarray(sticker, "RGBA"))
            output = output_dir / f"{STICKER_NAMES[sticker_number - 1]}.png"
            image.save(output, "PNG", optimize=True)
            outputs.append(output)
            sticker_number += 1

    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    outputs = extract(args.source, args.output_dir)
    print(f"Extracted {len(outputs)} stickers into {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
