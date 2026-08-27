#!/usr/bin/env python3
"""Generate a single self-contained GitHub overview card (SVG).

No third-party badge services: data comes straight from the GitHub GraphQL API
and every pixel is drawn here, so the card can never 503 or rate-limit.

Usage:  GITHUB_TOKEN=... python scripts/gen_stats.py [username]
Writes: assets/overview.svg
"""
import datetime
import json
import math
import os
import sys
import urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else "s3hq4y"
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

QUERY = """
query($login:String!){
  user(login:$login){
    createdAt
    followers{totalCount}
    repositories(first:100, ownerAffiliations:OWNER, isFork:false){
      totalCount
      nodes{ name stargazerCount
        languages(first:8, orderBy:{field:SIZE,direction:DESC}){
          edges{ size node{ name color } } } }
    }
    contributionsCollection{
      totalCommitContributions restrictedContributionsCount
      contributionCalendar{
        totalContributions
        weeks{ contributionDays{ date contributionCount } } }
    }
    pullRequests{totalCount}
    issues{totalCount}
  }
}"""

# ---------------------------------------------------------------- theme
BG      = "#1a1b27"
PANEL   = "#20222f"
BORDER  = "#2f3348"
TITLE   = "#70a5fd"
TEXT    = "#c9d1d9"
MUTED   = "#8b93b3"
ACCENT  = "#bf91f3"
FLAME   = "#f7768e"
HEAT    = ["#20222f", "#1f3b57", "#26608c", "#3f8fd0", "#70a5fd"]

W = 860
FONT = "'Segoe UI',Ubuntu,-apple-system,sans-serif"
MONO = "'JetBrains Mono',Consolas,monospace"


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}",
                 "Content-Type": "application/json",
                 "User-Agent": "readme-overview"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["data"]["user"]


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


ICONS = {
 "commit": "M11.93 8.5a4 4 0 01-7.86 0H.75a.75.75 0 010-1.5h3.32a4 4 0 017.86 0h3.32a.75.75 0 010 1.5zM8 10a2 2 0 100-4 2 2 0 000 4z",
 "star":   "M8 .25l2.06 4.18 4.61.67-3.34 3.25.79 4.59L8 10.78l-4.12 2.16.79-4.59L1.33 5.1l4.61-.67z",
 "repo":   "M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5zm10.5-1h-8a1 1 0 00-1 1v6.708A2.486 2.486 0 014.5 9h8z",
 "pr":     "M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z",
 "issue":  "M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM0 8a8 8 0 1116 0A8 8 0 010 8zm9 3a1 1 0 11-2 0 1 1 0 012 0zm-.25-6.25v3.5a.75.75 0 01-1.5 0v-3.5a.75.75 0 011.5 0z",
 "people": "M5.5 3.5a2 2 0 100 4 2 2 0 000-4zM2 5.5a3.5 3.5 0 115.898 2.549 5.507 5.507 0 013.034 4.084.75.75 0 11-1.482.235 4.001 4.001 0 00-7.9 0 .75.75 0 01-1.482-.236A5.507 5.507 0 013.102 8.05 3.49 3.49 0 012 5.5zM11 4a.75.75 0 100 1.5 1.75 1.75 0 11-.5 3.428.75.75 0 10-.5 1.414 3.25 3.25 0 101-6.342z",
}


# ------------------------------------------------------------- analysis
def flat_days(user):
    days = []
    for wk in user["contributionsCollection"]["contributionCalendar"]["weeks"]:
        for d in wk["contributionDays"]:
            days.append((datetime.date.fromisoformat(d["date"]), d["contributionCount"]))
    days.sort()
    return days


def streaks(days):
    """Return (current, cur_range, longest, long_range). Today with 0 does not
    break the current streak yet — the day is not over."""
    today = days[-1][0]
    best = cur = 0
    best_rng = cur_rng = (None, None)
    for date, n in days:
        if n > 0:
            cur = cur + 1 if cur else 1
            cur_rng = (date if cur == 1 else cur_rng[0], date)
            if cur > best:
                best, best_rng = cur, cur_rng
        else:
            if date != today:
                cur, cur_rng = 0, (None, None)
    return cur, cur_rng, best, best_rng


