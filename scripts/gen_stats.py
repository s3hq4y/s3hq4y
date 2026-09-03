#!/usr/bin/env python3
"""Generate a single self-contained GitHub overview card (SVG).

No third-party badge services: data comes straight from the GitHub GraphQL API
and every pixel is drawn here, so the card can never 503 or rate-limit.

Usage:  GITHUB_TOKEN=... python scripts/gen_stats.py [username]
        python scripts/gen_stats.py --replay [old.svg]   (re-render cached card
        data parsed back out of a previously generated overview.svg — handy
        when no token is at hand)
Writes: assets/overview.svg
"""
import datetime
import json
import math
import os
import re
import sys
import urllib.request

USER = "s3hq4y"
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

QUERY = """
query($login:String!){
  user(login:$login){
    createdAt
    followers{totalCount}
    repositories(first:100, ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC){
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

# ------------------------------------------------------------- theme
from _retro_theme import (ADV, CONTENT_Y, HEAT, LINE, LINE_DIM, SCREEN, TEXT,
                          esc, window)

LANG_RAMP = ["#7dff7d", "#5fff5f", "#4dcc4d", "#2f9e2f", "#2a842a", "#236b23"]

C = dict(bg=SCREEN, bar="#0c150c", border=LINE_DIM, dim=TEXT["dim"],
         fg=TEXT["fg"], cy=TEXT["cy"], gr=TEXT["gr"], ye=TEXT["ye"],
         ma=TEXT["ma"], rd=TEXT["rd"], bl=TEXT["bl"])


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}",
                 "Content-Type": "application/json",
                 "User-Agent": "readme-overview"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["data"]["user"]


# ------------------------------------------------------------- analysis
def flat_days(weeks):
    days = []
    for wk in weeks:
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
    # no %-d: it is glibc-only and explodes on Windows/strftime
    return f"{d.strftime('%b')} {d.day}, {d.year}" if d else "—"


def fmt_short(a, b):
    if not a:
        return "—"
    if a.year == b.year:
        return f"{a.strftime('%b')} {a.day} – {b.strftime('%b')} {b.day}, {b.year}"
    return f"{a.strftime('%b')} {a.day}, {a.year} – {b.strftime('%b')} {b.day}, {b.year}"


def languages(user, top_n=6):
    agg = {}
    for n in user["repositories"]["nodes"]:
        for e in n["languages"]["edges"]:
            k = (e["node"]["name"], e["node"]["color"] or "#4d8f4d")
            agg[k] = agg.get(k, 0) + e["size"]
    total = sum(agg.values()) or 1
    top = sorted(agg.items(), key=lambda x: -x[1])[:top_n]
    return [(n, c, v * 100 / total) for (n, c), v in top]


def collect(user):
    """Reduce a GraphQL user payload to the flat data the card needs."""
    c = user["contributionsCollection"]
    weeks = c["contributionCalendar"]["weeks"]
    days = flat_days(weeks)
    cur, cur_rng, best, best_rng = streaks(days)
    return dict(
        stats=[
            ("commits",      c["totalCommitContributions"] + c["restrictedContributionsCount"]),
            ("stars",        sum(n["stargazerCount"] for n in user["repositories"]["nodes"])),
            ("public_repos", user["repositories"]["totalCount"]),
            ("pull_reqs",    user["pullRequests"]["totalCount"]),
            ("issues",       user["issues"]["totalCount"]),
            ("followers",    user["followers"]["totalCount"]),
        ],
        langs=languages(user),
        contribs=c["contributionCalendar"]["totalContributions"],
        cur=cur, cur_sub=fmt_short(*cur_rng),
        best=best, best_sub=fmt_short(*best_rng),
        weeks=[[(d["date"], d["contributionCount"]) for d in w["contributionDays"]]
               for w in weeks],
        generated=datetime.date.today().isoformat(),
    )


# ------------------------------------------------------------ replay --
def _num(s):
    return int(s.replace(",", ""))


def parse_old_svg(path):
    """Recover the card data from a previously generated overview.svg."""
    src = open(path, encoding="utf-8").read()

    def texts(pat):
        return [(float(x), float(y), t) for x, y, t in
                re.findall(pat, src)]

    # -- stats rows: key at cx+24, right-aligned bold value at cx+415
    keys = texts(r'<text x="([\d.]+)" y="([\d.]+)" class="m fg">([^<]+)</text>')
    vals = texts(r'<text x="([\d.]+)" y="([\d.]+)" text-anchor="end" '
                 r'class="m b"><tspan fill="#b9ffb9">([^<]+)</tspan></text>')
    # two columns share each baseline: value sits 391px right of its key
    vby = {(x, y): t for x, y, t in vals}
    stats, seen = [], set()
    for x, y, k in keys:
        if (x + 391, y) in vby and (x, y) not in seen and "%" not in k:
            stats.append((k, _num(vby[(x + 391, y)])))
            seen.add((x, y))
    if len(stats) != 6:
        sys.exit(f"replay: expected 6 stat rows, found {len(stats)}")

    # -- language rows: name + left bar + right-aligned "pct%"
    pcts = texts(r'<text x="([\d.]+)" y="([\d.]+)" text-anchor="end" '
                 r'class="m dim">([\d.]+)%</text>')
    pby = {(x, y): p for x, y, p in pcts}
    bars = re.findall(r'<tspan fill="(#[0-9a-fA-F]{6})">[^<]*</tspan>'
                      r'<tspan class="dim">', src)
    lang_rows = sorted([k for k in keys if (k[0] + 391, k[1]) in pby],
                       key=lambda k: k[1])
    langs = []
    for (x, y, name), col in zip(lang_rows, bars):
        langs.append((name, col, float(pby[(x + 391, y)])))

    # -- streak cells: big number / caption / sub, three centered groups
    bigs = [(x, y, re.sub(r"<[^>]+>", "", t).strip().replace("\u25b2", "").strip())
            for x, y, t in texts(r'<text x="([\d.]+)" y="([\d.]+)" text-anchor="middle" '
                                 r'class="m big b" fill="#[0-9a-fA-F]{6}">(.*?)</text>')]
    caps = {y: t for x, y, t in texts(r'<text x="([\d.]+)" y="([\d.]+)" text-anchor="middle" '
                                      r'class="m dim">(.*?)</text>')}
    subs = {y: t for x, y, t in texts(r'<text x="([\d.]+)" y="([\d.]+)" text-anchor="middle" '
                                      r'class="m sm dim">(.*?)</text>')}
    bigs.sort(key=lambda b: b[0])
    cells = []
    for x, y, big in bigs:
        big_txt = re.sub(r"<[^>]+>", "", big)
        cells.append((_num(re.sub(r"[^0-9,]", "", big_txt)),
                      caps.get(y + 18, ""), subs.get(y + 34, "")))
    if len(cells) != 3:
        sys.exit(f"replay: expected 3 streak cells, found {len(cells)}")

    # -- heatmap: every cell carries "<title>date: n</title>"
    flat = [(d, int(n)) for d, n in
            re.findall(r"<title>(\d{4}-\d{2}-\d{2}): (\d+)</title>", src)]
    weeks = [flat[i:i + 7] for i in range(0, len(flat), 7)]

    gen = re.search(r"generated (\d{4}-\d{2}-\d{2})", src)
    return dict(
        stats=stats, langs=langs,
        contribs=sum(n for _, n in flat),
        cur=cells[1][0], cur_sub=cells[1][2],
        best=cells[2][0], best_sub=cells[2][2],
        weeks=weeks,
        generated=gen.group(1) if gen else datetime.date.today().isoformat(),
    )


# ---------------------------------------------------------------- card
LH = 19
W = 900
PAD = 26
X = PAD + 4


def render_card(d, title_user=None):
    out = []

    def T(x, y, cls, txt, anchor=None, size=None):
        a = f' text-anchor="{anchor}"' if anchor else ""
        s = f' font-size="{size}"' if size else ""
        out.append(f'    <text x="{x:.0f}" y="{y}"{a}{s} class="{cls}">{txt}</text>')

    CURSOR = ('<tspan class="fg">\u2588<animate attributeName="opacity" '
              'values="1;1;0;0" dur="1.1s" repeatCount="indefinite"/></tspan>')

    def prompt(y, cmd, caret=False):
        # caret lives inside the same text run -> always one cell after the text
        T(X, y, "m", '<tspan class="gr b">&gt;</tspan><tspan class="cy b">  ~/dev</tspan>'
          '<tspan class="dim">&#160;git:(</tspan><tspan class="rd">main</tspan>'
          f'<tspan class="dim">)&#160;</tspan><tspan class="fg">{cmd}</tspan>'
          f'{CURSOR if caret else ""}')

    # ---- block 1: gh stats
    y = CONTENT_Y
    prompt(y, "gh api graphql --stats")
    y += LH + 6

    stats = d["stats"]
    COL2 = X + 436
    for i, (k, v) in enumerate(stats):
        cx = X if i % 2 == 0 else COL2
        ly = y + (i // 2) * LH
        tee = "\u2514\u2500" if i // 2 == 2 else "\u251c\u2500"
        T(cx, ly, "m dim", tee)
        T(cx + 24, ly, "m fg", esc(k))
        T(cx + 150, ly, "m dim", "\u00b7" * 26)
        T(cx + 415, ly, "m b", f'<tspan fill="{C["ma"]}">{v:,}</tspan>', anchor="end")
    y += 3 * LH + 14

    # ---- block 2: languages
    prompt(y, "langstat --top 6")
    y += LH + 6
    BAR = 20
    for i, (name, _old_color, pct) in enumerate(d["langs"]):
        color = LANG_RAMP[i % len(LANG_RAMP)]
        cx = X if i % 2 == 0 else COL2
        ly = y + (i // 2) * LH
        tee = "\u2514\u2500" if i // 2 == 2 else "\u251c\u2500"
        filled = max(1, round(pct / 100 * BAR)) if pct > 0 else 0
        full = "\u2588" * filled
        empty = "\u2591" * (BAR - filled)
        T(cx, ly, "m dim", tee)
        T(cx + 24, ly, "m fg", esc(name))
        T(cx + 150, ly, "m",
          f'<tspan fill="{color}">{full}</tspan>'
          f'<tspan class="dim">{empty}</tspan>')
        T(cx + 415, ly, "m dim", f"{pct:.1f}%", anchor="end")
    y += 3 * LH + 14

    # ---- block 3: streaks
    prompt(y, "streak --summary")
    y += LH + 6
    cells = [
        (f'{d["contribs"]:,}', "total contributions", "past 12 months", C["cy"]),
        (f'{d["cur"]}', "current streak", d["cur_sub"], C["rd"]),
        (f'{d["best"]}', "longest streak", d["best_sub"], C["ye"]),
    ]
    bw = (W - 2 * PAD - 16) / 3
    for i, (big, cap, sub, col) in enumerate(cells):
        bx = PAD + i * (bw + 8)
        out.append(f'    <rect x="{bx:.0f}" y="{y-2}" width="{bw:.0f}" height="70" rx="3" '
                   f'fill="{C["bar"]}" stroke="{C["border"]}"/>')
        mid = bx + bw / 2
        flame = '<tspan fill="' + C["rd"] + '"> \u2191</tspan>' if i == 1 else ""
        out.append(f'    <text x="{mid:.0f}" y="{y+30}" text-anchor="middle" '
                   f'class="m big b" fill="{col}">{big}{flame}</text>')
        T(mid, y + 48, "m dim", esc(cap), anchor="middle")
        T(mid, y + 64, "m sm dim", esc(sub), anchor="middle")
    y += 70 + 22

    # ---- block 4: heatmap
    prompt(y, "heatmap --since 1y")
    y += LH + 8
    gap = 3
    weeks = d["weeks"]
    cell = max(7, int((W - 2 * PAD + gap) / len(weeks)) - gap)
    grid_w = len(weeks) * (cell + gap) - gap
    gx = PAD + (W - 2 * PAD - grid_w) / 2
    for wi, wk in enumerate(weeks):
        for di, (date, n) in enumerate(wk):
            dow = datetime.date.fromisoformat(date).isoweekday() % 7
            lvl = min(n, 5)
            out.append(f'    <rect x="{gx+wi*(cell+gap):.1f}" y="{y+dow*(cell+gap)}" '
                       f'width="{cell}" height="{cell}" rx="1.5" fill="{HEAT[lvl]}">'
                       f'<title>{date}: {n}</title></rect>')
    y += 7 * (cell + gap) + 6
    lgx = W - PAD - 6 * (cell + gap) - 38
    T(lgx - 6, y + 9, "m sm dim", "0", anchor="end")
    for i, col in enumerate(HEAT):
        out.append(f'    <rect x="{lgx+i*(cell+gap)}" y="{y}" width="{cell}" height="{cell}" '
                   f'rx="1.5" fill="{col}"/>')
    T(lgx + 6 * (cell + gap) + 4, y + 9, "m sm dim", "5+")
    T(X, y + 9, "m sm dim",
      f'generated {d["generated"]} \u00b7 scripts/gen_stats.py')
    y += cell + 14

    # ---- trailing prompt
    y_last = y + 14
    prompt(y_last, "", caret=True)

    return window(
        W, y_last + 50, f"{(title_user or USER).upper()}@EARTH \u2014 GH STATS",
        out, uid="o",
        tag="VAULT-TEC DB",
        foot_left="CONTRIBUTION LEDGER \u00b7 HOLOTAPE",
        foot_right="SIG 640K OK",
        label=f"{title_user or USER} GitHub overview terminal")


if __name__ == "__main__":
    argv = [a for a in sys.argv[1:]]
    replay = "--replay" in argv
    argv = [a for a in argv if a != "--replay"]
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    p = os.path.join(ROOT, "assets", "overview.svg")
    if replay:
        src = argv[0] if argv else p
        d = parse_old_svg(src)
    else:
        if argv:
            USER = argv[0]
        if not TOKEN:
            sys.exit("GITHUB_TOKEN / GH_TOKEN required (or use --replay)")
        d = collect(fetch())
    with open(p, "w", encoding="utf-8") as f:
        f.write(render_card(d))
    print("wrote assets/overview.svg")
