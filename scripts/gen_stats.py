#!/usr/bin/env python3
"""Generate Swiss International Style GitHub statistics and contribution SVGs."""

import datetime
import html
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

USER = "s3hq4y"
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

QUERY = """
query($login:String!){
  user(login:$login){
    name
    createdAt
    followers{totalCount}
    repositories(first:100, ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC){
      totalCount
      nodes{
        name stargazerCount
        languages(first:8, orderBy:{field:SIZE,direction:DESC}){
          edges{size node{name color}}
        }
      }
    }
    contributionsCollection{
      totalCommitContributions restrictedContributionsCount
      contributionCalendar{
        totalContributions
        weeks{contributionDays{date contributionCount}}
      }
    }
    pullRequests{totalCount}
    issues{totalCount}
  }
}
"""

BG = "#111114"
INK = "#f2f0f0"
MUTED = "#a09a9f"
LINE = "#363238"
RED = "#ff4655"
PALETTE = ["#29262b", "#49232a", "#70252f", "#a52b38", "#d93645", RED]
FONT = "Arial, Helvetica, sans-serif"


def esc(value):
    return html.escape(str(value), quote=True)


def fetch(username):
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN or GH_TOKEN environment variable is required.")
    payload = json.dumps({
        "query": QUERY,
        "variables": {"login": username},
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "swiss-github-readme",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API HTTP {error.code}: {detail[:500]}") from error
    if result.get("errors"):
        messages = "; ".join(item.get("message", "GraphQL error") for item in result["errors"])
        raise RuntimeError(f"GitHub GraphQL error: {messages}")
    user = result.get("data", {}).get("user")
    if user is None:
        raise RuntimeError(f"GitHub user not found: {username}")
    return user


def flat_days(weeks):
    days = []
    for week in weeks:
        for day in week["contributionDays"]:
            days.append((
                datetime.date.fromisoformat(day["date"]),
                day["contributionCount"],
            ))
    days.sort()
    return days


def streaks(days):
    if not days:
        return 0, (None, None), 0, (None, None)
    today = days[-1][0]
    best = current = 0
    best_range = current_range = (None, None)
    for date, count in days:
        if count > 0:
            current = current + 1 if current else 1
            current_range = (date if current == 1 else current_range[0], date)
            if current > best:
                best, best_range = current, current_range
        elif date != today:
            current, current_range = 0, (None, None)
    return current, current_range, best, best_range


def fmt_short(start, end):
    if not start:
        return "—"
    if start.year == end.year:
        return f"{start.strftime('%b')} {start.day} – {end.strftime('%b')} {end.day}, {end.year}"
    return f"{start.strftime('%b')} {start.day}, {start.year} – {end.strftime('%b')} {end.day}, {end.year}"


def languages(user, top_n=6):
    aggregate = {}
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            key = (edge["node"]["name"], edge["node"]["color"] or "#777777")
            aggregate[key] = aggregate.get(key, 0) + edge["size"]
    total = sum(aggregate.values()) or 1
    top = sorted(aggregate.items(), key=lambda item: -item[1])[:top_n]
    return [(name, color, size * 100 / total) for (name, color), size in top]


def collect(user):
    contribution = user["contributionsCollection"]
    calendar = contribution["contributionCalendar"]
    weeks = calendar["weeks"]
    days = flat_days(weeks)
    current, current_range, best, best_range = streaks(days)
    return {
        "display_name": (user.get("name") or "Christina!"),
        "stats": [
            ("COMMITS", contribution["totalCommitContributions"] + contribution["restrictedContributionsCount"]),
            ("STARS", sum(repo["stargazerCount"] for repo in user["repositories"]["nodes"])),
            ("PUBLIC REPOSITORIES", user["repositories"]["totalCount"]),
            ("PULL REQUESTS", user["pullRequests"]["totalCount"]),
            ("ISSUES", user["issues"]["totalCount"]),
            ("FOLLOWERS", user["followers"]["totalCount"]),
        ],
        "langs": languages(user),
        "contribs": calendar["totalContributions"],
        "cur": current,
        "cur_sub": fmt_short(*current_range),
        "best": best,
        "best_sub": fmt_short(*best_range),
        "weeks": [
            [(day["date"], day["contributionCount"]) for day in week["contributionDays"]]
            for week in weeks
        ],
        "generated": datetime.date.today().isoformat(),
    }


def svg_start(width, height, title, description):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{esc(title)}</title>',
        f'<desc id="desc">{esc(description)}</desc>',
        f'<rect width="{width}" height="{height}" fill="{BG}"/>',
        f'<g font-family="{FONT}" fill="{INK}">',
    ]


def text(x, y, value, size=13, weight=400, fill=INK, anchor=None, spacing=None):
    attrs = ""
    if anchor:
        attrs += f' text-anchor="{anchor}"'
    if spacing is not None:
        attrs += f' letter-spacing="{spacing}"'
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}"{attrs}>{esc(value)}</text>'
    )


