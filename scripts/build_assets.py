#!/usr/bin/env python3
"""Build the static SVG assets for the profile README.

Run: python3 scripts/build_assets.py
Outputs to assets/ (header, section titles, divider, project cards in light & dark).
Edit PROJECTS / SECTIONS below and re-run to update.
"""
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "assets"
FONT = "Segoe UI, Ubuntu, Helvetica Neue, Arial, sans-serif"
MONO = "SFMono-Regular, Consolas, Liberation Mono, Menlo, monospace"
INDIGO, CYAN, VIOLET = "#6366F1", "#06B6D4", "#8B5CF6"

THEMES = {
    "light": dict(bg="#FFFFFF", bg2="#F6F8FA", border="#D0D7DE", title="#1F2328", text="#57606A",
                  chip="#EEF2FF", chipText="#4338CA", glow="0.10"),
    "dark": dict(bg="#161B22", bg2="#0D1117", border="#30363D", title="#F0F6FC", text="#9DA7B3",
                 chip="#1E2140", chipText="#A5B4FC", glow="0.22"),
}


def write(name: str, svg: str) -> None:
    path = A / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg.strip() + "\n", encoding="utf-8")


def header() -> str:
    lines = [
        ("$ whoami", "hammad iqbal"),
        ("$ cat role.txt", "Full-Stack &amp; CRM Developer"),
        ("$ ls stack/", "laravel  nextjs  react  react-native  node  mysql  mongodb"),
    ]
    rows, t = [], 0.4
    for i, (cmd, out) in enumerate(lines):
        y = 138 + i * 44
        rows.append(f'''
    <g>
      <text x="560" y="{y}" class="cmd">{cmd}</text>
      <text x="560" y="{y + 20}" class="out">{out}</text>
    </g>''')
        t += 0.9
    return f'''
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="320" viewBox="0 0 1200 320" role="img" aria-label="Hammad Iqbal, Full-Stack and CRM Developer">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#1E1B4B"/>
      <stop offset="0.55" stop-color="#312E81"/>
      <stop offset="1" stop-color="#0E7490"/>
    </linearGradient>
    <radialGradient id="o1" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{VIOLET}" stop-opacity="0.75"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>
    <radialGradient id="o2" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{CYAN}" stop-opacity="0.65"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>
    <linearGradient id="txt" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#A5F3FC"/></linearGradient>
    <clipPath id="clip"><rect width="1200" height="320" rx="24"/></clipPath>
  </defs>
  <style>
    .o {{ animation: drift 14s ease-in-out infinite alternate; }}
    .o2 {{ animation-duration: 18s; animation-direction: alternate-reverse; }}
    @keyframes drift {{ from {{ transform: translate(0,0); }} to {{ transform: translate(120px,40px); }} }}
    .cmd {{ font: 600 16px {MONO}; fill: #67E8F9; }}
    .out {{ font: 15px {MONO}; fill: #E2E8F0; }}
    .cur {{ animation: blink 1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .o, .cur {{ animation: none; opacity: 1; }} }}
  </style>
  <g clip-path="url(#clip)">
    <rect width="1200" height="320" fill="url(#bg)"/>
    <circle class="o" cx="180" cy="60" r="220" fill="url(#o1)"/>
    <circle class="o o2" cx="980" cy="300" r="260" fill="url(#o2)"/>
    <path d="M0 0H1200" stroke="#fff" stroke-opacity="0.08"/>
  </g>
  <text x="64" y="132" font-family="{FONT}" font-size="20" font-weight="600" fill="#C7D2FE" letter-spacing="3">HI, I'M</text>
  <text x="64" y="190" font-family="{FONT}" font-size="58" font-weight="800" fill="url(#txt)">Hammad Iqbal</text>
  <text x="64" y="232" font-family="{FONT}" font-size="22" font-weight="500" fill="#E0E7FF">Full-Stack &amp; CRM Developer</text>
  <text x="64" y="264" font-family="{FONT}" font-size="16" fill="#A5B4FC">Laravel · Next.js · React · Node · business automation</text>
  <!-- glass terminal -->
  <rect x="530" y="50" width="610" height="242" rx="16" fill="#0B1020" fill-opacity="0.55" stroke="#FFFFFF" stroke-opacity="0.18"/>
  <circle cx="556" cy="74" r="6" fill="#FF5F57"/><circle cx="576" cy="74" r="6" fill="#FEBC2E"/><circle cx="596" cy="74" r="6" fill="#28C840"/>
  <text x="835" y="79" text-anchor="middle" font-family="{MONO}" font-size="12" fill="#94A3B8">~/hammadiqbal6</text>
  <line x1="530" y1="94" x2="1140" y2="94" stroke="#FFFFFF" stroke-opacity="0.10"/>{"".join(rows)}
  <text x="560" y="272" class="cmd">$</text><rect class="cur" x="576" y="258" width="10" height="18" fill="#67E8F9" fill-opacity="0.9"/>
</svg>'''


def section(title: str, emoji: str) -> str:
    w = 60 + len(title) * 15
    return f'''
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="46" viewBox="0 0 {w} 46" role="img" aria-label="{escape(title)}">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{INDIGO}"/><stop offset="1" stop-color="#0891B2"/></linearGradient></defs>
  <text x="0" y="30" font-family="{FONT}" font-size="24">{emoji}</text>
  <text x="38" y="30" font-family="{FONT}" font-size="24" font-weight="700" fill="url(#g)">{escape(title)}</text>
  <rect x="38" y="39" width="{w - 38}" height="3" rx="1.5" fill="url(#g)" opacity="0.55"/>
</svg>'''


