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
LH = 19
COLORS = dict(bg="#1a1b26", bar="#16161e", border="#2f3348", dim="#565f89",
              fg="#c0caf5", cy="#7dcfff", gr="#9ece6a", ye="#e0af68",
              ma="#bb9af7", rd="#f7768e", bl="#70a5fd")
# index == number of contributions that day (5+ clamps to the brightest)
HEAT = ["#20222f", "#1f3f5c", "#2a5f8a", "#3782b8", "#4ea6dd", "#7dcfff"]


def overview(user):
    C = COLORS
    c = user["contributionsCollection"]
    days = flat_days(user)
    cur, cur_rng, best, best_rng = streaks(days)
    total_stars = sum(n["stargazerCount"] for n in user["repositories"]["nodes"])
    contribs = c["contributionCalendar"]["totalContributions"]
    langs = languages(user)
    weeks = c["contributionCalendar"]["weeks"]

    W, PAD = 900, 26
    X = PAD + 4
    out = []

    def T(x, y, cls, txt, anchor=None):
        a = f' text-anchor="{anchor}"' if anchor else ""
        out.append(f'    <text x="{x:.0f}" y="{y}"{a} class="{cls}">{txt}</text>')

    CURSOR = ('<tspan class="fg">\u2588<animate attributeName="opacity" '
              'values="1;1;0;0" dur="1.1s" repeatCount="indefinite"/></tspan>')

    def prompt(y, cmd, caret=False):
        # caret lives inside the same text run -> always one cell after the text
        T(X, y, "m", '<tspan class="gr b">\u279c</tspan><tspan class="cy b">  ~/dev</tspan>'
          '<tspan class="dim"> git:(</tspan><tspan class="rd">main</tspan>'
          f'<tspan class="dim">) </tspan><tspan class="fg">{cmd}</tspan>'
          f'{CURSOR if caret else ""}')

    # ---- block 1: gh stats
    y = 78
    prompt(y, "gh api graphql --stats")
    y += LH + 6

    stats = [
        ("commits",  c["totalCommitContributions"] + c["restrictedContributionsCount"]),
        ("stars",    total_stars),
        ("repos",    user["repositories"]["totalCount"]),
        ("pull_reqs", user["pullRequests"]["totalCount"]),
        ("issues",   user["issues"]["totalCount"]),
        ("followers", user["followers"]["totalCount"]),
    ]
    COL2 = X + 436
    for i, (k, v) in enumerate(stats):
        cx = X if i % 2 == 0 else COL2
        ly = y + (i // 2) * LH
        tee = "\u2514\u2500" if i // 2 == 2 else "\u251c\u2500"
        T(cx, ly, "m dim", tee)
        T(cx + 24, ly, "m fg", k)
        T(cx + 150, ly, "m dim", "\u00b7" * 26)
        T(cx + 415, ly, "m b", f'<tspan fill="{C["ma"]}">{v:,}</tspan>', anchor="end")
    y += 3 * LH + 14

    # ---- block 2: languages
    prompt(y, "langstat --top 6")
    y += LH + 6
    BAR = 20
    for i, (name, color, pct) in enumerate(langs):
        cx = X if i % 2 == 0 else COL2
        ly = y + (i // 2) * LH
        tee = "\u2514\u2500" if i // 2 == 2 else "\u251c\u2500"
        filled = max(1, round(pct / 100 * BAR)) if pct > 0 else 0
        T(cx, ly, "m dim", tee)
        T(cx + 24, ly, "m fg", esc(name))
        T(cx + 150, ly, "m",
          f'<tspan fill="{color}">{"\u2588" * filled}</tspan>'
          f'<tspan class="dim">{"\u2591" * (BAR - filled)}</tspan>')
        T(cx + 415, ly, "m dim", f"{pct:.1f}%", anchor="end")
    y += 3 * LH + 14

    # ---- block 3: streaks
    prompt(y, "streak --summary")
    y += LH + 6
    cells = [
        (f"{contribs:,}", "total contributions", "past 12 months", C["cy"]),
        (f"{cur}", "current streak", fmt_short(*cur_rng) if cur else "no active streak", C["rd"]),
        (f"{best}", "longest streak", fmt_short(*best_rng), C["ye"]),
    ]
    bw = (W - 2 * PAD - 16) / 3
    for i, (big, cap, sub, col) in enumerate(cells):
        bx = PAD + i * (bw + 8)
        out.append(f'    <rect x="{bx:.0f}" y="{y-2}" width="{bw:.0f}" height="70" rx="6" '
                   f'fill="#16161e" stroke="{C["border"]}"/>')
        mid = bx + bw / 2
        flame = '<tspan fill="' + C["rd"] + '"> \u25b2</tspan>' if i == 1 else ""
        out.append(f'    <text x="{mid:.0f}" y="{y+30}" text-anchor="middle" '
                   f'class="m big b" fill="{col}">{big}{flame}</text>')
        T(mid, y + 48, "m dim", esc(cap), anchor="middle")
        T(mid, y + 64, "m sm dim", esc(sub), anchor="middle")
    y += 70 + 22

    # ---- block 4: heatmap
    prompt(y, "heatmap --since 1y")
    y += LH + 8
    gap = 3
    cell = max(7, int((W - 2 * PAD + gap) / len(weeks)) - gap)
    grid_w = len(weeks) * (cell + gap) - gap
    gx = PAD + (W - 2 * PAD - grid_w) / 2
    for wi, wk in enumerate(weeks):
        for d in wk["contributionDays"]:
            dow = datetime.date.fromisoformat(d["date"]).isoweekday() % 7
            n = d["contributionCount"]
            # absolute scale: 1,2,3,4 commits step through the ramp, 5+ is full brightness
            lvl = min(n, 5)
            out.append(f'    <rect x="{gx+wi*(cell+gap):.1f}" y="{y+dow*(cell+gap)}" '
                       f'width="{cell}" height="{cell}" rx="1.5" fill="{HEAT[lvl]}">'
                       f'<title>{d["date"]}: {n}</title></rect>')
    y += 7 * (cell + gap) + 6
    lgx = W - PAD - 6 * (cell + gap) - 38
    T(lgx - 6, y + 9, "m sm dim", "0", anchor="end")
    for i, col in enumerate(HEAT):
        out.append(f'    <rect x="{lgx+i*(cell+gap)}" y="{y}" width="{cell}" height="{cell}" '
                   f'rx="1.5" fill="{col}"/>')
    T(lgx + 6 * (cell + gap) + 4, y + 9, "m sm dim", "5+")
    T(X, y + 9, "m sm dim",
      f'generated {datetime.date.today().isoformat()} \u00b7 scripts/gen_stats.py')
    y += cell + 14

    # ---- trailing prompt
    prompt(y + 14, "", caret=True)
    H = y + 38

    head = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(USER)} GitHub overview terminal">
  <defs>
    <clipPath id="sc"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="10"/></clipPath>
    <style>
      .m {{ font-family:\'JetBrains Mono\',\'Cascadia Code\',Consolas,\'DejaVu Sans Mono\',monospace; font-size:14px }}
      .big {{ font-size:26px }} .sm {{ font-size:11px }}
      .dim{{ fill:{C["dim"]} }} .fg {{ fill:{C["fg"]} }} .cy {{ fill:{C["cy"]} }}
      .gr {{ fill:{C["gr"]} }} .rd {{ fill:{C["rd"]} }} .b {{ font-weight:700 }}
    </style>
  </defs>
  <rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10.5" fill="{C["bg"]}" stroke="{C["border"]}"/>
  <g clip-path="url(#sc)">
    <rect x="1" y="1" width="{W-2}" height="30" fill="{C["bar"]}"/>
    <circle cx="22" cy="16" r="5.5" fill="#f7768e"/>
    <circle cx="40" cy="16" r="5.5" fill="#e0af68"/>
    <circle cx="58" cy="16" r="5.5" fill="#9ece6a"/>
    <text x="{W/2}" y="21" class="m dim" text-anchor="middle">{esc(USER)}@earth: ~/dev \u2014 gh stats</text>
'''
    return head + "\n".join(out) + "\n  </g>\n</svg>\n"


if __name__ == "__main__":
    if not TOKEN:
        sys.exit("GITHUB_TOKEN / GH_TOKEN required")
    u = fetch()
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    p = os.path.join(ROOT, "assets", "overview.svg")
    with open(p, "w", encoding="utf-8") as f:
        f.write(overview(u))
    print("wrote assets/overview.svg")
