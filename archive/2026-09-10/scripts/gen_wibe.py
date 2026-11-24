#!/usr/bin/env python3
"""Render the Wibe featured-project panel (assets/wibe.svg) for README.md.

Sibling of gen_panels.py: the same ROBCO TERMLINK window chrome, with the
Wibe product icon (wibe repo docs/reference_shape_vscode.svg) rasterized to
a 32x32 phosphor pixel grid in the same four inks as the Portal logo.

The grid below was produced by scripts/raster_wibe.py (8x8 supersampling,
perceptual-luminance snapping); regenerate that way whenever the master
artwork changes. 5x7 pixel letters: same font as gen_panels, plus the
missing W/I/B/E glyphs.

Run:  python scripts/gen_wibe.py
"""
import os

from _retro_theme import CONTENT_Y, window

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
W = 900
PAD = 26
X = PAD + 4
LH = 20
H_PAD = 42          # room for the Fallout status bar below the last line

CURSOR = ('<tspan class="fg">\u2588<animate attributeName="opacity" values="1;1;0;0" '
          'dur="1.1s" repeatCount="indefinite"/></tspan>')


def prompt(y, cmd, caret=False):
    """A ROBCO TERMLINK prompt line (same as gen_panels)."""
    return (f'    <text x="{X}" y="{y}" class="m">'
            f'<tspan class="gr b">&gt;</tspan><tspan class="cy b">&#160;&#160;~/dev</tspan>'
            f'<tspan class="dim">&#160;git:(</tspan><tspan class="rd">main</tspan>'
            f'<tspan class="dim">)&#160;</tspan><tspan class="fg">{cmd}</tspan>'
            f'{CURSOR if caret else ""}</text>')


# ---------------------------------------------------------------- pixels
# 32x32 phosphor rasterization of the Wibe icon master artwork
# (github.com/s3hq4y/wibe docs/reference_shape_vscode.svg): the pale left
# face -> 'w', the deeper right face -> 'b', antialiased and shaded edges
# fall to 'c'/'d'. Cell chars: . = empty, w = pale #d9ffd9, b = #2e8b2e,
# c = #0f5c14, d = #17491b.
WIBE_PIXEL = [
    ".................cbbwbbbcd......",
    ".............cbbwwwwwbbbbbbbcd..",
    ".........cbbwwwwwwwbbbbbbbbbbbbb",
    ".....dbbwwwwwwwbbbd..bbbbbbbbbbb",
    ".dbbwwwwwwwbbcd......bbbbbbbbbbb",
    "bbbwwwwbbc...........bbbbbbbbbbb",
    "bbbbbbc..............bbbbbbbbbbb",
    "wwwbbbb..............bbbbbbbbbbb",
    "wwwwwwb..............bbbbbbbbbbb",
    "wwwwwwb..............bbbbbbbbbbb",
    "wwwwwwb..............bbbbbbbbbbb",
    "wwwwwwb..............bbbbbbbbbbb",
    "wwwwwwb..............bbbbbbbbbbb",
    "wwwwwwb..............bbbbbbbbbbb",
    "wwwwwwb..............bbbbbbbbbbb",
    "wwwwwwb..............bbbbbbbbbbb",
    "wwwwwwb..............bbbbbbbbbbb",
    "bwwwwwb..............bbbbbbbbbbb",
    "bwwwwwb..............bbbbbbbbbbb",
    "bwwwwwb..............bbbbbbbbbbb",
    "bwwwwwb..............bbbbbbbbbbb",
    "bwwwwwb..............bbbbbbbbbbb",
    "bwwwwwb..............bbbbbbbbbbb",
    "bwwwwwb..............bbbbbbbbbbb",
    "bwwwwwb..............bbbbbbbbbbb",
    "bwwwwwb..............cbbbbbbbbbb",
    "bwwwwwb..............cbbbbbbbbbb",
    "cbbwwwb..............cbbbbbbbbbb",
    "...dcbc..............cbbbbbbbbbb",
    ".....................cbbbbbbbbbb",
    ".....................cbbbbbbbcd.",
    ".....................cbbcd......",
]

PIXEL_INKS = {"b": "#2e8b2e", "d": "#17491b", "c": "#0f5c14", "w": "#d9ffd9"}

# 5x7 pixel bitmap font — WIBE glyphs (rest of the alphabet lives in
# gen_panels.py for the PORTAL wordmark).
WIBE_FONT = {
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
}

# Phosphor ramp accents, cycled per letter (same as the PORTAL wordmark).
PIXEL_LETTER_COLORS = ["bl", "cy", "gr", "ye", "ma", "rd"]


def pixel_grid(x, y, grid, cell, inks=PIXEL_INKS):
    """Emit a pixel-art grid as horizontally run-lengthed crisp rects."""
    frags = []
    for r, row in enumerate(grid):
        run = None
        for c, ch in enumerate(row + "."):
            if run and ch != run[0]:
                frags.append(f'<rect x="{x + run[1] * cell}" y="{y + r * cell}" '
                             f'width="{(c - run[1]) * cell}" height="{cell}" '
                             f'fill="{inks[run[0]]}"/>')
                run = None
            if ch in inks and not run:
                run = (ch, c)
    return frags


def pixel_text(x, y, text, cell):
    """Emit `text` in the 5x7 pixel font, one accent color per letter."""
    frags = []
    for i, ch in enumerate(text):
        color = PIXEL_LETTER_COLORS[i % len(PIXEL_LETTER_COLORS)]
        for r, row in enumerate(WIBE_FONT[ch]):
            for c, bit in enumerate(row):
                if bit == "1":
                    frags.append(f'<rect x="{x + (6 * i + c) * cell}" y="{y + r * cell}" '
                                 f'width="{cell}" height="{cell}" class="{color}"/>')
    return frags


def wibe():
    L = []
    y = CONTENT_Y
    L.append((y, prompt(y, "wibe --logo")))
    y += LH + 8

    LOGO_CELL, LETTER_CELL = 5, 8
    logo_x, logo_y = 212, y
    tx0 = logo_x + 32 * LOGO_CELL + 36
    ty0 = logo_y + (32 * LOGO_CELL - 7 * LETTER_CELL) // 2
    rects = pixel_grid(logo_x, logo_y, WIBE_PIXEL, LOGO_CELL)
    rects += pixel_text(tx0, ty0, "WIBE", LETTER_CELL)
    L.append((y, '    <g shape-rendering="crispEdges">' + "".join(rects) + "</g>"))
    ty_tag = ty0 + 7 * LETTER_CELL + 20
    L.append((ty_tag, f'    <text x="{tx0}" y="{ty_tag}" class="m">'
                      f'<tspan class="fg">vibe coding</tspan>'
                      f'<tspan class="dim">&#160;@&#160;</tspan>'
                      f'<tspan class="cy">your AI websites</tspan></text>'))
    y += 32 * LOGO_CELL + 14

    L.append((y, prompt(y, "", caret=True)))
    return window(
        W, y + H_PAD, "S9Y@EARTH \u2014 FEATURED: WIBE",
        [f for _, f in L], uid="w",
        tag="ROBCO INDUSTRIES",
        foot_left="WIBE TERMLINK \u00b7 UPLINK SECURE",
        foot_right="SIG 640K OK",
        label="featured project \u2014 wibe: vibe coding with a custom agent "
              "ext. and a local browser-backed agent")


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    p = os.path.join(ROOT, "assets", "wibe.svg")
    with open(p, "w", encoding="utf-8") as f:
        f.write(wibe())
    print("wrote assets/wibe.svg")