def divider() -> str:
    return f'''
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="24" viewBox="0 0 1200 24" role="img" aria-label="">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{INDIGO}" stop-opacity="0"/><stop offset="0.5" stop-color="{INDIGO}"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <style>.d {{ animation: pulse 4s ease-in-out infinite; transform-origin: 600px 12px; }} @keyframes pulse {{ 50% {{ transform: scaleX(0.7); opacity: .6; }} }} @media (prefers-reduced-motion: reduce) {{ .d {{ animation: none; }} }}</style>
  <rect class="d" x="100" y="11" width="1000" height="2" rx="1" fill="url(#g)"/>
  <circle cx="600" cy="12" r="4" fill="{CYAN}"/>
</svg>'''


PROJECTS = [
    # slug, emoji, title, one-liner (2 lines max), chips, status
    ("fullstack-crm", "🗂️", "fullstack-crm", ["Visa-agency CRM: lead approvals, onboarding,", "5-role RBAC, PDF invoices and documents"], ["Laravel", "Next.js", "TypeScript", "Docker"], "CRM"),
    ("bulk-excel", "📊", "bulk-excel", ["Bulk Excel import API for housing-scheme", "plot data, with a React upload UI"], ["Laravel", "Laravel Excel", "React", "Vite"], "Full-stack"),
    ("crypto-trading-bot", "🤖", "crypto-trading-bot", ["Trend-following + news-sentiment crypto bot,", "paper trading first"], ["Python", "freqtrade"], "In progress · private"),
    ("stock-trading-bot", "📈", "stock-trading-bot", ["Trend-following + news-sentiment stock bot,", "paper trading first"], ["Python", "Alpaca paper"], "In progress · private"),
    ("Promptopia", "💬", "Promptopia", ["Prompt-sharing web app with", "MongoDB persistence"], ["Next.js", "MongoDB", "Tailwind"], "Web app"),
    ("Donewithit", "📱", "Donewithit", ["Mobile marketplace app with an", "Express backend"], ["React Native", "Expo", "Express"], "Mobile"),
    ("Vanslife-next", "🚐", "Vanslife-next", ["Van-rental app with protected routes", "on the App Router"], ["Next.js", "React"], "Web app"),
    ("realtor-clone-react", "🏠", "realtor-clone-react", ["Realtor-style property listing", "clone"], ["React", "Tailwind"], "Web app"),
]


def card(p, theme: str) -> str:
    slug, emoji, title, desc, chips, status = p
    c = THEMES[theme]
    wip = status.startswith("In progress")
    sfill, stext = ("#FEF3C7", "#92400E") if wip and theme == "light" else ("#3B2F12", "#FCD34D") if wip else (c["chip"], c["chipText"])
    sw = 24 + len(status) * 8
    x, chip_svg = 28, []
    for ch in chips:
        w = 22 + len(ch) * 8.6
        chip_svg.append(f'<rect x="{x}" y="146" width="{w:.0f}" height="30" rx="15" fill="{c["bg2"]}" stroke="{c["border"]}"/>'
                        f'<text x="{x + w / 2:.0f}" y="166" text-anchor="middle" class="chip">{escape(ch)}</text>')
        x += w + 8
    d = "".join(f'<text x="28" y="{96 + i * 24}" class="desc">{escape(l)}</text>' for i, l in enumerate(desc))
    return f'''
<svg xmlns="http://www.w3.org/2000/svg" width="600" height="200" viewBox="0 0 600 200" role="img" aria-label="{escape(title)}: {escape(" ".join(desc))}">
  <defs>
    <linearGradient id="b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{INDIGO}"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>
    <radialGradient id="glow" cx="1" cy="0" r="0.9"><stop offset="0" stop-color="{INDIGO}" stop-opacity="{c["glow"]}"/><stop offset="1" stop-color="{INDIGO}" stop-opacity="0"/></radialGradient>
  </defs>
  <style>
    .t {{ font: 700 25px {FONT}; fill: {c["title"]}; }}
    .desc {{ font: 17px {FONT}; fill: {c["text"]}; }}
    .chip {{ font: 600 14px {FONT}; fill: {c["text"]}; }}
    .st {{ font: 700 12px {FONT}; fill: {stext}; letter-spacing: .5px; }}
  </style>
  <rect x="1" y="1" width="598" height="198" rx="18" fill="{c["bg"]}" stroke="{c["border"]}"/>
  <rect x="1" y="1" width="598" height="198" rx="18" fill="url(#glow)"/>
  <rect x="1" y="1" width="5" height="198" rx="2.5" fill="url(#b)"/>
  <text x="28" y="57" font-size="26" font-family="{FONT}">{emoji}</text>
  <text x="66" y="57" class="t">{escape(title)}</text>
  <rect x="{572 - sw:.0f}" y="34" width="{sw:.0f}" height="26" rx="13" fill="{sfill}"/>
  <text x="{572 - sw / 2:.0f}" y="51" text-anchor="middle" class="st">{escape(status.upper())}</text>
  {d}
  {"".join(chip_svg)}
</svg>'''


SECTIONS = [("about", "About me", "👋"), ("stack", "Tech stack", "🧰"), ("projects", "Featured projects", "🚀"), ("stats", "GitHub at a glance", "📊")]

if __name__ == "__main__":
    write("header.svg", header())
    write("divider.svg", divider())
    for slug, title, emoji in SECTIONS:
        write(f"sections/{slug}.svg", section(title, emoji))
    for p in PROJECTS:
        for th in THEMES:
            write(f"cards/{p[0]}-{th}.svg", card(p, th))
    print("assets built")