def render_stats(data, username):
    width, height = 960, 324
    out = svg_start(
        width, height,
        f"{data['display_name']} GitHub statistics",
        "GitHub activity metrics, language distribution, and contribution streaks.",
    )
    out += [
        text(32, 38, f"{data['display_name'].upper()} / PROFILE", 11, 700, RED, spacing=1.8),
        text(32, 78, "Statistics", 34, 700),
        text(928, 42, data["display_name"], 11, 700, MUTED, "end", 0.5),
        text(928, 64, f"UPDATED {data['generated']}", 10, 400, MUTED, "end"),
        f'<line x1="32" y1="98" x2="928" y2="98" stroke="{INK}" stroke-width="2"/>',
    ]

    metrics = data["stats"]
    cell_w = 146
    start_x, start_y = 32, 120
    for index, (label, value) in enumerate(metrics):
        x = start_x + index * 150
        y = start_y
        out += [
            text(x, y + 11, f"{index + 1:02d} / {label}", 9, 700, MUTED, spacing=0.5),
            text(x, y + 40, f"{value:,}", 22, 700, RED if index == 0 else INK),
            f'<line x1="{x}" y1="{y + 52}" x2="{x + cell_w}" y2="{y + 52}" stroke="{LINE}"/>',
        ]

    out += [
        text(32, 220, "LANGUAGE DISTRIBUTION", 11, 700, INK, spacing=1.1),
        text(928, 220, "TOP 6 BY CODE SIZE", 9, 400, MUTED, "end", 0.8),
    ]

    langs = data["langs"]
    if langs:
        x0, y0, total_w, gap = 32, 234, 896, 3
        available = total_w - gap * (len(langs) - 1)
        for name, color, pct in langs:
            segment = available * pct / 100
            out.append(
                f'<rect x="{x0:.2f}" y="{y0}" width="{max(0, segment):.2f}" height="8" fill="{esc(color)}"/>'
            )
            x0 += segment + gap
        label_y = 266
        for index, (name, _color, pct) in enumerate(langs):
            col = index % 3
            row = index // 3
            x = 32 + col * 304
            y = label_y + row * 24
            out += [
                f'<rect x="{x}" y="{y - 9}" width="7" height="7" fill="{esc(langs[index][1])}"/>',
                text(x + 14, y - 1, name, 11, 600),
                text(x + 288, y - 1, f"{pct:.1f}%", 10, 400, MUTED, "end"),
            ]
    else:
        out.append(text(32, 259, "No language data available", 12, 400, MUTED))

    out += [
        f'<line x1="32" y1="308" x2="928" y2="308" stroke="{INK}"/>',
        text(32, 320, f"CURRENT STREAK  {data['cur']} DAYS  /  {data['cur_sub']}", 9, 700, MUTED),
        text(928, 320, f"LONGEST  {data['best']} DAYS  /  {data['best_sub']}", 9, 700, MUTED, "end"),
        "</g></svg>",
    ]
    return "\n".join(out) + "\n"


def render_heatmap(data, username):
    weeks = data["weeks"]
    columns = max(1, len(weeks))
    cell, gap = 11, 4
    left, top = 54, 82
    grid_width = columns * (cell + gap) - gap
    width = left + grid_width + 30
    height = 220
    out = svg_start(
        width, height,
        f"{data['display_name']} contribution heatmap",
        f"{data['contribs']} contributions in the displayed contribution calendar.",
    )
    out += [
        text(24, 34, f"{data['display_name'].upper()} / CONTRIBUTION CALENDAR", 11, 700, RED, spacing=1.5),
        text(24, 61, f"{data['contribs']:,}", 25, 700),
        text(105, 60, "TOTAL CONTRIBUTIONS", 10, 700, MUTED, spacing=0.8),
    ]

    month_seen = set()
    for week_index, week in enumerate(weeks):
        for date_string, count in week:
            date = datetime.date.fromisoformat(date_string)
            day_index = date.isoweekday() % 7
            x = left + week_index * (cell + gap)
            y = top + day_index * (cell + gap)
            level = 0 if count == 0 else min(5, 1 + (count - 1) // 3)
            out.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" '
                f'rx="1" fill="{PALETTE[level]}">'
                f'<title>{esc(date_string)}: {count} contributions</title></rect>'
            )
            if date.day <= 7:
                month_key = (date.year, date.month)
                if month_key not in month_seen:
                    out.append(text(x, 75, date.strftime("%b").upper(), 8, 600, MUTED))
                    month_seen.add(month_key)

    day_labels = [(0, "SUN"), (2, "TUE"), (4, "THU")]
    for day_index, label in day_labels:
        out.append(text(24, top + day_index * (cell + gap) + 9, label, 8, 600, MUTED))

    legend_x = max(left, width - 180)
    legend_y = 190
    out.append(text(24, legend_y + 9, "LESS", 8, 600, MUTED))
    for index, color in enumerate(PALETTE):
        out.append(
            f'<rect x="{legend_x + index * 17}" y="{legend_y}" width="11" height="11" '
            f'rx="1" fill="{color}"/>'
        )
    out += [
        text(legend_x + 6 * 17 + 3, legend_y + 9, "MORE", 8, 600, MUTED),
        text(width - 24, 34, f"{data['generated']}  /  {data['display_name']}", 9, 600, MUTED, "end"),
        "</g></svg>",
    ]
    return "\n".join(out) + "\n"


def main():
    username = USER
    args = sys.argv[1:]
    if args:
        username = args[0]
    try:
        data = collect(fetch(username))
    except (RuntimeError, KeyError, ValueError, urllib.error.URLError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "stats.svg").write_text(render_stats(data, username), encoding="utf-8")
    (ASSETS / "heatmap.svg").write_text(render_heatmap(data, username), encoding="utf-8")
    print(f"Generated assets/stats.svg and assets/heatmap.svg for {username}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
