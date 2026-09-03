#!/usr/bin/env python3
"""Render the static TUI panels used by README.md (featured portal + footer).

These have no external data source, so they are generated once and committed.
Run:  python scripts/gen_panels.py
"""
import os

from _retro_theme import (ADV, CONTENT_Y, GLOW_WHITE, HEAT, LINE, LINE_DIM,
                          SCREEN, TEXT, esc, window)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
W = 900
PAD = 26
X = PAD + 4
LH = 20
H_PAD = 42          # room for the Fallout status bar below the last line

CURSOR = ('<tspan class="fg">\u2588<animate attributeName="opacity" values="1;1;0;0" '
          'dur="1.1s" repeatCount="indefinite"/></tspan>')


def prompt(y, cmd, caret=False):
    """A ROBCO TERMLINK prompt line. The caret is a tspan inside the same
    text run, so it always sits exactly one cell after the last glyph."""
    return (f'    <text x="{X}" y="{y}" class="m">'
            f'<tspan class="gr b">&gt;</tspan><tspan class="cy b">&#160;&#160;~/dev</tspan>'
            f'<tspan class="dim">&#160;git:(</tspan><tspan class="rd">main</tspan>'
            f'<tspan class="dim">)&#160;</tspan><tspan class="fg">{esc(cmd)}</tspan>'
            f'{CURSOR if caret else ""}</text>')


# ---------------------------------------------------------------- pixels
# 32x32 pixelization of the Portal icon (resources/icon.svg in the portal
# repo), rasterized from the source SVG and snapped to its four inks,
# re-inked as a monochrome green phosphor logo.
# Cell chars: . = panel background, b = mid green body, d = dark green edge,
# c = bright green screen, w = pale highlight.
PORTAL_PIXEL = [
    "................................",
    "................................",
    "................................",
    "....cccccccccccccccccccccddd....",
    "...bbbbbbbbbbbbbbbbbbbbbbdddd...",
    "....bbbbbbbbbbbbbbbbbbbbbdddd...",
    "....bbbbbbbbbbbbbbbbbbbbbdddd...",
    "....bbbcccccccccccccccbbbdddd...",
    "....bbbcccccccccccccccbbbdddd...",
    "....bbbcccbbbbbbbbbbccbbbdddd...",
    "....bbbccbbbbbbbbbbbccbbbdddd...",
    "....bbbccbbbbbbbbbbbccbbbdddd...",
    "....bbbccbbbwwbbbwwbccbbbdddd...",
    "....bbbccbbbwwbbbwwbccbbbdddd...",
    "....bbbccbbbwwbbbwwbccbbbdddd...",
    "....bbbccbcwwwwwwwwwwcbbbdddd...",
    "....bbbccbcwwwwwwwwwwcbbbdddd...",
    "....bbbccbcwwwwwwwwwwcbbbdddd...",
    "....bbbccbcwwwwwwwwwwcbbbdddd...",
    "....bbbccbcwwwwwwwwwwcbbbdddd...",
    "....bbbccbbbbbwwwbbbccbbbdddd...",
    "....bbbccbbbbbwwwbbbccbbbdddd...",
    "....bbbccbbbbbwwwbbbccbbbdddd...",
    "....bbbccbbbbbwwwbbbccbbbdddd...",
    "....bbbccbbbbbbbbbbbccbbbdddd...",
    "....bbbbbbbbbbbbbbbbbbbbbdddd...",
    "....bbbbbbbbbbbbbbbbbbbbbdddd...",
    "....bbbbbbbbbbbbbbbbbbbbbdddd...",
    ".........................ddd....",
    "................................",
    "................................",
    "................................",
]

PIXEL_INKS = {"b": "#2e8b2e", "d": "#17491b", "c": "#0f5c14", "w": "#d9ffd9"}

