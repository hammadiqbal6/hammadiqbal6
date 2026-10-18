#!/usr/bin/env python3
"""Generate every dynamic profile asset from the GitHub API.

Usage:  GITHUB_TOKEN=... python3 scripts/profile_dynamic.py <login> <out_dir> [--readme README.md]

Writes light + dark SVGs to <out_dir> (published to the `output` branch):
  stats-overview, stats-languages, activity (12-week sparkline + streaks),
  tip (rotates daily), updated (last-refresh stamp, PKT), card-<repo> (project cards:
  curated copy + live facts).
With --readme, also rewrites the <!--START_x--> ... <!--END_x--> sections
(NOW, SHIPPED) in the README. Only PUBLIC data is shown by name; private work is
mentioned generically. Standard library only.
"""
from __future__ import annotations

import json, os, re, sys, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

PKT = timezone(timedelta(hours=5), "PKT")
FONT = "Segoe UI, Ubuntu, Helvetica Neue, Arial, sans-serif"
ROOT = Path(__file__).resolve().parent.parent
THEMES = {
    "light": dict(bg="#FFFFFF", bg2="#F6F8FA", border="#D0D7DE", title="#1F2328", text="#57606A",
                  value="#1F2328", track="#EAEEF2", chip="#EEF2FF", chipText="#4338CA", glow="0.10",
                  accent="#6366F1", area="#6366F1"),
    "dark": dict(bg="#161B22", bg2="#0D1117", border="#30363D", title="#F0F6FC", text="#9DA7B3",
                 value="#F0F6FC", track="#21262D", chip="#1E2140", chipText="#A5B4FC", glow="0.22",
                 accent="#818CF8", area="#22D3EE"),
}

# Curated copy. Facts (language, commits, last update, latest PR) are filled in live.
PROJECTS = [
    dict(repo="fullstack-crm", emoji="🗂️", tag="CRM",
         desc=["Visa-agency CRM: lead approvals, token onboarding,", "5-role RBAC, questionnaires, PDF invoices"],
         chips=["Laravel 12", "Next.js 16", "Redis", "Docker"]),
    dict(repo="bulk-excel", emoji="📊", tag="Full-stack",
         desc=["Bulk Excel import API for housing-scheme plots,", "with a separate React 19 upload UI"],
         chips=["Laravel", "Laravel Excel", "React", "Vite"]),
    dict(repo="crypto-trading-bot", emoji="🤖", tag="In progress", private=True,
         desc=["Trend-following + news-sentiment crypto bot.", "Demo / paper trading only; no proven edge yet"],
         chips=["Python", "freqtrade", "Bybit demo"]),
    dict(repo="stock-trading-bot", emoji="📈", tag="In progress", private=True,
         desc=["Trend-following + news-sentiment stock bot.", "Paper trading only; no proven edge yet"],
         chips=["Python", "Alpaca paper"]),
    dict(repo="Donewithit", emoji="📱", tag="Mobile",
         desc=["Second-hand marketplace: JWT auth, listings,", "photo posts, seller messaging, offline notice"],
         chips=["React Native", "Expo", "Express", "JWT"]),
    dict(repo="Promptopia", emoji="💬", tag="Web app",
         desc=["AI prompt-sharing app: debounced search,", "Google sign-in, CRUD, creator profiles"],
         chips=["Next.js 13", "MongoDB", "NextAuth", "Docker"]),
    dict(repo="realtor-clone-react", emoji="🏠", tag="Web app",
         desc=["Harbor Homes: rent / sale listings with image", "slider, auth flows and full listing CRUD"],
         chips=["React 18", "Router v6", "Tailwind", "CI"]),
    dict(repo="Vanslife-react", emoji="🚐", tag="Web app",
         desc=["#VanLife rentals: type filters, rent-to-cart,", "host dashboard with auth-gated CRUD"],
         chips=["React 18", "Redux Toolkit", "Formik", "Tailwind"]),
]

