#!/usr/bin/env python3
"""Generate self-hosted GitHub stats cards (light + dark) from the GraphQL API.

Usage: GITHUB_TOKEN=... python3 scripts/stats_card.py <username> <out_dir>
Counts only PUBLIC, non-fork repositories owned by the user, so numbers are
reproducible by anyone. Runs daily in .github/workflows/profile-assets.yml.
"""
import json, os, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

FONT = "Segoe UI, Ubuntu, Helvetica Neue, Arial, sans-serif"
THEMES = {
    "light": dict(bg="#FFFFFF", border="#D0D7DE", title="#1F2328", text="#57606A", value="#1F2328", track="#EAEEF2"),
    "dark": dict(bg="#161B22", border="#30363D", title="#F0F6FC", text="#9DA7B3", value="#F0F6FC", track="#21262D"),
}
QUERY = """
query($login: String!) {
  user(login: $login) {
    name login createdAt
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions totalPullRequestContributions totalIssueContributions
      restrictedContributionsCount
      contributionCalendar { totalContributions }
    }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) {
      totalCount
      nodes { name stargazerCount languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } } }
    }
  }
}"""


def fetch(login: str) -> dict:
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "profile-stats"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
            if "errors" in data:
                raise RuntimeError(data["errors"])
            user = data["data"]["user"]
            # exclude the profile repo itself (its helper scripts are not project work)
            user["repositories"]["nodes"] = [n for n in user["repositories"]["nodes"] if n["name"].lower() != login.lower()]
            user["repositories"]["totalCount"] = len(user["repositories"]["nodes"])
            return user
        except Exception:  # transient network errors
            if attempt == 2:
                raise


def card(title: str, body: str, c: dict) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="250" viewBox="0 0 600 250" role="img" aria-label="{escape(title)}">
  <defs>
    <linearGradient id="b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6366F1"/><stop offset="1" stop-color="#06B6D4"/></linearGradient>
  </defs>
  <style>.h{{font:700 21px {FONT};fill:{c["title"]}}}.l{{font:15px {FONT};fill:{c["text"]}}}.v{{font:700 26px {FONT};fill:{c["value"]}}}.s{{font:600 14px {FONT};fill:{c["text"]}}}</style>
  <rect x="1" y="1" width="598" height="248" rx="18" fill="{c["bg"]}" stroke="{c["border"]}"/>
  <rect x="28" y="30" width="4" height="22" rx="2" fill="url(#b)"/>
  <text x="42" y="48" class="h">{escape(title)}</text>
  {body}
</svg>
'''


def overview(u: dict, c: dict) -> str:
    cc = u["contributionsCollection"]
    items = [
        ("Contributions (last year)", cc["contributionCalendar"]["totalContributions"]),
        ("Public repositories", u["repositories"]["totalCount"]),
        ("Commits (last year)", cc["totalCommitContributions"] + cc["restrictedContributionsCount"]),
        ("Pull requests (last year)", cc["totalPullRequestContributions"]),
        ("Languages used", len({e["node"]["name"] for n in u["repositories"]["nodes"] for e in n["languages"]["edges"]})),
        ("On GitHub since", datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00")).year),
    ]
    out = []
    for i, (label, val) in enumerate(items):
        x, y = 42 + (i % 2) * 280, 104 + (i // 2) * 56
        out.append(f'<text x="{x}" y="{y}" class="v">{val}</text><text x="{x}" y="{y + 22}" class="l">{escape(label)}</text>')
    return card("GitHub overview", "".join(out), c)


def languages(u: dict, c: dict) -> str:
    totals, colors = {}, {}
    for n in u["repositories"]["nodes"]:
        for e in n["languages"]["edges"]:
            name = e["node"]["name"]
            totals[name] = totals.get(name, 0) + e["size"]
            colors[name] = e["node"]["color"] or "#8B949E"
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:6]
    total = sum(v for _, v in top) or 1
    x, bar = 42, []
    for name, v in top:
        w = 516 * v / total
        bar.append(f'<rect x="{x:.1f}" y="76" width="{max(w, 2):.1f}" height="12" fill="{colors[name]}"/>')
        x += w
    rows = []
    for i, (name, v) in enumerate(top):
        cx, cy = 42 + (i % 2) * 280, 126 + (i // 2) * 40
        rows.append(f'<circle cx="{cx + 6}" cy="{cy - 5}" r="6" fill="{colors[name]}"/>'
                    f'<text x="{cx + 20}" y="{cy}" class="s">{escape(name)} <tspan fill-opacity="0.7">{100 * v / total:.1f}%</tspan></text>')
    body = (f'<clipPath id="r"><rect x="42" y="76" width="516" height="12" rx="6"/></clipPath>'
            f'<rect x="42" y="76" width="516" height="12" rx="6" fill="{c["track"]}"/><g clip-path="url(#r)">{"".join(bar)}</g>{"".join(rows)}'
            f'<text x="42" y="236" class="l" font-size="12">Public, non-fork repos · updated {datetime.now(timezone.utc):%Y-%m-%d}</text>')
    return card("Top languages", body, c)


if __name__ == "__main__":
    login, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    u = fetch(login)
    for th, c in THEMES.items():
        (out / f"stats-overview-{th}.svg").write_text(overview(u, c), encoding="utf-8")
        (out / f"stats-languages-{th}.svg").write_text(languages(u, c), encoding="utf-8")
    print("stats cards written to", out)
