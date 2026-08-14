#!/usr/bin/env python3
"""Extract the GNU Baby contact sheet into named transparent sticker PNGs."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


ROWS = (
    ((0, 201), (95, 285, 475, 670, 865, 1060, 1250, 1440)),
    ((201, 374), (80, 260, 440, 620, 800, 980, 1150, 1320, 1480)),
    ((374, 534), (100, 300, 500, 700, 900, 1080, 1260, 1450)),
    ((534, 685), (100, 300, 500, 700, 900, 1080, 1260, 1450)),
    ((685, 848), (100, 300, 500, 700, 900, 1080, 1260, 1450)),
    ((848, 1024), (75, 205, 325, 445, 555, 650, 745, 840, 930, 1020, 1105, 1190, 1280, 1370, 1450, 1510)),
)

STICKER_NAMES = (
    "gnubaby_greeting", "gnubaby_winking", "gnubaby_laughing",
    "gnubaby_celebrating", "gnubaby_hugging_heart", "gnubaby_angel",
    "gnubaby_devil", "gnubaby_crying",
    "gnubaby_question", "gnubaby_thinking", "gnubaby_idea",
    "gnubaby_shy", "gnubaby_blowing_a_kiss", "gnubaby_cool",
    "gnubaby_party", "gnubaby_listening_to_music", "gnubaby_reading",
    "gnubaby_laptop", "gnubaby_desktop_computer", "gnubaby_terminal",
    "gnubaby_ninja", "gnubaby_pirate", "gnubaby_scientist",
    "gnubaby_artist", "gnubaby_detective",
    "gnubaby_sleeping", "gnubaby_sick", "gnubaby_coffee",
    "gnubaby_watching_movie", "gnubaby_gaming", "gnubaby_love_letter",
    "gnubaby_hero", "gnubaby_running",
    "gnubaby_business", "gnubaby_presentation", "gnubaby_programming",
    "gnubaby_system_tools", "gnubaby_rocket", "gnubaby_in_the_rain",
    "gnubaby_thoughtful", "gnubaby_hiding",
    "gnubaby_approval", "gnubaby_rejection", "gnubaby_warning",
    "gnubaby_information", "gnubaby_next_step", "gnubaby_previous_step",
    "gnubaby_upload", "gnubaby_download", "gnubaby_command_line",
    "gnubaby_code", "gnubaby_folder", "gnubaby_document",
    "gnubaby_search", "gnubaby_settings", "gnubaby_delete",
    "gnubaby_help",
)

CANVAS_SIZE = 256
ARTWORK_SIZE = 232
ALPHA_THRESHOLD = 8
MIN_COMPONENT_PIXELS = 100


def _fit_on_canvas(image: Image.Image) -> Image.Image:
    bounds = image.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError("Extracted sticker is empty")
    cropped = image.crop(bounds)
    scale = min(ARTWORK_SIZE / cropped.width, ARTWORK_SIZE / cropped.height)
    size = (max(1, round(cropped.width * scale)), max(1, round(cropped.height * scale)))
    cropped = cropped.resize(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    canvas.alpha_composite(cropped, ((CANVAS_SIZE - size[0]) // 2, (CANVAS_SIZE - size[1]) // 2))
    return canvas


def _row_masks(
    row: np.ndarray, centers: tuple[int, ...], *, use_geometric_cells: bool = False
) -> list[np.ndarray]:
    if use_geometric_cells:
        x_coordinates = np.arange(row.shape[1])
        boundaries = [(left + right) // 2 for left, right in zip(centers, centers[1:])]
        owners = np.digitize(x_coordinates, boundaries)
        masks = []
        for column in range(len(centers)):
            mask = np.broadcast_to(owners == column, row.shape[:2]) & (
                row[:, :, 3] > ALPHA_THRESHOLD
            )
            labels, component_count = ndimage.label(mask)
            if component_count:
                sizes = np.bincount(labels.ravel())
                largest = 1 + int(np.argmax(sizes[1:]))
                mask = labels == largest
            masks.append(mask)
        return masks

    labels, component_count = ndimage.label(row[:, :, 3] > ALPHA_THRESHOLD)
    assignments: list[list[int]] = [[] for _ in centers]
    for label in range(1, component_count + 1):
        _, xs = np.where(labels == label)
        if xs.size < MIN_COMPONENT_PIXELS:
            continue
        column = min(range(len(centers)), key=lambda index: abs(float(xs.mean()) - centers[index]))
        assignments[column].append(label)
    masks = [np.isin(labels, component_labels) for component_labels in assignments]

    # Split a shared component only when a generated glow or prop joins two
    # neighbours and leaves one configured position empty.
    for column, component_labels in enumerate(assignments):
        if component_labels:
            continue
        donor = next(
            (
                neighbour
                for neighbour in (column - 1, column + 1)
                if 0 <= neighbour < len(centers) and assignments[neighbour]
            ),
            None,
        )
        if donor is None:
            continue
        midpoint = (centers[column] + centers[donor]) // 2
        shared = masks[donor].copy()
        x_coordinates = np.arange(row.shape[1])[None, :]
        if column < donor:
            masks[column] = shared & (x_coordinates < midpoint)
            masks[donor] = shared & (x_coordinates >= midpoint)
        else:
            masks[column] = shared & (x_coordinates >= midpoint)
            masks[donor] = shared & (x_coordinates < midpoint)
    return masks


def extract(source: Path, output_dir: Path) -> list[Path]:
    sheet = Image.open(source).convert("RGBA")
    if sheet.size != (1536, 1024):
        raise ValueError(f"Expected a 1536x1024 contact sheet, got {sheet.width}x{sheet.height}")
    if sum(len(centers) for _, centers in ROWS) != len(STICKER_NAMES):
        raise RuntimeError("Sticker names do not match the configured grid")

    pixels = np.asarray(sheet)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    sticker_number = 0
    for (top, bottom), centers in ROWS:
        row = pixels[top:bottom]
        for mask in _row_masks(row, centers, use_geometric_cells=top == 848):
            output = output_dir / f"{STICKER_NAMES[sticker_number]}.png"
            # The 16 tightly packed utility designs in the bottom source row
            # overlap and cannot be reconstructed by cropping. Preserve the
            # individually regenerated replacements when they already exist.
            if sticker_number >= 41 and output.exists():
                outputs.append(output)
                sticker_number += 1
                continue
            sticker = np.zeros_like(row)
            sticker[mask] = row[mask]
            sticker[:, :, 3] = np.where(sticker[:, :, 3] <= ALPHA_THRESHOLD, 0, sticker[:, :, 3])
            _fit_on_canvas(Image.fromarray(sticker, "RGBA")).save(output, "PNG", optimize=True)
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