Q_USER = """
query($login: String!, $from: DateTime!) {
  user(login: $login) {
    login createdAt
    contributionsCollection(from: $from) {
      totalCommitContributions totalPullRequestContributions restrictedContributionsCount
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
      commitContributionsByRepository(maxRepositories: 10) {
        repository { name isPrivate url description pushedAt primaryLanguage { name } }
        contributions { totalCount }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name url pushedAt stargazerCount
        primaryLanguage { name color }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
        defaultBranchRef { target { ... on Commit { history { totalCount } committedDate } } }
        pullRequests(states: MERGED, first: 1, orderBy: {field: UPDATED_AT, direction: DESC}) {
          nodes { title number mergedAt url }
        }
      }
    }
  }
}"""
Q_SHIPPED = """
query($q: String!) {
  search(query: $q, type: ISSUE, first: 8) {
    nodes { ... on PullRequest { title number url mergedAt repository { name isPrivate } } }
  }
}"""


def gql(query: str, **variables) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
                 "Content-Type": "application/json", "User-Agent": "profile-dynamic"},
    )
    last = None
    for _ in range(4):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                data = json.load(r)
            if data.get("errors"):
                raise RuntimeError(data["errors"])
            return data["data"]
        except Exception as e:  # transient network/API errors: retry
            last = e
    raise last


# ---------- helpers ----------
def parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def ago(ts: str | None, now: datetime) -> str:
    if not ts:
        return "—"
    d = (now.date() - parse(ts).astimezone(PKT).date()).days
    if d <= 0:
        return "today"
    if d == 1:
        return "yesterday"
    if d < 30:
        return f"{d} days ago"
    if d < 365:
        return f"{d // 30} mo ago"
    return f"{d // 365} yr ago"


def clip(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def frame(w: int, h: int, label: str, c: dict, body: str, extra_style: str = "") -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">
  <defs>
    <linearGradient id="b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6366F1"/><stop offset="1" stop-color="#06B6D4"/></linearGradient>
    <radialGradient id="glow" cx="1" cy="0" r="0.9"><stop offset="0" stop-color="#6366F1" stop-opacity="{c["glow"]}"/><stop offset="1" stop-color="#6366F1" stop-opacity="0"/></radialGradient>
  </defs>
  <style>.h{{font:700 21px {FONT};fill:{c["title"]}}}.l{{font:16px {FONT};fill:{c["text"]}}}.v{{font:700 26px {FONT};fill:{c["value"]}}}.s{{font:600 15px {FONT};fill:{c["text"]}}}.m{{font:14px {FONT};fill:{c["text"]}}}{extra_style}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}</style>
  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="18" fill="{c["bg"]}" stroke="{c["border"]}"/>
  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="18" fill="url(#glow)"/>
  {body}
