#!/usr/bin/env python3
"""Generate original stickers that complete the Papirus, GNOME and Numix tabs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEMES = ROOT / "ksnip_py" / "stickers" / "themes"
HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<!-- Original ksnip_py artwork, GPL-3.0. Theme-compatible palette; no upstream artwork copied. -->
"""


@dataclass(frozen=True)
class Theme:
    name: str
    size: int
    face: str
    edge: str
    ink: str
    accent: str
    panel: str
    shadow: str
    defs: str = ""


THEME_DATA = (
    Theme("papirus", 48, "#ffd54f", "#ef9a28", "#424242", "#42a5f5", "#f5f5f5", "#000", ""),
    Theme(
        "gnome", 256, "url(#face)", "#c17d11", "#2e3436", "#729fcf", "#eeeeec", "#2e3436",
        '<defs><linearGradient id="face" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#fff08a"/><stop offset="1" stop-color="#f5b928"/></linearGradient></defs>',
    ),
    Theme("numix", 48, "#f6d267", "#d9a441", "#656565", "#2eb8ac", "#f3f3f3", "#4d4d4d", ""),
)


OPEN_EYES = '<circle cx="23" cy="26" r="3"/><circle cx="41" cy="26" r="3"/>'
SMILE = '<path d="M23 42q9 10 18 0" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>'

FACES = {
    "confused_face": (
        '<circle cx="23" cy="26" r="3"/><circle cx="41" cy="28" r="3"/><path d="m17 19 11-2m8 1 10 4" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>',
        '<path d="M24 46q8-5 16 1" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>', ""),
    "face_blowing_a_kiss": (
        '<path d="M17 27q6-7 12 0" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/><circle cx="41" cy="25" r="3"/>',
        '<path d="M27 44q5-5 10 0-5 5-10 0" fill="#ef5350" stroke="currentColor" stroke-width="1.5"/>',
        '<path d="M52 33c-6-6-12 2 0 11 12-9 6-17 0-11z" fill="#ec407a" stroke="currentColor" stroke-width="1.5"/>'),
    "face_savoring_food": (OPEN_EYES,
        '<path d="M22 42q10 10 20 0" fill="none" stroke="currentColor" stroke-width="3"/><path d="M34 45q9 0 6 7-7 4-11-3" fill="#ef5350" stroke="currentColor" stroke-width="1.5"/>', ""),
    "face_with_symbols_on_mouth": (
        '<path d="m17 21 11 7m-11 0 11-7m9 0 10 7m-10 0 10-7" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>',
        '<rect x="18" y="40" width="28" height="12" rx="3" fill="#546e7a"/><path d="m22 49 4-6m2 6 4-6m3 6 5-6" stroke="#fff" stroke-width="2"/>',
        '<text x="48" y="18" font-family="sans-serif" font-size="11" font-weight="bold" fill="#e53935">#</text>'),
    "grinning_face_with_big_eyes": (
        '<circle cx="23" cy="25" r="6" fill="#fff" stroke="currentColor" stroke-width="2"/><circle cx="41" cy="25" r="6" fill="#fff" stroke="currentColor" stroke-width="2"/><circle cx="23" cy="25" r="2"/><circle cx="41" cy="25" r="2"/>',
        '<path d="M20 40q12 17 24 0z" fill="#fff" stroke="currentColor" stroke-width="2"/>', ""),
    "grinning_face_with_smiling_eyes": (
        '<path d="M16 27q7-8 14 0m4 0q7-8 14 0" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>',
        '<path d="M20 40q12 17 24 0z" fill="#fff" stroke="currentColor" stroke-width="2"/>', ""),
    "grinning_face_with_sweat": (
        '<path d="M16 27q7-8 14 0m4 0q7-8 14 0" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>',
        '<path d="M20 40q12 16 24 0z" fill="#fff" stroke="currentColor" stroke-width="2"/>',
        '<path d="M52 8q-10 12 0 17 10-5 0-17z" fill="#42a5f5" stroke="currentColor" stroke-width="1.5"/>'),
    "grinning_squinting_face": (
        '<path d="m16 21 12 6-12 6m32-12-12 6 12 6" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>',
        '<path d="M19 40q13 18 26 0z" fill="#fff" stroke="currentColor" stroke-width="2"/>', ""),
    "hushed_face": ('<circle cx="23" cy="25" r="4"/><circle cx="41" cy="25" r="4"/>',
        '<ellipse cx="32" cy="46" rx="6" ry="8" fill="currentColor"/>', ""),
    "nerd_face": (
        '<circle cx="22" cy="25" r="8" fill="#fff" fill-opacity=".35" stroke="currentColor" stroke-width="3"/><circle cx="42" cy="25" r="8" fill="#fff" fill-opacity=".35" stroke="currentColor" stroke-width="3"/><path d="M30 25h4" stroke="currentColor" stroke-width="3"/><circle cx="22" cy="25" r="2"/><circle cx="42" cy="25" r="2"/>',
        '<path d="M22 42q10 11 20 0" fill="#fff" stroke="currentColor" stroke-width="2"/><path d="M28 44v6m8-6v6" stroke="currentColor"/>', ""),
    "neutral_face": (OPEN_EYES, '<path d="M23 47h18" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>', ""),
    "pouting_face": (
        '<circle cx="23" cy="27" r="3"/><circle cx="41" cy="27" r="3"/><path d="m16 19 12 4m8 0 12-4" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>',
        '<path d="M23 50q9-9 18 0" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>', ""),
    "smiling_face_with_heart_eyes": (
        '<path d="M23 26c-11-8-14 3 0 12 14-9 11-20 0-12zm18 0c-11-8-14 3 0 12 14-9 11-20 0-12z" fill="#e91e63"/>', SMILE, ""),
    "smiling_face_with_hearts": (
        '<path d="M16 27q7-8 14 0m4 0q7-8 14 0" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>', SMILE,
        '<path d="M10 10C3 4-2 13 10 22 22 13 17 4 10 10zm45 5c-6-5-11 3 0 11 11-8 6-16 0-11z" fill="#ec407a" stroke="currentColor"/>'),
    "smiling_face_with_sunglasses": (
        '<path d="M12 20h18v5q-1 9-9 9t-8-9zm22 0h18l-1 5q-1 9-9 9t-8-9zM30 23h4" fill="#343434" stroke="#111" stroke-width="2" stroke-linejoin="round"/>', SMILE, ""),
}