def fmt(d):
    return d.strftime("%b %-d, %Y") if d else "—"


def fmt_short(a, b):
    if not a:
        return "—"
    if a.year == b.year:
        return f"{a.strftime('%b %-d')} – {b.strftime('%b %-d, %Y')}"
    return f"{a.strftime('%b %-d, %Y')} – {b.strftime('%b %-d, %Y')}"


def languages(user, top_n=6):
    agg = {}
    for n in user["repositories"]["nodes"]:
        for e in n["languages"]["edges"]:
            k = (e["node"]["name"], e["node"]["color"] or "#8b93b3")
            agg[k] = agg.get(k, 0) + e["size"]
    total = sum(agg.values()) or 1
    top = sorted(agg.items(), key=lambda x: -x[1])[:top_n]
    return [(n, c, v * 100 / total) for (n, c), v in top]


# ---------------------------------------------------------------- card
def overview(user):
    c = user["contributionsCollection"]
    days = flat_days(user)
    cur, cur_rng, best, best_rng = streaks(days)
    total_stars = sum(n["stargazerCount"] for n in user["repositories"]["nodes"])
    contribs = c["contributionCalendar"]["totalContributions"]
    langs = languages(user)

    stats = [
        ("commit", "Commits",      c["totalCommitContributions"] + c["restrictedContributionsCount"]),
        ("star",   "Stars earned", total_stars),
        ("repo",   "Repositories", user["repositories"]["totalCount"]),
        ("pr",     "Pull requests", user["pullRequests"]["totalCount"]),
        ("issue",  "Issues",       user["issues"]["totalCount"]),
        ("people", "Followers",    user["followers"]["totalCount"]),
    ]

    # ---- layout constants
    PAD = 22
    HEAD_H = 58
    ROW_Y = HEAD_H + 26          # first stat row baseline
    COL_L, COL_LW = PAD, 300     # left panel (stats)
    COL_R = PAD + COL_LW + 16    # right panel (languages)
    COL_RW = W - COL_R - PAD
    BODY_H = 6 * 27 + 14
    STREAK_Y = ROW_Y + BODY_H + 18
    STREAK_H = 92
    HEAT_Y = STREAK_Y + STREAK_H + 18
    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    gap = 3
    # size cells so the grid spans the full content width
    cell = max(7, int((W - 2 * PAD + gap) / len(weeks)) - gap)
    HEAT_H = 22 + 7 * (cell + gap) + 22
    H = HEAT_Y + HEAT_H + 14

    o = []
    a = o.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
      f'viewBox="0 0 {W} {H}" role="img" aria-label="{esc(USER)} GitHub overview">')
    a(f'''<style>
    .h{{font:700 20px {FONT};fill:{TITLE}}}
    .sec{{font:600 12px {FONT};fill:{MUTED};letter-spacing:.09em}}
    .lbl{{font:400 14px {FONT};fill:{TEXT}}}
    .val{{font:700 15px {FONT};fill:{ACCENT}}}
    .big{{font:700 30px {FONT};fill:{TEXT}}}
    .bigf{{font:700 34px {FONT};fill:{FLAME}}}
    .cap{{font:600 12px {FONT};fill:{TITLE}}}
    .sub{{font:400 11px {FONT};fill:{MUTED}}}
    .foot{{font:400 11px {MONO};fill:{MUTED}}}
    .fade{{opacity:0;animation:f .6s ease forwards}}
    @keyframes f{{to{{opacity:1}}}}
    @keyframes grow{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
    </style>''')
    a(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="{BG}" stroke="{BORDER}"/>')

    # header
    a(f'<text x="{PAD}" y="34" class="h">{esc(USER)} · GitHub Overview</text>')
    a(f'<text x="{W-PAD}" y="34" class="sub" text-anchor="end">'
      f'joined {datetime.datetime.fromisoformat(user["createdAt"].replace("Z","+00:00")).strftime("%b %Y")}</text>')
    a(f'<line x1="{PAD}" y1="{HEAD_H-14}" x2="{W-PAD}" y2="{HEAD_H-14}" stroke="{BORDER}"/>')

    # ---- left: stats
    a(f'<text x="{COL_L}" y="{ROW_Y-8}" class="sec">ACTIVITY</text>')
    y = ROW_Y + 22
    for i, (ic, label, val) in enumerate(stats):
        a(f'<g class="fade" style="animation-delay:{.06*i:.2f}s">'
          f'<g transform="translate({COL_L+1},{y-12}) scale(.88)" fill="{TITLE}"><path d="{ICONS[ic]}"/></g>'
          f'<text x="{COL_L+26}" y="{y}" class="lbl">{label}</text>'
          f'<text x="{COL_L+COL_LW-10}" y="{y}" class="val" text-anchor="end">{val:,}</text></g>')
        y += 27

    # divider between columns
    a(f'<line x1="{COL_R-8}" y1="{ROW_Y-24}" x2="{COL_R-8}" y2="{ROW_Y+BODY_H}" stroke="{BORDER}"/>')

    # ---- right: languages
    a(f'<text x="{COL_R}" y="{ROW_Y-8}" class="sec">MOST USED LANGUAGES</text>')
    bar_y = ROW_Y + 12
    bar_w = COL_RW
    a(f'<clipPath id="bar"><rect x="{COL_R}" y="{bar_y}" width="{bar_w}" height="11" rx="5.5"/></clipPath>')
    a(f'<g clip-path="url(#bar)">')
    x = float(COL_R)
    for name, color, pct in langs:
        w = bar_w * pct / 100
        a(f'<rect x="{x:.2f}" y="{bar_y}" width="{w:.2f}" height="11" fill="{color}" '
          f'style="transform-origin:{x:.2f}px 0;animation:grow .9s ease-out"/>')
        x += w
    if x < COL_R + bar_w:
        a(f'<rect x="{x:.2f}" y="{bar_y}" width="{COL_R+bar_w-x:.2f}" height="11" fill="{MUTED}" opacity=".35"/>')
    a('</g>')

    ly = bar_y + 34
    for i, (name, color, pct) in enumerate(langs):
        cx = COL_R + (i % 2) * (COL_RW // 2)
        if i % 2 == 0 and i:
            ly += 26
        a(f'<g class="fade" style="animation-delay:{.5+.05*i:.2f}s">'
          f'<circle cx="{cx+5}" cy="{ly-4}" r="5" fill="{color}"/>'
          f'<text x="{cx+17}" y="{ly}" class="lbl">{esc(name)} '
          f'<tspan fill="{MUTED}">{pct:.1f}%</tspan></text></g>')

    # ---- streak band
    a(f'<rect x="{PAD}" y="{STREAK_Y}" width="{W-2*PAD}" height="{STREAK_H}" rx="9" '
      f'fill="{PANEL}" stroke="{BORDER}"/>')
    third = (W - 2 * PAD) / 3
    cells = [
        (f"{contribs:,}", "Total contributions", "past 12 months", False),
        (f"{cur}", "Current streak", fmt_short(*cur_rng) if cur else "no active streak", True),
        (f"{best}", "Longest streak", fmt_short(*best_rng), False),
    ]
    for i, (big, cap, sub, flame) in enumerate(cells):
        cx = PAD + third * (i + .5)
        if flame:
            a(f'<g transform="translate({cx-58},{STREAK_Y+26})">'
              f'<circle cx="0" cy="16" r="20" fill="none" stroke="{FLAME}" stroke-width="2" opacity=".55">'
              f'<animate attributeName="r" values="20;23;20" dur="3s" repeatCount="indefinite"/>'
              f'<animate attributeName="opacity" values=".55;.15;.55" dur="3s" repeatCount="indefinite"/>'
              f'</circle>'
              f'<path transform="translate(-8,6) scale(1.05)" fill="{FLAME}" '
              f'd="M8 0C8 0 3 4.5 3 9a5 5 0 0010 0c0-1.6-.9-3-1.8-4.1-.5.9-1.2 1.5-1.9 1.5C11.4 4.3 9.8 1.5 8 0z"/>'
              f'</g>')
            a(f'<text x="{cx+18}" y="{STREAK_Y+40}" class="bigf" text-anchor="middle">{big}</text>')
            a(f'<text x="{cx+18}" y="{STREAK_Y+62}" class="cap" text-anchor="middle">{cap}</text>')
            a(f'<text x="{cx+18}" y="{STREAK_Y+79}" class="sub" text-anchor="middle">{esc(sub)}</text>')
        else:
            a(f'<text x="{cx}" y="{STREAK_Y+38}" class="big" text-anchor="middle">{big}</text>')
            a(f'<text x="{cx}" y="{STREAK_Y+60}" class="cap" text-anchor="middle">{cap}</text>')
            a(f'<text x="{cx}" y="{STREAK_Y+77}" class="sub" text-anchor="middle">{esc(sub)}</text>')
        if i:
            lx = PAD + third * i
            a(f'<line x1="{lx}" y1="{STREAK_Y+16}" x2="{lx}" y2="{STREAK_Y+STREAK_H-16}" stroke="{BORDER}"/>')

    # ---- heatmap (last 53 weeks, drawn from the same calendar)
    a(f'<text x="{PAD}" y="{HEAT_Y+10}" class="sec">CONTRIBUTION HEATMAP</text>')
    peak = max((d["contributionCount"] for w in weeks for d in w["contributionDays"]), default=0) or 1
    grid_w = len(weeks) * (cell + gap) - gap
    gx = PAD + (W - 2 * PAD - grid_w) / 2
    gy = HEAT_Y + 22
    for wi, wk in enumerate(weeks):
        for d in wk["contributionDays"]:
            dow = datetime.date.fromisoformat(d["date"]).isoweekday() % 7
            n = d["contributionCount"]
            # log scale: a 3-commit day should not look identical to a 40-commit day
            lvl = 0 if n == 0 else min(4, 1 + int(math.log1p(n) / math.log1p(peak) * 3.999))
            a(f'<rect x="{gx+wi*(cell+gap):.1f}" y="{gy+dow*(cell+gap)}" width="{cell}" height="{cell}" '
              f'rx="2" fill="{HEAT[lvl]}"><title>{d["date"]}: {n}</title></rect>')
    # legend
    lgx = W - PAD - 5 * (cell + gap) - 36
    lgy = gy + 7 * (cell + gap) + 5
    a(f'<text x="{lgx-6}" y="{lgy+9}" class="sub" text-anchor="end">less</text>')
    for i, col in enumerate(HEAT):
        a(f'<rect x="{lgx+i*(cell+gap)}" y="{lgy}" width="{cell}" height="{cell}" rx="2" fill="{col}"/>')
    a(f'<text x="{lgx+5*(cell+gap)+2}" y="{lgy+9}" class="sub">more</text>')
    a(f'<text x="{PAD}" y="{lgy+9}" class="foot">generated {datetime.date.today().isoformat()} '
      f'by scripts/gen_stats.py</text>')

    a('</svg>')
    return "\n".join(o)


if __name__ == "__main__":
    if not TOKEN:
        sys.exit("GITHUB_TOKEN / GH_TOKEN required")
    u = fetch()
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    p = os.path.join(ROOT, "assets", "overview.svg")
    with open(p, "w", encoding="utf-8") as f:
        f.write(overview(u))
    print("wrote assets/overview.svg")
