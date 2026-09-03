#!/usr/bin/env python3
"""Render the badge-style skills panel (assets/skills.svg)."""
import os

from _retro_theme import (ADV, CONTENT_Y, HEAT, LINE, LINE_DIM, SCREEN, TEXT,
                          esc, window)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FS = 13
ADV_PX = FS * ADV          # Fixedsys Core: exactly 0.6 em per glyph
PADX = 11
CHIP_H, CHIP_GAP, ROW_GAP, LH = 24, 7, 9, 19
W, PAD = 900, 26
X = PAD + 4
LABEL_W = 118

CURSOR = ('<tspan class="fg">\u2588<animate attributeName="opacity" values="1;1;0;0" '
          'dur="1.1s" repeatCount="indefinite"/></tspan>')

GROUPS = [
 ("languages", "#7dff7d", ["TypeScript", "JavaScript", "Python", "Java", "C++", "C#", "Go", "PHP", "SQL"]),
 ("frontend",  "#66ff66", ["React", "Next.js", "Vue", "Nuxt", "Angular", "Redux",
                           "React Native", "Tailwind", "SCSS", "Material-UI",
                           "Framer Motion", "GSAP", "PWA"]),
 ("graphics",  "#b9ffb9", ["Three.js", "React Three Fiber", "Babylon.js", "PlayCanvas",
                           "PixiJS", "Spine", "WebGL"]),
 ("backend",   "#ccff99", ["Node.js", "Express", "NestJS", "Laravel", "CodeIgniter",
                           "GraphQL", "Apollo", "REST"]),
 ("data",      "#6bff6b", ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Firebase", "Prisma"]),
 ("infra",     "#5fff5f", ["Docker", "AWS", "Nginx", "Caddy", "Git", "NX", "Jest"]),
]


def prompt(y, cmd, caret=False):
    return (f'    <text x="{X}" y="{y}" class="m">'
            f'<tspan class="gr b">&gt;</tspan><tspan class="cy b">&#160;&#160;~/dev</tspan>'
            f'<tspan class="dim">&#160;git:(</tspan><tspan class="rd">main</tspan>'
            f'<tspan class="dim">)&#160;</tspan><tspan class="fg">{esc(cmd)}</tspan>'
            f'{CURSOR if caret else ""}</text>')


def build():
    chip_x0, chip_maxx = X + LABEL_W, W - PAD - 4
    out = [prompt(CONTENT_Y, "skills --list --group")]
    y = CONTENT_Y + LH + 12

    for name, color, items in GROUPS:
        row_y, cx = y, chip_x0
        for it in items:
            w = len(it) * ADV_PX + 2 * PADX
            if cx + w > chip_maxx:
                cx, row_y = chip_x0, row_y + CHIP_H + ROW_GAP
            out.append(
                f'    <g><rect x="{cx:.1f}" y="{row_y}" width="{w:.1f}" height="{CHIP_H}" '
                f'rx="3" fill="{color}" fill-opacity=".13" stroke="{color}" '
                f'stroke-opacity=".55"/>'
                f'<text x="{cx + w/2:.1f}" y="{row_y + 16}" text-anchor="middle" '
                f'class="m c" fill="{color}">{esc(it)}</text></g>')
            cx += w + CHIP_GAP
        mid = y + ((row_y - y) + CHIP_H) / 2 + 4
        out.append(f'    <text x="{X}" y="{mid:.0f}" class="m b" fill="{color}">'
                   f'{esc(name)}<tspan class="dim">/</tspan></text>')
        y = row_y + CHIP_H + 16

    y += 14
    out.append(prompt(y, "", caret=True))

    return window(
        W, y + 40, "S9Y@EARTH \u2014 SKILLS DATABASE",
        out, uid="k",
        tag="VAULT-TEC",
        foot_left="SKILLSDB.LST \u00b7 READ-ONLY",
        foot_right="SIG 640K OK",
        label="Technical skills")


if __name__ == "__main__":
    p = os.path.join(ROOT, "assets", "skills.svg")
    with open(p, "w", encoding="utf-8") as f:
        f.write(build())
    print("wrote assets/skills.svg")
