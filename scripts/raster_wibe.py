#!/usr/bin/env python3
"""Rasterize the Wibe product icon (docs/reference_shape_vscode.svg in the
wibe repo) into the 32x32 phosphor pixel grid used by gen_wibe.py.

The source SVG is simple enough to rasterize analytically: two gradient
quads (left face / right face), one soft shade quad clipped inside the
left face, and a couple of thin highlight strokes that vanish below the
32x32 Nyquist limit. We polygonize the paths, supersample 8x8 per cell,
composite, then snap each cell to the phosphor inks:

  '.' = empty            'b' = mid green body (#2e8b2e)
  'd' = dark green edge  'c' = deeper green fill  (#0f5c14)
  'w' = pale highlight   'd' = shade              (#17491b)

Usage:
  python scripts/raster_wibe.py [path-to-reference_shape_vscode.svg]
If no path is given, the master artwork is fetched from GitHub.
"""
import re
import sys
import urllib.request

import numpy as np
from matplotlib.path import Path

INK_BY_NAME = {"b": "#2e8b2e", "d": "#17491b", "c": "#0f5c14", "w": "#d9ffd9"}

SRC_URL = ("https://raw.githubusercontent.com/s3hq4y/wibe/master/"
           "docs/reference_shape_vscode.svg")

# inks of the source artwork
L_TOP, L_BOT = (0x12, 0xFF, 0x86), (0x00, 0xF0, 0x6E)   # left face gradient
R_TOP, R_BOT = (0x06, 0xB8, 0x5D), (0x00, 0xA3, 0x4D)   # right face gradient
SHADE = (0x00, 0x22, 0x0C)                               # spandrel shade

SS = 8              # supersamples per side per cell
N = 32              # grid cells


def load_svg(path=None):
    if path:
        with open(path, "rb") as f:
            return f.read().decode("utf-8")
    with urllib.request.urlopen(SRC_URL, timeout=30) as r:
        return r.read().decode("utf-8")


def parse_d(d):
    """Tokenize an SVG path d attribute into [(cmd, args...)] tuples."""
    toks = re.findall(r"[MLQZmlqz]|-?\d+\.?\d*(?:[eE][+-]?\d+)?", d)
    out, i = [], 0
    while i < len(toks):
        cmd = toks[i]
        n = {"M": 2, "L": 2, "Q": 4, "Z": 0}.get(cmd.upper())
        if cmd == "Z" or cmd == "z":
            out.append(("Z",)); i += 1; continue
        args = []
        for k in range(n):
            i += 1
            args.append(float(toks[i]))
        out.append((cmd, args)); i += 1
    return out


def flatten(d, seg=24):
    """Polygonize a d attribute: quadratics are sampled into polylines."""
    ops = parse_d(d)
    pts, cur, start = [], (0.0, 0.0), None
    for op in ops:
        if len(op) == 1:          # Z
            pts.append(start)
            continue
        cmd, a = op
        c = cmd.upper()
        if c == "M":
            cur = (a[0], a[1]); start = cur; pts.append(cur)
        elif c == "L":
            cur = (a[0], a[1]); pts.append(cur)
        elif c == "Q":
            p0, pc, p1 = cur, (a[0], a[1]), (a[2], a[3])
            for t in np.linspace(0, 1, seg + 1)[1:]:
                x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * pc[0] + t * t * p1[0]
                y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * pc[1] + t * t * p1[1]
                pts.append((x, y))
            cur = p1
        else:
            pts.append(start)
    return np.array(pts)


def paths_from_svg(svg):
    ds = re.findall(r'<path\s+d="([^"]*)"[^>]*fill="url\(#([a-zA-Z]+)\)"', svg)
    by = {name: d for d, name in ds}
    # left panel (lightest gradient), right panel, spandrel shade quad
    return by["leftPanel"], by["rightPanel"], by["springShade"]


def bbox_linear_gradient(poly, c0, c1):
    """t along the object bounding-box diagonal for x1=0,y1=0,x2=1,y2=1."""
    (x0, y0), (x1, y1) = poly.min(0), poly.max(0)
    vx, vy = x1 - x0, y1 - y0
    return (x0, y0), (vx, vy), vx * vx + vy * vy, c0, c1


