#!/usr/bin/env python3
"""Generate the original GPL-3.0 SuperTux-inspired sticker collection."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "ksnip_py" / "stickers" / "themes" / "supertux"

HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<!-- Original ksnip_py artwork, GPL-3.0. No SuperTux game asset was copied. -->
"""


def face(eyes: str, mouth: str, extras: str = "") -> str:
    return HEADER + f"""<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <path d="M9 58 20 39h24l11 19-13-5-10 7-10-7z" fill="#e53935" stroke="#7f1715" stroke-width="2" stroke-linejoin="round"/>
  <ellipse cx="32" cy="30" rx="24" ry="27" fill="#202124"/>
  <ellipse cx="23" cy="28" rx="12" ry="16" fill="#f5f5dc"/><ellipse cx="41" cy="28" rx="12" ry="16" fill="#f5f5dc"/>
  <ellipse cx="32" cy="43" rx="17" ry="12" fill="#f5f5dc"/>
  {eyes}
  <path d="m25 34 7-5 7 5-7 7z" fill="#ff9800" stroke="#8a4b08" stroke-width="1.5" stroke-linejoin="round"/>
  {mouth}
  <circle cx="32" cy="55" r="3" fill="#ffd54f" stroke="#8a6500" stroke-width="1"/>
  {extras}
</svg>
"""


OPEN_EYES = '<circle cx="23" cy="25" r="3" fill="#202124"/><circle cx="41" cy="25" r="3" fill="#202124"/>'
SMILE = '<path d="M24 43q8 7 16 0" fill="none" stroke="#202124" stroke-width="2.5" stroke-linecap="round"/>'

FACES = {
    "confused_face": (
        '<circle cx="23" cy="25" r="3" fill="#202124"/><circle cx="41" cy="27" r="3" fill="#202124"/><path d="m17 18 11-2m8 1 10 4" stroke="#202124" stroke-width="2" stroke-linecap="round"/>',
        '<path d="M25 46q7-4 14 1" fill="none" stroke="#202124" stroke-width="2.5" stroke-linecap="round"/>',
        "",
    ),
    "face_blowing_a_kiss": (
        '<path d="M18 25q5-5 10 0" fill="none" stroke="#202124" stroke-width="2.5" stroke-linecap="round"/><circle cx="41" cy="25" r="3" fill="#202124"/>',
        '<path d="M27 45q5-5 10 0-5 4-10 0" fill="#ef5350" stroke="#202124" stroke-width="1.5"/>',
        '<path d="M50 36c-5-6-12 1 0 10 12-9 5-16 0-10z" fill="#ff6f91" stroke="#8f2946" stroke-width="1.5"/>',
    ),
    "face_savoring_food": (
        OPEN_EYES,
        '<path d="M23 43q9 8 18 0" fill="none" stroke="#202124" stroke-width="2.5"/><path d="M34 45q8 1 5 7-6 3-9-3" fill="#ef5350" stroke="#8f2946" stroke-width="1.5"/>',
        "",
    ),
    "face_with_symbols_on_mouth": (
        '<path d="m17 20 11 5m-11 0 11-5m9 0 9 5m-9 0 9-5" stroke="#202124" stroke-width="2.5" stroke-linecap="round"/>',
        '<rect x="20" y="41" width="24" height="10" rx="3" fill="#546e7a"/><path d="m23 48 4-5m1 5 4-5m3 5 4-5" stroke="#fff" stroke-width="1.7"/>',
        '<text x="48" y="19" font-size="10" font-weight="bold" fill="#e53935">#</text>',
    ),
    "grinning_face_with_big_eyes": (
        '<circle cx="23" cy="25" r="5" fill="#fff" stroke="#202124" stroke-width="2"/><circle cx="41" cy="25" r="5" fill="#fff" stroke="#202124" stroke-width="2"/><circle cx="23" cy="25" r="2"/><circle cx="41" cy="25" r="2"/>',
        '<path d="M21 42q11 14 22 0z" fill="#fff" stroke="#202124" stroke-width="2" stroke-linejoin="round"/>',
        "",
    ),
    "grinning_face_with_smiling_eyes": (
        '<path d="M17 26q6-7 12 0m6 0q6-7 12 0" fill="none" stroke="#202124" stroke-width="2.5" stroke-linecap="round"/>',
        '<path d="M21 42q11 14 22 0z" fill="#fff" stroke="#202124" stroke-width="2"/>',
        "",
    ),
    "grinning_face_with_sweat": (
        '<path d="M17 26q6-7 12 0m6 0q6-7 12 0" fill="none" stroke="#202124" stroke-width="2.5" stroke-linecap="round"/>',
        '<path d="M21 42q11 12 22 0z" fill="#fff" stroke="#202124" stroke-width="2"/>',
        '<path d="M52 11q-9 10 0 14 9-4 0-14z" fill="#42a5f5" stroke="#1769aa" stroke-width="1.5"/>',
    ),
    "grinning_squinting_face": (
        '<path d="m17 21 10 5-10 5m30-10-10 5 10 5" fill="none" stroke="#202124" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>',
        '<path d="M20 41q12 15 24 0z" fill="#fff" stroke="#202124" stroke-width="2"/>',
        "",
    ),
    "hushed_face": (
        '<circle cx="23" cy="25" r="4" fill="#202124"/><circle cx="41" cy="25" r="4" fill="#202124"/>',
        '<ellipse cx="32" cy="47" rx="6" ry="7" fill="#263238"/>',
        "",
    ),
    "nerd_face": (
        '<circle cx="22" cy="25" r="7" fill="none" stroke="#263238" stroke-width="3"/><circle cx="42" cy="25" r="7" fill="none" stroke="#263238" stroke-width="3"/><path d="M29 25h6" stroke="#263238" stroke-width="3"/><circle cx="22" cy="25" r="2"/><circle cx="42" cy="25" r="2"/>',
        '<path d="M23 43q9 8 18 0" fill="#fff" stroke="#202124" stroke-width="2"/><path d="M28 44v5m8-5v5" stroke="#202124" stroke-width="1"/>',
        "",
    ),
    "neutral_face": (OPEN_EYES, '<path d="M24 47h16" stroke="#202124" stroke-width="2.5" stroke-linecap="round"/>', ""),
    "pouting_face": (
        '<circle cx="23" cy="26" r="3"/><circle cx="41" cy="26" r="3"/><path d="m17 19 11 3m8 0 11-3" stroke="#202124" stroke-width="2.5" stroke-linecap="round"/>',
        '<path d="M24 49q8-7 16 0" fill="none" stroke="#202124" stroke-width="2.5" stroke-linecap="round"/>',
        "",
    ),
    "smiling_face_with_heart_eyes": (
        '<path d="M23 29c-10-7-12-1 0 7 12-8 10-14 0-7zm18 0c-10-7-12-1 0 7 12-8 10-14 0-7z" fill="#ef476f"/>',
        SMILE,
        "",
    ),
    "smiling_face_with_hearts": (
        '<path d="M17 26q6-7 12 0m6 0q6-7 12 0" fill="none" stroke="#202124" stroke-width="2.5" stroke-linecap="round"/>',
        SMILE,
        '<path d="M10 12c-6-5-10 2 1 10 11-8 7-15-1-10zm44 2c-6-5-10 2 1 10 11-8 7-15-1-10z" fill="#ff6f91" stroke="#8f2946"/>',
    ),
    "smiling_face_with_sunglasses": (
        '<path d="M13 20h17v5q-1 8-8 8t-8-8zm21 0h17l-1 5q-1 8-8 8t-8-8zM30 23h4" fill="#263238" stroke="#050505" stroke-width="2" stroke-linejoin="round"/>',
        SMILE,
        "",
    ),
}


