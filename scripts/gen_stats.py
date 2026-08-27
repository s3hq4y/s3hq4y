#!/usr/bin/env python3
"""Generate self-hosted GitHub stats SVG cards (no external service required).

Usage:  GITHUB_TOKEN=... python scripts/gen_stats.py [username]
Writes: assets/stats.svg, assets/langs.svg
"""
import json, os, sys, urllib.request, datetime

USER = sys.argv[1] if len(sys.argv) > 1 else "s3hq4y"
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

QUERY = """
query($login:String!){
  user(login:$login){
    followers{totalCount}
    repositories(first:100, ownerAffiliations:OWNER, isFork:false){
      totalCount
      nodes{ name stargazerCount
        languages(first:8, orderBy:{field:SIZE,direction:DESC}){
          edges{ size node{ name color } } } }
    }
    contributionsCollection{
      totalCommitContributions restrictedContributionsCount
      contributionCalendar{ totalContributions } }
    pullRequests{totalCount}
    issues{totalCount}
  }
}"""

def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json",
                 "User-Agent": "readme-stats"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["data"]["user"]

# ---------- theme (tokyonight-ish) ----------
BG, BORDER, TITLE, TEXT, MUTED, ACCENT = "#1a1b27", "#2f3348", "#70a5fd", "#c9d1d9", "#8b93b3", "#bf91f3"

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

ICONS = {  # tiny inline glyph paths (16x16 viewBox)
 "star": "M8 .25l2.06 4.18 4.61.67-3.34 3.25.79 4.59L8 10.78l-4.12 2.16.79-4.59L1.33 5.1l4.61-.67z",
 "commit": "M11.93 8.5a4 4 0 01-7.86 0H.75a.75.75 0 010-1.5h3.32a4 4 0 017.86 0h3.32a.75.75 0 010 1.5zM8 10a2 2 0 100-4 2 2 0 000 4z",
 "pr": "M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z",
 "issue": "M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM0 8a8 8 0 1116 0A8 8 0 010 8zm9 3a1 1 0 11-2 0 1 1 0 012 0zm-.25-6.25v3.5a.75.75 0 01-1.5 0v-3.5a.75.75 0 011.5 0z",
 "repo": "M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5zm10.5-1h-8a1 1 0 00-1 1v6.708A2.486 2.486 0 014.5 9h8z",
 "people": "M5.5 3.5a2 2 0 100 4 2 2 0 000-4zM2 5.5a3.5 3.5 0 115.898 2.549 5.507 5.507 0 013.034 4.084.75.75 0 11-1.482.235 4.001 4.001 0 00-7.9 0 .75.75 0 01-1.482-.236A5.507 5.507 0 013.102 8.05 3.49 3.49 0 012 5.5zM11 4a.75.75 0 100 1.5 1.75 1.75 0 11-.5 3.428.75.75 0 10-.5 1.414 3.25 3.25 0 101-6.342z",
}

CARD_H = 240  # both cards share one canvas height so they align side by side


