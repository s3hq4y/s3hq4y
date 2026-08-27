#!/usr/bin/env python3
"""Render the badge-style skills panel (assets/skills.svg)."""
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FS, ADV, PADX = 13, 7.82, 11
CHIP_H, CHIP_GAP, ROW_GAP, LH = 24, 7, 9, 19
W, PAD = 900, 26
X = PAD + 4
LABEL_W = 118
MONO = "'JetBrains Mono','Cascadia Code',Consolas,'DejaVu Sans Mono',monospace"

CURSOR = ('<tspan class="fg">\u2588<animate attributeName="opacity" values="1;1;0;0" '
          'dur="1.1s" repeatCount="indefinite"/></tspan>')

GROUPS = [
 ("languages", "#7dcfff", ["TypeScript", "JavaScript", "Python", "Go", "PHP", "SQL"]),
 ("frontend",  "#9ece6a", ["React", "Next.js", "Vue", "Nuxt", "Angular", "Redux",
                           "React Native", "Tailwind", "SCSS", "Material-UI",
                           "Framer Motion", "GSAP", "PWA"]),
 ("graphics",  "#bb9af7", ["Three.js", "React Three Fiber", "Babylon.js", "PlayCanvas",
                           "PixiJS", "Spine", "WebGL"]),
 ("backend",   "#e0af68", ["Node.js", "Express", "NestJS", "Laravel", "CodeIgniter",
                           "GraphQL", "Apollo", "REST"]),
 ("data",      "#f7768e", ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Firebase", "Prisma"]),
 ("infra",     "#7aa2f7", ["Docker", "AWS", "Nginx", "Caddy", "Git", "NX", "Jest"]),
]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def prompt(y, cmd, caret=False):
    return (f'    <text x="{X}" y="{y}" class="m">'
            f'<tspan class="gr b">\u279c</tspan><tspan class="cy b">  ~/dev</tspan>'
            f'<tspan class="dim"> git:(</tspan><tspan class="rd">main</tspan>'
            f'<tspan class="dim">) </tspan><tspan class="fg">{esc(cmd)}</tspan>'
            f'{CURSOR if caret else ""}</text>')


def build():
    chip_x0, chip_maxx = X + LABEL_W, W - PAD - 4
    out = [prompt(78, "skills --list --group")]
    y = 78 + LH + 12

    for name, color, items in GROUPS:
        row_y, cx = y, chip_x0
        for it in items:
            w = len(it) * ADV + 2 * PADX
            if cx + w > chip_maxx:
                cx, row_y = chip_x0, row_y + CHIP_H + ROW_GAP
            out.append(
                f'    <g><rect x="{cx:.1f}" y="{row_y}" width="{w:.1f}" height="{CHIP_H}" '
                f'rx="5" fill="{color}" fill-opacity=".13" stroke="{color}" '
                f'stroke-opacity=".55"/>'
                f'<text x="{cx + w/2:.1f}" y="{row_y + 16}" text-anchor="middle" class="c" '
                f'fill="{color}">{esc(it)}</text></g>')
            cx += w + CHIP_GAP
        mid = y + ((row_y - y) + CHIP_H) / 2 + 4
        out.append(f'    <text x="{X}" y="{mid:.0f}" class="m b" fill="{color}">'
                   f'{esc(name)}<tspan class="dim">/</tspan></text>')
        y = row_y + CHIP_H + 16

    y += 14
    out.append(prompt(y, "", caret=True))
    H = y + 26

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Technical skills">
  <defs>
    <clipPath id="sc"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="10"/></clipPath>
    <style>
      .m {{ font-family:{MONO}; font-size:14px }}
      .c {{ font-family:{MONO}; font-size:{FS}px }}
      .dim{{ fill:#565f89 }} .fg {{ fill:#c0caf5 }} .cy {{ fill:#7dcfff }}
      .gr {{ fill:#9ece6a }} .rd {{ fill:#f7768e }} .b {{ font-weight:700 }}
    </style>
  </defs>
  <rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10.5" fill="#1a1b26" stroke="#2f3348"/>
  <g clip-path="url(#sc)">
    <rect x="1" y="1" width="{W-2}" height="30" fill="#16161e"/>
    <circle cx="22" cy="16" r="5.5" fill="#f7768e"/>
    <circle cx="40" cy="16" r="5.5" fill="#e0af68"/>
    <circle cx="58" cy="16" r="5.5" fill="#9ece6a"/>
    <text x="{W/2}" y="21" class="m dim" text-anchor="middle">s9y@earth: ~/skills \u2014 skills --list</text>
{chr(10).join(out)}
  </g>
</svg>
'''


if __name__ == "__main__":
    p = os.path.join(ROOT, "assets", "skills.svg")
    with open(p, "w", encoding="utf-8") as f:
        f.write(build())
    print("wrote assets/skills.svg")