SYMBOLS = {
    "cursor": '<path d="m22 13 25 25-11 1 6 13-7 3-6-13-8 8z" fill="#fff" stroke="currentColor" stroke-width="2.5" stroke-linejoin="round"/>',
    "tutorial_attention": '<path d="M32 15v25m0 9v1" stroke="#fff" stroke-width="7" stroke-linecap="round"/>',
    "tutorial_information": '<circle cx="32" cy="20" r="4" fill="#fff"/><path d="M32 30v20" stroke="#fff" stroke-width="7" stroke-linecap="round"/>',
    "tutorial_question": '<path d="M22 24q1-10 11-10 10 0 10 8 0 8-10 11v6m0 10v1" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round"/>',
    "tutorial_next_step": '<path d="M15 32h32m-12-13 13 13-13 13" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>',
    "tutorial_tip": '<path d="M21 27q0-12 11-12t11 12q0 7-6 11l-2 7h-6l-2-7q-6-4-6-11z" fill="#fff59d" stroke="currentColor" stroke-width="2"/><path d="M28 50h8" stroke="#fff" stroke-width="4" stroke-linecap="round"/>',
    "tutorial_mouse_click": '<rect x="22" y="11" width="20" height="42" rx="10" fill="#fff" stroke="currentColor" stroke-width="3"/><path d="M32 12v15h10" fill="none" stroke="#ef5350" stroke-width="3"/>',
    "tutorial_terminal": '<rect x="11" y="15" width="42" height="34" rx="4" fill="#263238" stroke="#fff" stroke-width="2"/><path d="m18 26 7 6-7 6m12 0h14" fill="none" stroke="#80cbc4" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>',
    "tutorial_keyboard": '<rect x="8" y="17" width="48" height="31" rx="4" fill="#eceff1" stroke="currentColor" stroke-width="3"/><path d="M14 24h5m4 0h5m4 0h5m4 0h7M14 31h7m4 0h5m4 0h5m4 0h5M15 39h34" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>',
}

BADGE_COLORS = {
    "cursor": "#42a5f5", "tutorial_attention": "#ef5350", "tutorial_information": "#42a5f5",
    "tutorial_question": "#ab47bc", "tutorial_next_step": "#26a69a", "tutorial_tip": "#ffa726",
    "tutorial_mouse_click": "#78909c", "tutorial_terminal": "#546e7a", "tutorial_keyboard": "#607d8b",
}


def face_svg(theme: Theme, eyes: str, mouth: str, extras: str) -> str:
    return HEADER + f'''<svg xmlns="http://www.w3.org/2000/svg" width="{theme.size}" height="{theme.size}" viewBox="0 0 64 64">
  {theme.defs}<ellipse cx="32" cy="34" rx="27" ry="27" fill="{theme.shadow}" opacity=".2"/>
  <circle cx="32" cy="31" r="27" fill="{theme.face}" stroke="{theme.edge}" stroke-width="2.5"/>
  <path d="M14 18q18-17 36 0" fill="none" stroke="#fff" stroke-opacity=".28" stroke-width="3" stroke-linecap="round"/>
  <g color="{theme.ink}" fill="{theme.ink}">{eyes}{mouth}{extras}</g>
</svg>
'''


def symbol_svg(theme: Theme, name: str, symbol: str) -> str:
    color = BADGE_COLORS[name]
    if theme.name == "papirus":
        body = f'<rect x="7" y="7" width="50" height="50" rx="13" fill="{color}"/><path d="M14 14h36" stroke="#fff" stroke-opacity=".25" stroke-width="3" stroke-linecap="round"/>'
    elif theme.name == "gnome":
        body = f'<circle cx="32" cy="34" r="27" fill="#000" opacity=".25"/><circle cx="32" cy="31" r="27" fill="{color}" stroke="{theme.edge}" stroke-width="2.5"/><path d="M15 18q17-15 34 0" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="3"/>'
    else:
        body = f'<circle cx="32" cy="32" r="27" fill="{color}"/><circle cx="32" cy="32" r="22" fill="none" stroke="#fff" stroke-opacity=".22" stroke-width="2"/>'
    return HEADER + f'''<svg xmlns="http://www.w3.org/2000/svg" width="{theme.size}" height="{theme.size}" viewBox="0 0 64 64">
  {body}<g color="{theme.ink}">{symbol}</g>
</svg>
'''


def main() -> int:
    generated = 0
    for theme in THEME_DATA:
        output = THEMES / theme.name
        output.mkdir(parents=True, exist_ok=True)
        for name, (eyes, mouth, extras) in FACES.items():
            (output / f"{name}.svg").write_text(face_svg(theme, eyes, mouth, extras), encoding="utf-8")
            generated += 1
        for name, symbol in SYMBOLS.items():
            (output / f"{name}.svg").write_text(symbol_svg(theme, name, symbol), encoding="utf-8")
            generated += 1
    print(f"Generated {generated} original themed stickers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