</svg>
'''


def heading(text: str) -> str:
    return f'<rect x="28" y="30" width="4" height="22" rx="2" fill="url(#b)"/><text x="42" y="48" class="h">{escape(text)}</text>'


# ---------- cards ----------
def overview(u: dict, repos: list, c: dict) -> str:
    cc = u["contributionsCollection"]
    langs = {e["node"]["name"] for r in repos for e in r["languages"]["edges"]}
    items = [
        ("Contributions (last year)", cc["contributionCalendar"]["totalContributions"]),
        ("Public repositories", len(repos)),
        ("Commits (last year)", cc["totalCommitContributions"] + cc["restrictedContributionsCount"]),
        ("Pull requests (last year)", cc["totalPullRequestContributions"]),
        ("Languages used", len(langs)),
        ("On GitHub since", parse(u["createdAt"]).year),
    ]
    body = [heading("GitHub overview")]
    for i, (label, val) in enumerate(items):
        x, y = 42 + (i % 2) * 280, 100 + (i // 2) * 54
        body.append(f'<text x="{x}" y="{y}" class="v">{val}</text><text x="{x}" y="{y + 22}" class="l">{escape(label)}</text>')
    return frame(600, 260, "GitHub overview", c, "".join(body))


def languages(repos: list, c: dict, now: datetime) -> str:
    totals, colors = {}, {}
    for r in repos:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            totals[n] = totals.get(n, 0) + e["size"]
            colors[n] = e["node"]["color"] or "#8B949E"
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:6]
    total = sum(v for _, v in top) or 1
    x, bars = 42, []
    for n, v in top:
        w = 516 * v / total
        bars.append(f'<rect x="{x:.1f}" y="76" width="{max(w, 2):.1f}" height="12" fill="{colors[n]}"/>')
        x += w
    rows = []
    for i, (n, v) in enumerate(top):
        cx, cy = 42 + (i % 2) * 280, 126 + (i // 2) * 40
        rows.append(f'<circle cx="{cx + 6}" cy="{cy - 5}" r="6" fill="{colors[n]}"/>'
                    f'<text x="{cx + 20}" y="{cy}" class="s">{escape(n)} <tspan fill-opacity="0.7">{100 * v / total:.1f}%</tspan></text>')
    body = (heading("Top languages") +
            f'<clipPath id="r"><rect x="42" y="76" width="516" height="12" rx="6"/></clipPath>'
            f'<rect x="42" y="76" width="516" height="12" rx="6" fill="{c["track"]}"/><g clip-path="url(#r)">{"".join(bars)}</g>{"".join(rows)}'
            f'<text x="42" y="240" class="m">Public, non-fork repos by code size</text>')
    return frame(600, 260, "Top languages", c, body)


def streaks(days: list[tuple[date, int]], today: date) -> tuple[int, int]:
    longest = run = 0
    for _, n in days:
        run = run + 1 if n > 0 else 0
        longest = max(longest, run)
    cur = 0
    for d, n in reversed(days):
        if d > today:
            continue
        if n > 0:
            cur += 1
        elif d == today:  # today not over yet; don't break the streak
            continue
        else:
            break
    return cur, longest


def activity(u: dict, c: dict, now: datetime) -> str:
    weeks = u["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [(date.fromisoformat(d["date"]), d["contributionCount"]) for w in weeks for d in w["contributionDays"]]
    cur, longest = streaks(days, now.date())
    wk = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks][-12:]
    peak = max(wk) or 1
    x0, x1, y0, y1 = 42, 558, 200, 110
    step = (x1 - x0) / (len(wk) - 1)
    pts = [(x0 + i * step, y0 - (y0 - y1) * v / peak) for i, v in enumerate(wk)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"M{x0},{y0} L" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + f" L{x1},{y0} Z"
    last30 = sum(n for d, n in days if (now.date() - d).days < 30)
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{c["area"]}"/>' for x, y in pts)
    body = (heading("Activity · last 12 weeks") +
            f'<text x="42" y="88" class="m">🔥 Current streak <tspan font-weight="700" fill="{c["value"]}">{cur}d</tspan>'
            f'   ·   Longest <tspan font-weight="700" fill="{c["value"]}">{longest}d</tspan>'
            f'   ·   Last 30 days <tspan font-weight="700" fill="{c["value"]}">{last30}</tspan></text>'
            f'<defs><linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["area"]}" stop-opacity="0.35"/><stop offset="1" stop-color="{c["area"]}" stop-opacity="0"/></linearGradient></defs>'
            f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="{c["track"]}" stroke-width="2"/>'
            f'<path d="{area}" fill="url(#a)"/>'
            f'<polyline class="ln" points="{line}" fill="none" stroke="{c["area"]}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" pathLength="1"/>'
            f'{dots}<text x="42" y="232" class="m">{len(wk)} weeks ago</text><text x="558" y="232" text-anchor="end" class="m">this week · peak {peak}/wk</text>')
    style = ".ln{stroke-dasharray:1;stroke-dashoffset:0;animation:draw 1.6s ease-out backwards}@keyframes draw{from{stroke-dashoffset:1}}"
    return frame(600, 260, "Activity over the last 12 weeks", c, body, style)


def tip(c: dict, now: datetime) -> str:
    tips = json.loads((ROOT / "scripts" / "tips.json").read_text(encoding="utf-8"))
    t = tips[now.date().toordinal() % len(tips)]
    words, lines, cur = t.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > 46:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    lines.append(cur)
    lines = lines[:5]
    txt = "".join(f'<text x="42" y="{100 + i * 30}" class="tp">{escape(l)}</text>' for i, l in enumerate(lines))
    body = heading("Dev tip of the day") + txt + f'<text x="42" y="240" class="m">Rotates daily · {now:%d %b %Y}</text>'
    return frame(600, 260, "Dev tip: " + t, c, body, f".tp{{font:19px {FONT};fill:{c['title']}}}")


def updated(c: dict, now: datetime) -> str:
    label = f"Auto-updated {now:%d %b %Y, %H:%M} PKT"
    w = 40 + len(label) * 7.4
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="28" viewBox="0 0 {w:.0f} 28" role="img" aria-label="{escape(label)}">
  <style>.p{{animation:pulse 2.4s ease-in-out infinite}}@keyframes pulse{{50%{{opacity:.35}}}}@media (prefers-reduced-motion: reduce){{.p{{animation:none}}}}</style>
  <rect x="0.5" y="0.5" width="{w - 1:.0f}" height="27" rx="13.5" fill="{c["bg"]}" stroke="{c["border"]}"/>
  <circle class="p" cx="16" cy="14" r="4.5" fill="#22C55E"/>
  <text x="28" y="18.5" font-family="{FONT}" font-size="12.5" font-weight="600" fill="{c["text"]}">{escape(label)}</text>
</svg>
'''