def badge(symbol: str, color: str, extra: str = "") -> str:
    return HEADER + f"""<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <path d="M8 58 21 36h22l13 22-14-5-10 7-10-7z" fill="#e53935" stroke="#7f1715" stroke-width="2"/>
  <circle cx="32" cy="28" r="23" fill="#202124"/><ellipse cx="25" cy="26" rx="11" ry="14" fill="#f5f5dc"/><ellipse cx="39" cy="26" rx="11" ry="14" fill="#f5f5dc"/>
  <circle cx="24" cy="23" r="2.5"/><circle cx="40" cy="23" r="2.5"/><path d="m25 31 7-5 7 5-7 7z" fill="#ff9800" stroke="#8a4b08"/>
  <circle cx="48" cy="46" r="14" fill="{color}" stroke="#202124" stroke-width="2"/>
  {symbol}{extra}
</svg>
"""


BADGES = {
    "check_mark": ('<path d="m39 46 6 6 11-13" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>', "#43a047", ""),
    "cross_mark": ('<path d="m42 40 12 12m0-12L42 52" stroke="#fff" stroke-width="4" stroke-linecap="round"/>', "#e53935", ""),
    "cursor": ('<path d="m42 35 13 12-6 1 3 7-4 2-3-7-5 4z" fill="#fff" stroke="#202124" stroke-width="1.5"/>', "#42a5f5", ""),
    "tutorial_attention": ('<path d="M48 38v11m0 5v1" stroke="#fff" stroke-width="4" stroke-linecap="round"/>', "#ef5350", ""),
    "tutorial_information": ('<path d="M48 44v11m0-16v1" stroke="#fff" stroke-width="4" stroke-linecap="round"/>', "#42a5f5", ""),
    "tutorial_tip": ('<path d="M44 47q-5-8 4-10 9 2 4 10l-2 3h-4zm1 6h6" fill="#ffd54f" stroke="#5d4900" stroke-width="1.5"/>', "#fff3c4", ""),
    "tutorial_question": ('<path d="M43 42q1-5 6-5t5 4q0 4-5 5v3m0 5v1" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round"/>', "#ab47bc", ""),
    "tutorial_next_step": ('<path d="M40 46h12m-5-6 6 6-6 6" fill="none" stroke="#fff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>', "#26c6da", ""),
    "tutorial_mouse_click": ('<rect x="43" y="36" width="10" height="20" rx="5" fill="#fff" stroke="#202124"/><path d="M48 36v8h5" stroke="#ff7043" stroke-width="2"/>', "#eceff1", ""),
    "tutorial_keyboard": ('<rect x="38" y="40" width="20" height="14" rx="2" fill="#546e7a"/><path d="M41 44h3m2 0h3m2 0h3m-12 4h12" stroke="#fff" stroke-width="2"/>', "#eceff1", ""),
    "tutorial_terminal": ('<rect x="38" y="39" width="21" height="16" rx="2" fill="#263238"/><path d="m42 44 3 3-3 3m6 0h6" fill="none" stroke="#80cbc4" stroke-width="2"/>', "#78909c", ""),
}


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, (eyes, mouth, extras) in FACES.items():
        (OUTPUT / f"{name}.svg").write_text(face(eyes, mouth, extras), encoding="utf-8")
    for name, (symbol, color, extra) in BADGES.items():
        (OUTPUT / f"{name}.svg").write_text(badge(symbol, color, extra), encoding="utf-8")
    print(f"Generated {len(FACES) + len(BADGES)} SuperTux stickers in {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
