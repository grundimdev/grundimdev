"""Builds assets/languages.svg from the language stats of all repos owned by the token's user."""
import json
import os
import sys
import urllib.request

TOKEN = os.environ.get("GH_TOKEN")
OUT = "assets/languages.svg"
TOP = 8

# Related languages are merged so the card stays readable.
GROUPS = {
    "Dart": "Dart / Flutter",
    "C#": "C# / Unity",
    "ShaderLab": "C# / Unity",
    "HLSL": "C# / Unity",
    "PLpgSQL": "SQL",
    "TSQL": "SQL",
}
IGNORE = {"Objective-C", "Swift", "CMake", "C++", "Batchfile", "Shell", "Dockerfile"}
COLORS = {
    "Dart / Flutter": "#00B4AB",
    "JavaScript": "#E8C547",
    "C# / Unity": "#2E9E3E",
    "HTML": "#E34C26",
    "CSS": "#663399",
    "Java": "#B07219",
    "TypeScript": "#3178C6",
    "SQL": "#336790",
    "Kotlin": "#A97BFF",
    "Python": "#3572A5",
}


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def repos():
    page = 1
    while True:
        batch = api(f"/user/repos?affiliation=owner&per_page=100&page={page}")
        if not batch:
            return
        yield from batch
        page += 1


def collect():
    totals = {}
    for repo in repos():
        if repo["fork"] or repo["name"] == repo["owner"]["login"]:
            continue
        for lang, size in api(f"/repos/{repo['full_name']}/languages").items():
            if lang in IGNORE:
                continue
            name = GROUPS.get(lang, lang)
            totals[name] = totals.get(name, 0) + size
    total = sum(totals.values())
    top = sorted(totals.items(), key=lambda kv: -kv[1])[:TOP]
    return [(name, 100 * size / total) for name, size in top]


def render(langs):
    W, top, rh, bx, bw = 495, 56, 30, 150, 270
    H = top + len(langs) * rh + 14
    rows = []
    for i, (n, p) in enumerate(langs):
        y, d = top + i * rh, 0.15 * i
        c = COLORS.get(n, "#8B949E")
        w = max(6, round(bw * p / langs[0][1]))
        rows.append(f'''  <g class="row" style="animation-delay:{d:.2f}s">
    <circle cx="28" cy="{y+9}" r="5" fill="{c}"/>
    <text x="42" y="{y+13}" class="name">{n}</text>
    <rect x="{bx}" y="{y+4}" width="{bw}" height="10" rx="5" class="track"/>
    <rect x="{bx}" y="{y+4}" width="{w}" height="10" rx="5" fill="{c}" class="bar" style="animation-delay:{d+0.2:.2f}s"/>
    <text x="{W-24}" y="{y+13}" class="pct" text-anchor="end">{p:.1f}%</text>
  </g>''')
    rows = "\n".join(rows)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Languages">
  <style>
    :root {{ --bg:#ffffff; --border:#e4e7eb; --fg:#1f2328; --muted:#656d76; --track:#eef1f4; }}
    @media (prefers-color-scheme: dark) {{
      :root {{ --bg:#0d1117; --border:#30363d; --fg:#e6edf3; --muted:#8b949e; --track:#161b22; }}
    }}
    text {{ font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; }}
    .card {{ fill:var(--bg); stroke:var(--border); }}
    .title {{ fill:var(--fg); font-size:16px; font-weight:600; }}
    .sub {{ fill:var(--muted); font-size:11px; }}
    .name {{ fill:var(--fg); font-size:12.5px; }}
    .pct {{ fill:var(--muted); font-size:12px; font-variant-numeric:tabular-nums; }}
    .track {{ fill:var(--track); }}
    .row {{ opacity:0; animation:fade .5s ease-out forwards; }}
    .bar {{ transform-box:fill-box; transform-origin:left center; transform:scaleX(0); animation:grow 1.1s cubic-bezier(.22,1,.36,1) forwards; }}
    @keyframes fade {{ from {{ opacity:0; transform:translateY(4px); }} to {{ opacity:1; transform:none; }} }}
    @keyframes grow {{ to {{ transform:scaleX(1); }} }}
    @media (prefers-reduced-motion: reduce) {{ .row,.bar {{ animation:none; opacity:1; transform:none; }} }}
  </style>
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" class="card"/>
  <text x="24" y="32" class="title">Languages</text>
  <text x="{W-24}" y="32" class="sub" text-anchor="end">across all my projects</text>
{rows}
</svg>
'''


if __name__ == "__main__":
    if not TOKEN:
        print("LANGUAGES_TOKEN secret is not set, keeping the current card.")
        sys.exit(0)
    with open(OUT, "w") as f:
        f.write(render(collect()))