def lerp_color(c0, c1, t):
    return tuple(round(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    svg = load_svg(path)
    l_panel, r_panel, shade_q = paths_from_svg(svg)
    l_poly, r_poly = flatten(l_panel), flatten(r_panel)
    sh_poly = flatten(shade_q)
    P_L, P_R, P_S = Path(l_poly), Path(r_poly), Path(sh_poly)

    # shade quad gradient is userSpaceOnUse: x1=258.68 233.85 -> x2=242.69 323.78
    m = re.search(r'<linearGradient[^>]*id="springShade"[^>]*>', svg)
    x1, y1, x2, y2 = (float(v) for v in re.findall(r'x1="([\d.]+)"[^>]*y1="([\d.]+)"[^>]*x2="([\d.]+)"[^>]*y2="([\d.]+)"', m.group(0))[0])
    svx, svy = x2 - x1, y2 - y1
    s_len2 = svx * svx + svy * svy

    bl0, blv, bl2, c0, c1 = bbox_linear_gradient(l_poly, L_TOP, L_BOT)
    br0, brv, br2, c2, c3 = bbox_linear_gradient(r_poly, R_TOP, R_BOT)

    X0 = min(l_poly[:, 0].min(), r_poly[:, 0].min())
    X1 = max(l_poly[:, 0].max(), r_poly[:, 0].max())
    Y0 = min(l_poly[:, 1].min(), r_poly[:, 1].min())
    Y1 = max(l_poly[:, 1].max(), r_poly[:, 1].max())

    out = []
    bl0 = np.array(bl0); br0 = np.array(br0)
    for cy in range(N):
        row = ""
        for cx in range(N):
            acc = np.zeros(3)
            for sy in range(SS):
                yy = Y0 + (cy + (sy + .5) / SS) / N * (Y1 - Y0)
                for sx in range(SS):
                    xx = X0 + (cx + (sx + .5) / SS) / N * (X1 - X0)
                    col = None
                    if P_L.contains_point((xx, yy)):
                        t = (np.dot((xx, yy) - bl0, blv) / bl2)
                        col = lerp_color(c0, c1, min(max(t, 0), 1))
                        if P_S.contains_point((xx, yy)):
                            ts = max(0., min(1., ((xx - x1) * svx + (yy - y1) * svy) / s_len2))
                            op = 0.46 * (1 - ts)   # 0.46 -> 0 along the shade
                            col = lerp_color(col, SHADE, op)
                    elif P_R.contains_point((xx, yy)):
                        t = (np.dot((xx, yy) - br0, brv) / br2)
                        col = lerp_color(c2, c3, min(max(t, 0), 1))
                    if col is not None:
                        acc += col
            if acc.sum() == 0:
                row += "."
                continue
            a, g, b_ = acc / (SS * SS)
            y = (.2126 * a + .7152 * g + .0722 * b_) / 255
            if y >= .62: row += "w"
            elif y >= .20: row += "b"
            elif y >= .10: row += "c"
            else: row += "d"
        out.append(row)

    # normalize: center the artwork on the 32x32 canvas
    rows_nz = [i for i, r in enumerate(out) if r.strip(".")]
    cols_nz = [j for r in out for j, ch in enumerate(r) if ch != "."]
    r0, r1 = min(rows_nz), max(rows_nz)
    c0i, c1i = min(cols_nz), max(cols_nz)
    body = [r[c0i:c1i + 1] for r in out[r0:r1 + 1]]
    H, Wd = len(body), len(body[0])
    pad_l = (N - Wd) // 2 if Wd < N else 0
    pad_t = (N - H) // 2 if H < N else 0
    grid = ["." * N for _ in range(pad_t)]
    for r in body:
        grid.append("." * pad_l + r + "." * (N - pad_l - len(r)))
    grid += ["." * N] * (N - len(grid))
    grid = grid[:N]

    print("\n".join(grid))
    print("\n// content rows %d..%d, cols %d..%d (cell %.0fx%.0f px)"
          % (r0, r1, c0i, c1i, (X1 - X0) / N, (Y1 - Y0) / N))


if __name__ == "__main__":
    main()