def project_card(p: dict, info: dict | None, c: dict, theme: str, now: datetime) -> str:
    wip = p.get("private")
    sfill, stext = (("#FEF3C7", "#92400E") if theme == "light" else ("#3B2F12", "#FCD34D")) if wip else (c["chip"], c["chipText"])
    status = (p["tag"] + (" · private" if wip else "")).upper()
    sw = 24 + len(status) * 8
    x, chips = 28, []
    for ch in p["chips"]:
        w = 22 + len(ch) * 8.6
        chips.append(f'<rect x="{x}" y="128" width="{w:.0f}" height="30" rx="15" fill="{c["bg2"]}" stroke="{c["border"]}"/>'
                     f'<text x="{x + w / 2:.0f}" y="148" text-anchor="middle" class="chip">{escape(ch)}</text>')
        x += w + 8
    desc = "".join(f'<text x="28" y="{90 + i * 23}" class="desc">{escape(l)}</text>' for i, l in enumerate(p["desc"]))
    if info:
        lang = info.get("primaryLanguage") or {}
        hist = ((info.get("defaultBranchRef") or {}).get("target") or {})
        commits = (hist.get("history") or {}).get("totalCount")
        facts = (f'<circle cx="34" cy="{196}" r="6" fill="{lang.get("color") or "#8B949E"}"/>'
                 f'<text x="46" y="201" class="fact">{escape(lang.get("name") or "—")}  ·  {commits or 0} commits  ·  updated {ago(info["pushedAt"], now)}</text>')
        prs = info["pullRequests"]["nodes"]
        if prs:
            facts += f'<text x="28" y="226" class="fact2">↳ latest PR #{prs[0]["number"]}: {escape(clip(prs[0]["title"], 52))}</text>'
        else:
            facts += f'<text x="28" y="226" class="fact2">↳ last commit {ago(hist.get("committedDate"), now)}</text>'
    else:
        facts = (f'<circle cx="34" cy="196" r="6" fill="#3572A5"/><text x="46" y="201" class="fact">Private repo · in active development</text>'
                 f'<text x="28" y="226" class="fact2">↳ demo / paper trading only, not financial advice</text>')
    title = p["repo"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="250" viewBox="0 0 600 250" role="img" aria-label="{escape(title)}: {escape(" ".join(p["desc"]))}">
  <defs>
    <linearGradient id="b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6366F1"/><stop offset="1" stop-color="#06B6D4"/></linearGradient>
    <radialGradient id="glow" cx="1" cy="0" r="0.9"><stop offset="0" stop-color="#6366F1" stop-opacity="{c["glow"]}"/><stop offset="1" stop-color="#6366F1" stop-opacity="0"/></radialGradient>
  </defs>
  <style>
    .t {{ font: 700 25px {FONT}; fill: {c["title"]}; }}
    .desc {{ font: 17px {FONT}; fill: {c["text"]}; }}
    .chip {{ font: 600 14px {FONT}; fill: {c["text"]}; }}
    .st {{ font: 700 12px {FONT}; fill: {stext}; letter-spacing: .5px; }}
    .fact {{ font: 600 14px {FONT}; fill: {c["title"]}; }}
    .fact2 {{ font: 14px {FONT}; fill: {c["text"]}; }}
  </style>
  <rect x="1" y="1" width="598" height="248" rx="18" fill="{c["bg"]}" stroke="{c["border"]}"/>
  <rect x="1" y="1" width="598" height="248" rx="18" fill="url(#glow)"/>
  <rect x="1" y="1" width="5" height="248" rx="2.5" fill="url(#b)"/>
  <text x="28" y="52" font-size="26" font-family="{FONT}">{p["emoji"]}</text>
  <text x="66" y="52" class="t">{escape(title)}</text>
  <rect x="{572 - sw:.0f}" y="29" width="{sw:.0f}" height="26" rx="13" fill="{sfill}"/>
  <text x="{572 - sw / 2:.0f}" y="46" text-anchor="middle" class="st">{escape(status)}</text>
  {desc}
  {"".join(chips)}
  <line x1="28" y1="176" x2="572" y2="176" stroke="{c["border"]}"/>
  {facts}
</svg>
'''


# ---------- README sections ----------
def section_now(u: dict, now: datetime) -> str:
    rows, private = [], 0
    for item in u["contributionsCollection"]["commitContributionsByRepository"]:
        r, n = item["repository"], item["contributions"]["totalCount"]
        if r["name"].lower() == u["login"].lower():
            continue
        if r["isPrivate"]:
            private += n
            continue
        if (now - parse(r["pushedAt"])).days > 45:
            continue
        lang = (r.get("primaryLanguage") or {}).get("name")
        rows.append(f'- 🔨 [**{r["name"]}**]({r["url"]}){f" · {lang}" if lang else ""}: {n} commits in the last year, last push {ago(r["pushedAt"], now)}')
        if len(rows) == 4:
            break
    private += u["contributionsCollection"]["restrictedContributionsCount"]
    if private:
        rows.append(f"- 🔒 plus {private} contributions to private projects (incl. the in-progress trading bots)")
    return "\n".join(rows) or "- 🌱 Quiet week. Planning the next build."


def section_shipped(prs: list, now: datetime) -> str:
    rows = []
    for p in prs:
        if not p or p["repository"]["isPrivate"] or p["repository"]["name"].lower() == "hammadiqbal6":
            continue
        rows.append(f'- ✅ [{escape(clip(p["title"], 70))}]({p["url"]}) · `{p["repository"]["name"]}` · {ago(p["mergedAt"], now)}')
        if len(rows) == 5:
            break
    return "\n".join(rows) or "- Nothing merged recently."


def replace_section(text: str, key: str, body: str) -> str:
    pat = re.compile(rf"(<!--START_{key}-->)(.*?)(<!--END_{key}-->)", re.S)
    return pat.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(3)}", text)


def main() -> None:
    login, out = sys.argv[1], Path(sys.argv[2])
    readme = Path(sys.argv[sys.argv.index("--readme") + 1]) if "--readme" in sys.argv else None
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now(PKT)
    frm = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    u = gql(Q_USER, login=login, **{"from": frm})["user"]
    repos = [r for r in u["repositories"]["nodes"] if r["name"].lower() != login.lower()]
    by_name = {r["name"]: r for r in repos}
    prs = gql(Q_SHIPPED, q=f"is:pr is:merged is:public user:{login} sort:updated-desc")["search"]["nodes"]
    prs.sort(key=lambda p: (p or {}).get("mergedAt") or "", reverse=True)

    for th, c in THEMES.items():
        (out / f"stats-overview-{th}.svg").write_text(overview(u, repos, c), encoding="utf-8")
        (out / f"stats-languages-{th}.svg").write_text(languages(repos, c, now), encoding="utf-8")
        (out / f"activity-{th}.svg").write_text(activity(u, c, now), encoding="utf-8")
        (out / f"tip-{th}.svg").write_text(tip(c, now), encoding="utf-8")
        (out / f"updated-{th}.svg").write_text(updated(c, now), encoding="utf-8")
        for p in PROJECTS:
            info = None if p.get("private") else by_name.get(p["repo"])
            (out / f"card-{p['repo']}-{th}.svg").write_text(project_card(p, info, c, th, now), encoding="utf-8")

    if readme:
        text = readme.read_text(encoding="utf-8")
        new = replace_section(text, "NOW", section_now(u, now))
        new = replace_section(new, "SHIPPED", section_shipped(prs, now))
        if new != text:
            readme.write_text(new, encoding="utf-8")
            print("README sections updated")
    print("assets written to", out)


if __name__ == "__main__":
    main()