# 5x7 pixel bitmap font, enough for the wordmark.
PIXEL_FONT = {
    "P": ["01110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
}

# Phosphor ramp accents, cycled per letter.
PIXEL_LETTER_COLORS = ["bl", "cy", "gr", "ye", "ma", "rd"]


def pixel_grid(x, y, grid, cell, inks=PIXEL_INKS):
    """Emit a pixel-art grid as horizontally run-lengthed crisp rects."""
    frags = []
    for r, row in enumerate(grid):
        run = None  # (char, start_col)
        for c, ch in enumerate(row + "."):  # sentinel flushes the last run
            if run and ch != run[0]:
                frags.append(f'<rect x="{x + run[1]*cell}" y="{y + r*cell}" '
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
        for r, row in enumerate(PIXEL_FONT[ch]):
            for c, bit in enumerate(row):
                if bit == "1":
                    frags.append(f'<rect x="{x + (6*i + c)*cell}" y="{y + r*cell}" '
                                 f'width="{cell}" height="{cell}" class="{color}"/>')
    return frags


# --------------------------------------------------------------- portal
def portal():
    L = []
    y = CONTENT_Y
    L.append((y, prompt(y, "portal --logo")))
    y += LH + 8

    LOGO_CELL, LETTER_CELL = 5, 8
    logo_x, logo_y = 212, y
    tx0 = logo_x + 32 * LOGO_CELL + 36
    ty0 = logo_y + (32 * LOGO_CELL - 7 * LETTER_CELL) // 2
    rects = pixel_grid(logo_x, logo_y, PORTAL_PIXEL, LOGO_CELL)
    rects += pixel_text(tx0, ty0, "PORTAL", LETTER_CELL)
    L.append((y, '    <g shape-rendering="crispEdges">' + "".join(rects) + "</g>"))
    ty_tag = ty0 + 7 * LETTER_CELL + 20
    L.append((ty_tag, f'    <text x="{tx0}" y="{ty_tag}" class="m">'
                      f'<tspan class="fg">workspace</tspan>'
                      f'<tspan class="dim">&#160;&gt;&#160;</tspan>'
                      f'<tspan class="cy">public MCP endpoint</tspan></text>'))
    y += 32 * LOGO_CELL + 14

    L.append((y, prompt(y, "", caret=True)))
    return window(
        W, y + H_PAD, "S9Y@EARTH \u2014 FEATURED: PORTAL",
        [f for _, f in L], uid="p",
        tag="ROBCO INDUSTRIES",
        foot_left="TERMLINK PROTOCOL \u00b7 UPLINK SECURE",
        foot_right="SIG 640K OK",
        label="featured project \u2014 portal: expose your VS Code workspace "
              "as a public MCP endpoint")


# --------------------------------------------------------------- footer
def footer():
    L = []
    y = CONTENT_Y
    L.append((y, prompt(y, "git push origin main")))
    y += LH + 6
    for frag in [
        '<tspan class="dim">Enumerating objects: </tspan><tspan class="fg">47</tspan>'
        '<tspan class="dim">&#160;, done.</tspan>',
        '<tspan class="dim">Writing objects: </tspan><tspan class="gr">100%</tspan>'
        '<tspan class="dim">&#160;(47/47),&#160;12.80&#160;KiB, done.</tspan>',
        '<tspan class="dim">To&#160;</tspan><tspan class="cy">github.com:s3hq4y/s3hq4y.git</tspan>',
        '<tspan class="gr">&#160;&#160;&#160;OK main&#160;-&gt;&#160;main</tspan>'
        '<tspan class="dim">&#160;&#160;&#160;Everything up-to-date.</tspan>',
    ]:
        L.append((y, f'    <text x="{X+26}" y="{y}" class="m">{frag}</text>'))
        y += LH
    y += 12

    L.append((y, prompt(y, "echo $MESSAGE")))
    y += LH + 6
    L.append((y, f'    <text x="{X+26}" y="{y}" class="m ye">'
                 f'Thanks for stopping by \u2014 let\u2019s build something impossible.</text>'))
    y += LH + 12

    L.append((y, prompt(y, "", caret=True)))
    return window(
        W, y + H_PAD, "S9Y@EARTH \u2014 ~/DEV \u2014 ZSH",
        [f for _, f in L], uid="f",
        tag="ROBCO INDUSTRIES",
        foot_left="TRANSFER COMPLETE \u00b7 0 ERR",
        foot_right="SIG 640K OK",
        label="git push origin main")


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    for name, svg in (("portal.svg", portal()), ("footer.svg", footer())):
        p = os.path.join(ROOT, "assets", name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote assets/" + name)