def stats_card(u):
    total_stars = sum(n["stargazerCount"] for n in u["repositories"]["nodes"])
    c = u["contributionsCollection"]
    rows = [
        ("commit", "Total Commits", c["totalCommitContributions"] + c["restrictedContributionsCount"]),
        ("star",   "Total Stars",   total_stars),
        ("repo",   "Repositories",   u["repositories"]["totalCount"]),
        ("pr",     "Total PRs",     u["pullRequests"]["totalCount"]),
        ("issue",  "Total Issues",  u["issues"]["totalCount"]),
        ("people", "Followers",     u["followers"]["totalCount"]),
    ]
    contribs = c["contributionCalendar"]["totalContributions"]
    h = CARD_H
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="450" height="{h}" viewBox="0 0 450 {h}" role="img" aria-label="{USER} GitHub stats">',
      f'<style>.t{{font:600 18px "Segoe UI",Ubuntu,sans-serif;fill:{TITLE}}}'
      f'.l{{font:400 14px "Segoe UI",Ubuntu,sans-serif;fill:{TEXT}}}'
      f'.v{{font:700 14px "Segoe UI",Ubuntu,sans-serif;fill:{ACCENT}}}'
      f'.s{{font:400 11px "Segoe UI",Ubuntu,sans-serif;fill:{MUTED}}}'
      f'.row{{opacity:0;animation:fi .5s ease forwards}}'
      f'@keyframes fi{{to{{opacity:1}}}}</style>',
      f'<rect x="0.5" y="0.5" width="449" height="{h-1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
      f'<text x="25" y="35" class="t">{esc(USER)}\u2019s GitHub Stats</text>',
      f'<line x1="25" y1="47" x2="425" y2="47" stroke="{BORDER}"/>']
    y = 72
    for i, (ic, label, val) in enumerate(rows):
        parts.append(f'<g class="row" style="animation-delay:{0.1*i:.1f}s">'
            f'<g transform="translate(27,{y-12}) scale(0.9)" fill="{TITLE}"><path d="{ICONS[ic]}"/></g>'
            f'<text x="52" y="{y}" class="l">{label}</text>'
            f'<text x="425" y="{y}" class="v" text-anchor="end">{val}</text></g>')
        y += 25
    parts.append(f'<text x="25" y="{h-16}" class="s">{contribs} contributions in the last year '
                 f'\u00b7 updated {datetime.date.today().isoformat()}</text>')
    parts.append('</svg>')
    return "\n".join(parts)

def langs_card(u, top_n=7):
    agg = {}
    for n in u["repositories"]["nodes"]:
        for e in n["languages"]["edges"]:
            k = (e["node"]["name"], e["node"]["color"] or "#888")
            agg[k] = agg.get(k, 0) + e["size"]
    total = sum(agg.values()) or 1
    top = sorted(agg.items(), key=lambda x: -x[1])[:top_n]
    h = CARD_H
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="380" height="{h}" viewBox="0 0 380 {h}" role="img" aria-label="Most used languages">',
      f'<style>.t{{font:600 18px "Segoe UI",Ubuntu,sans-serif;fill:{TITLE}}}'
      f'.l{{font:400 12px "Segoe UI",Ubuntu,sans-serif;fill:{TEXT}}}</style>',
      f'<rect x="0.5" y="0.5" width="379" height="{h-1}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
      '<text x="25" y="35" class="t">Most Used Languages</text>',
      f'<line x1="25" y1="47" x2="355" y2="47" stroke="{BORDER}"/>',
      '<mask id="m"><rect x="25" y="62" width="330" height="10" rx="5" fill="#fff"/></mask>',
      '<g mask="url(#m)">']
    x = 25.0
    for (name, color), size in top:
        w = 330 * size / total
        p.append(f'<rect x="{x:.2f}" y="62" width="{w:.2f}" height="10" fill="{color}">'
                 f'<animate attributeName="width" from="0" to="{w:.2f}" dur="0.8s" fill="freeze"/></rect>')
        x += w
    if x < 355:
        p.append(f'<rect x="{x:.2f}" y="62" width="{355-x:.2f}" height="10" fill="{MUTED}"/>')
    p.append('</g>')
    rows_n = (len(top) + 1) // 2
    step = 26
    y = 104
    for i, ((name, color), size) in enumerate(top):
        cx = 27 + (i % 2) * 168
        if i % 2 == 0 and i:
            y += step
        p.append(f'<circle cx="{cx+5}" cy="{y-4}" r="5" fill="{color}"/>'
                 f'<text x="{cx+16}" y="{y}" class="l">{esc(name)} {size*100/total:.1f}%</text>')
    p.append('</svg>')
    return "\n".join(p)

if __name__ == "__main__":
    if not TOKEN:
        sys.exit("GITHUB_TOKEN / GH_TOKEN required")
    u = fetch()
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    for fn, svg in (("stats.svg", stats_card(u)), ("langs.svg", langs_card(u))):
        with open(os.path.join(ROOT, "assets", fn), "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote assets/" + fn)
