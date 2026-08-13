#!/usr/bin/env python3
"""Extract the Geeko contact sheet into named transparent sticker PNGs."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


ROWS = (
    ((0, 142), (90, 255, 425, 595, 765, 940, 1110, 1280, 1450)),
    ((142, 274), (90, 255, 425, 595, 765, 940, 1110, 1280, 1450)),
    ((274, 414), (90, 255, 425, 595, 765, 940, 1110, 1280, 1450)),
    ((414, 536), (90, 255, 425, 595, 765, 940, 1110, 1280, 1450)),
    ((536, 661), (90, 270, 440, 610, 790, 970, 1260, 1450)),
    ((661, 766), (90, 255, 425, 595, 765, 940, 1110, 1280, 1450)),
    ((766, 887), (70, 220, 370, 520, 670, 820, 970, 1120, 1270, 1440)),
    ((887, 1024), (70, 220, 370, 520, 670, 820, 970, 1120, 1270, 1440)),
)

STICKER_NAMES = (
    "geeko_greeting", "geeko_walking", "geeko_waving", "geeko_dancing",
    "geeko_in_love", "geeko_hugging_heart", "geeko_blowing_a_kiss",
    "geeko_heart_eyes", "geeko_sleeping",
    "geeko_laptop", "geeko_idea", "geeko_listening_to_music", "geeko_party",
    "geeko_cool", "geeko_angel", "geeko_devil", "geeko_crying", "geeko_shy",
    "geeko_ninja", "geeko_pirate", "geeko_detective", "geeko_scientist",
    "geeko_artist", "geeko_explorer", "geeko_binoculars", "geeko_archaeologist",
    "geeko_chef",
    "geeko_kde_laptop", "geeko_desktop_computer", "geeko_programming",
    "geeko_terminal", "geeko_drawing_tablet", "geeko_keyboard", "geeko_mouse",
    "geeko_system_tools", "geeko_toolbox",
    "geeko_swearing", "geeko_question", "geeko_thinking", "geeko_tip",
    "geeko_information", "geeko_approval", "geeko_rejection", "geeko_warning",
    "geeko_cloud", "geeko_server", "geeko_database", "geeko_folder",
    "geeko_download", "geeko_upload", "geeko_sync", "geeko_security",
    "geeko_system_settings",
    "geeko_relaxing", "geeko_sleeping_on_leaf", "geeko_in_the_rain",
    "geeko_surfing", "geeko_skateboarding", "geeko_cycling", "geeko_driving",
    "geeko_rocket", "geeko_lucky", "geeko_ladybug",
    "geeko_behind_leaf", "geeko_on_branch", "geeko_with_map", "geeko_camera",
    "geeko_hiking", "geeko_winter", "geeko_guitar", "geeko_dj",
    "geeko_painting", "geeko_with_heart",
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
        labels, component_count = ndimage.label(row[:, :, 3] > ALPHA_THRESHOLD)
        assignments: list[list[int]] = [[] for _ in centers]
        for label in range(1, component_count + 1):
            _, xs = np.where(labels == label)
            if xs.size < MIN_COMPONENT_PIXELS:
                continue
            column = min(range(len(centers)), key=lambda index: abs(float(xs.mean()) - centers[index]))
            assignments[column].append(label)
        masks = [np.isin(labels, component_labels) for component_labels in assignments]

        # The generated sheet occasionally joins two neighbouring subjects
        # through a glow or prop. Split only an empty target from the nearest
        # shared component; all ordinary subjects retain complete components.
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

        # In the last row, the hiking and winter scenes touch each other and
        # therefore form one alpha component. Split just that shared component
        # at the clear visual gap between both subjects.
        if top == 887 and not assignments[4]:
            shared = masks[5].copy()
            x_coordinates = np.arange(row.shape[1])[None, :]
            masks[4] = shared & (x_coordinates < 790)
            masks[5] = shared & (x_coordinates >= 790)

        for mask in masks:
            sticker = np.zeros_like(row)
            sticker[mask] = row[mask]
            sticker[:, :, 3] = np.where(sticker[:, :, 3] <= ALPHA_THRESHOLD, 0, sticker[:, :, 3])
            output = output_dir / f"{STICKER_NAMES[sticker_number]}.png"
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
