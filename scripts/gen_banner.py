#!/usr/bin/env python3
"""Render assets/banner.svg — the big ROBCO TERMLINK welcome screen."""
import os

from _retro_theme import (ADV, FONT_STACK, LINE, LINE_DIM, TEXT, CONTENT_Y,
                          esc, window)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
W = 900
X = 34
COL = 404

ASCII_MARK = [
    "██████╗ █████╗  ██╗    ██╗",
    "██╔═══╝ ██╔══██╗╚██╗  ██╔╝",
    "║█████╗ ║██████║  ╚████╔╝ ",
    "╚═══██║ ╚═══██╔╝    ╚██╔╝ ",
    "██████║ █████╔╝     ██║   ",
    "╚═════╝ ╚════╝      ╚═╝   ",
]

SYSINFO = [
    ("OS",    "Earth (x86_64)"),
    ("Uptime", "shipping since 2025"),
    ("Shell",  "TypeScript / Go / Python"),
    ("WM",     "Three.js · Babylon.js · PlayCanvas"),
    ("Focus",  "grand strategy · AI · realtime 3D"),
]

SWATCHES = [TEXT["rd"], TEXT["ye"], TEXT["gr"], TEXT["cy"],
            TEXT["bl"], TEXT["ma"], TEXT["fg"]]

CURSOR = ('<tspan class="fg">\u2588<animate attributeName="opacity" values="1;1;0;0" '
          'dur="1.1s" begin="1.9s" repeatCount="indefinite"/></tspan>')


def nbsp(s):
    return esc(s).replace(" ", "&#160;")


def mark_rows(fill):
    tsps = "".join(f'<tspan x="{X}" dy="{16 if i else 0}">{nbsp(row)}</tspan>'
                   for i, row in enumerate(ASCII_MARK))
    return f'<text x="34" y="60" font-family="{FONT_STACK}" font-size="14" ' \
           f'xml:space="preserve" fill="{fill}">{tsps}</text>'


def prompt(y, cmd, caret=False, begin=None):
    g_open = (f'<g opacity="1"><animate attributeName="opacity" from="0" to="1" '
              f'begin="{begin}" dur="0.01s" fill="freeze"/>' if begin else "<g>")
    caret_frag = CURSOR if caret else ""
    return (f'    {g_open}<text x="{X}" y="{y}" class="m">'
            f'<tspan class="gr b">&gt;</tspan><tspan class="cy b">  ~/dev</tspan>'
            f'<tspan class="dim">&#160;git:(</tspan><tspan class="rd">main</tspan>'
            f'<tspan class="dim">) </tspan><tspan class="fg">{esc(cmd)}</tspan>'
            f'{caret_frag}</text></g>')


DASH_ROW = "\u2500" * 31


def build():
    L = []

    # -- ASCII personal mark: dark drop shadow + phosphor copy, typed in
    L.append(f'''        <g font-family="{FONT_STACK}" font-size="14" xml:space="preserve">
          <animate attributeName="opacity" from="0" to="1" begin="0.3s" dur="0.3s" fill="freeze"/>
          <g transform="translate(2,2)">{mark_rows("#0d250d")}</g>
          {mark_rows(TEXT["cy"])}
        </g>''')
    L.append(f'        <text x="{X}" y="170" class="m dim">ship it \u00b7 then polish</text>')

    # -- neofetch-style sysinfo column
    L.append('    <g class="m">')
    L.append(f'      <text x="{COL}" y="72">'
             f'<tspan class="bl b">s9y</tspan><tspan class="dim">@</tspan>'
             f'<tspan class="bl b">earth</tspan></text>')
    L.append(f'      <text x="{COL}" y="90" class="dim">{DASH_ROW}</text>')
    for i, (k, v) in enumerate(SYSINFO):
        yy = 112 + i * 20
        pad = "&#160;" * (7 - len(k))
        L.append(f'      <text x="{COL}" y="{yy}"><tspan class="ma b">{k}</tspan>'
                 f'<tspan class="dim">{pad}\u00b7&#160;</tspan>'
                 f'<tspan class="fg">{esc(v)}</tspan></text>')
    sw = "".join(f'<rect x="{COL + i * 22}" y="204" width="20" height="10" '
                 f'fill="{c}"/>' for i, c in enumerate(SWATCHES))
    L.append(f'      <g>{sw}</g>')
    L.append('    </g>')

    L.append(f'    <line x1="30" y1="222" x2="870" y2="222" stroke="{LINE_DIM}"/>')

    # -- typed prompts
    L.append(prompt(248, "whoami --verbose", begin="0.4s"))
    L.append(f'    <g opacity="1"><animate attributeName="opacity" from="0" to="1" '
             f'begin="1.2s" dur="0.01s" fill="freeze"/>'
             f'<text x="{X}" y="270" class="m ye">'
             f'Coding like it\u2019s 2050, but debugging like it\u2019s 1999.</text></g>')
    L.append(prompt(298, "git push origin main", caret=True, begin="1.9s"))

    return window(
        W, 352, "S9Y@EARTH \u2014 ~/DEV \u2014 ZSH \u2014 96\u00d724",
        L, uid="b",
        tag="ROBCO INDUSTRIES",
        foot_left="ROBCO INDUSTRIES (TM) TERMLINK PROTOCOL",
        foot_right="EST. 2077",
        label="s9y@earth \u2014 coding like it's 2050, debugging like it's 1999")


if __name__ == "__main__":
    p = os.path.join(ROOT, "assets", "banner.svg")
    with open(p, "w", encoding="utf-8") as f:
        f.write(build())
    print("wrote assets/banner.svg")
