#!/usr/bin/env python3
"""Render the static TUI panels used by README.md (about + featured portal + footer).

These have no external data source, so they are generated once and committed.
Run:  python scripts/gen_panels.py
"""
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
W, PAD = 900, 26
X = PAD + 4
LH = 20
MONO = "'JetBrains Mono','Cascadia Code',Consolas,'DejaVu Sans Mono',monospace"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def shell(title, body_lines, height_pad=24):
    """body_lines: list of (y, svg_fragment)."""
    H = body_lines[-1][0] + height_pad
    head = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(title)}">
  <defs>
    <clipPath id="sc"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="10"/></clipPath>
    <style>
      .m {{ font-family:{MONO}; font-size:14px }}
      .sm {{ font-family:{MONO}; font-size:12px }}
      .dim{{ fill:#565f89 }} .fg {{ fill:#c0caf5 }} .cy {{ fill:#7dcfff }}
      .gr {{ fill:#9ece6a }} .ye {{ fill:#e0af68 }} .ma {{ fill:#bb9af7 }}
      .rd {{ fill:#f7768e }} .bl {{ fill:#7aa2f7 }} .b {{ font-weight:700 }}
    </style>
  </defs>
  <rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10.5" fill="#1a1b26" stroke="#2f3348"/>
  <g clip-path="url(#sc)">
    <rect x="1" y="1" width="{W-2}" height="30" fill="#16161e"/>
    <circle cx="22" cy="16" r="5.5" fill="#f7768e"/>
    <circle cx="40" cy="16" r="5.5" fill="#e0af68"/>
    <circle cx="58" cy="16" r="5.5" fill="#9ece6a"/>
    <text x="{W/2}" y="21" class="m dim" text-anchor="middle">{esc(title)}</text>
'''
    return head + "\n".join(f for _, f in body_lines) + "\n  </g>\n</svg>\n"


CURSOR = ('<tspan class="fg">\u2588<animate attributeName="opacity" values="1;1;0;0" '
          'dur="1.1s" repeatCount="indefinite"/></tspan>')


def prompt(y, cmd, caret=False):
    """A shell prompt line. The caret is a tspan inside the same text run, so it
    always sits exactly one cell after the last glyph regardless of the font."""
    return (f'    <text x="{X}" y="{y}" class="m">'
            f'<tspan class="gr b">\u279c</tspan><tspan class="cy b">  ~/dev</tspan>'
            f'<tspan class="dim"> git:(</tspan><tspan class="rd">main</tspan>'
            f'<tspan class="dim">) </tspan><tspan class="fg">{esc(cmd)}</tspan>'
            f'{CURSOR if caret else ""}</text>')


# ---------------------------------------------------------------- about
def about():
    L = []
    y = 78
    L.append((y, prompt(y, "cat ./about.txt")))
    y += LH + 8

    KEY_X, VAL_X = X + 26, X + 170
    rows = [
        ("name",      "ma", "s9y", None),
        ("location",  "ma", "Earth", "planet 3, sol system"),
        ("building",  "ma", "grand-strategy engines", "3D globes \u00b7 AI tooling"),
        ("currently", "ma", "building WHAT I LOVE", None),
        ("exploring", "ma", "AI for smarter user experiences", None),
        ("motto",     "ma", "ship it, then make it elegant", None),
    ]
    for i, (k, kc, v, note) in enumerate(rows):
        tee = "\u2514\u2500" if i == len(rows) - 1 else "\u251c\u2500"
        L.append((y, f'    <text x="{X}" y="{y}" class="m dim">{tee}</text>'))
        L.append((y, f'    <text x="{KEY_X}" y="{y}" class="m b {kc}">{esc(k)}</text>'))
        frag = f'<tspan class="fg">{esc(v)}</tspan>'
        if note:
            frag += f'<tspan class="dim">  \u00b7 {esc(note)}</tspan>'
        L.append((y, f'    <text x="{VAL_X}" y="{y}" class="m">{frag}</text>'))
        y += LH

    y += 10
    L.append((y, prompt(y, "uptime")))
    y += LH + 6
    L.append((y, f'    <text x="{X+26}" y="{y}" class="m">'
                 f'<tspan class="ye">shipping since 2025</tspan>'
                 f'<tspan class="dim">  \u00b7  load average: </tspan>'
                 f'<tspan class="gr">0.42, 1.15, 2.03</tspan></text>'))
    y += LH + 12

    L.append((y, prompt(y, "", caret=True)))
    return shell("s9y@earth: ~/dev \u2014 cat about.txt", L)


# ---------------------------------------------------------------- pixels
# 32x32 pixelization of the Portal icon (resources/icon.svg in the portal
# repo), rasterized from the source SVG and snapped to its four inks.
# Cell chars: . = panel background, b = #0078D4, d = #005A9E, c = #50E6FF,
# w = #ffffff.
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

PIXEL_INKS = {"b": "#0078D4", "d": "#005A9E", "c": "#50E6FF", "w": "#ffffff"}

# 5x7 pixel bitmap font, enough for the wordmark.
PIXEL_FONT = {
    "P": ["01110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
}

# Tokyo Night accents, cycled per letter.
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
    y = 78
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
    L.append((ty_tag, f'    <text x="{tx0}" y="{ty_tag}" class="sm">'
                      f'<tspan class="fg">workspace</tspan>'
                      f'<tspan class="dim"> \u2192 </tspan>'
                      f'<tspan class="cy">public MCP endpoint</tspan></text>'))
    y += 32 * LOGO_CELL + 14

    L.append((y, prompt(y, "", caret=True)))
    return shell("s9y@earth: ~/dev \u2014 featured: portal", L)

# --------------------------------------------------------------- footer
def footer():
    L = []
    y = 78
    L.append((y, prompt(y, "git push origin main")))
    y += LH + 6
    for frag in [
        '<tspan class="dim">Enumerating objects: </tspan><tspan class="fg">47</tspan>'
        '<tspan class="dim">, done.</tspan>',
        '<tspan class="dim">Writing objects: </tspan><tspan class="gr">100%</tspan>'
        '<tspan class="dim"> (47/47), 12.80 KiB, done.</tspan>',
        '<tspan class="dim">To </tspan><tspan class="cy">github.com:s3hq4y/s3hq4y.git</tspan>',
        '<tspan class="gr">   \u2713 main -> main</tspan>'
        '<tspan class="dim">   Everything up-to-date.</tspan>',
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
    return shell("s9y@earth: ~/dev \u2014 zsh", L)


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    for name, svg in (("portal.svg", portal()), ("footer.svg", footer())):
        p = os.path.join(ROOT, "assets", name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote assets/" + name)
