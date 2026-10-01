"""Render dark.svg and light.svg for the profile README.

Profile content lives in PROFILE below. GitHub stats are fetched live from the
GraphQL API (needs GITHUB_TOKEN or GH_TOKEN), so the daily workflow keeps them
current. Run locally with:  GH_TOKEN=$(gh auth token) python build.py
"""
import datetime as dt
import json
import os
import urllib.request
from html import escape
from pathlib import Path

LOGIN = "7mxd"
ROOT = Path(__file__).parent
WIDTH = 60  # characters per info line, after the leading ". "

PROFILE = [
    ("Subject", "Ahmed Alawi Radhi"),
    ("Role", "Full Stack Developer (Freelance)"),
    ("Org", "Join Future W.L.L."),
    ("Prev", "Data Science Graduate Trainee @ Saal.ai"),
    ("Origin", "Abu Dhabi, UAE"),
    ("ToolChain", "Claude Code, VS Code, Jupyter, Postman"),
    None,
    ("Lang.Core", "Python, TypeScript, Dart, R, MATLAB, Java"),
    ("Lang.Libs", "Pandas, NumPy, scikit-learn, TensorFlow"),
    ("Dev.Stack", "NestJS, React, Flutter"),
    ("Data.Store", "PostgreSQL, MongoDB, Azure Blob, Docker"),
    ("Data.Viz", "Power BI, Tableau, Dataiku, Matplotlib"),
    None,
    "Contact",
    ("Grid.Mail", "AhmedARadhi00@gmail.com"),
    ("Grid.Portfolio", "7mxd.me"),
    ("Grid.LinkedIn", "linkedin.com/in/ahmedaradhi"),
    ("Grid.Github", "github.com/7mxd"),
    None,
    "GitHub Stats",
    "STATS",
    None,
    ("Degree", "BSc Applied Mathematics & Statistics"),
    ("Alma Mater", "Khalifa University"),
]
TAGLINE = "// Turning data into decisions."

THEMES = {
    "dark": dict(bg="black", text="#dbeafe", accent="#7DF9FF", key="#5EEAD4",
                 value="#E5E7EB", cc="#5f6b7a", section="#FF5F87", ascii="#7DF9FF"),
    "light": dict(bg="#f6f8fa", text="#24292f", accent="#0969da", key="#0969da",
                  value="#24292f", cc="#6e7781", section="#cf222e", ascii="#000000"),
}


def graphql(query, **variables):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("Set GITHUB_TOKEN or GH_TOKEN")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": LOGIN},
    )
    with urllib.request.urlopen(req) as resp:
        body = json.load(resp)
    if "errors" in body:
        raise SystemExit(f"GraphQL error: {body['errors']}")
    return body["data"]["user"]


def fetch_stats():
    user = graphql("""
    query($login: String!) { user(login: $login) {
      createdAt
      followers { totalCount }
      following { totalCount }
      repositories(ownerAffiliations: OWNER, privacy: PUBLIC) { totalCount }
      repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) { totalCount }
      contributionsCollection { contributionCalendar { totalContributions } }
    } }""", login=LOGIN)

    # contributionsCollection spans at most one year, so sum year by year.
    total = 0
    start = dt.datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
    now = dt.datetime.now(dt.timezone.utc)
    for year in range(start.year, now.year + 1):
        frm = max(start, dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc))
        to = min(now, dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc))
        year_data = graphql("""
        query($login: String!, $from: DateTime!, $to: DateTime!) { user(login: $login) {
          contributionsCollection(from: $from, to: $to) { contributionCalendar { totalContributions } }
        } }""", login=LOGIN, **{"from": frm.isoformat(), "to": to.isoformat()})
        total += year_data["contributionsCollection"]["contributionCalendar"]["totalContributions"]

    return {
        "repos": user["repositories"]["totalCount"],
        "contributed": user["repositoriesContributedTo"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "following": user["following"]["totalCount"],
        "year": user["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "total": total,
    }


def field(key, value, width):
    """`key: ..... value` padded with dots to exactly `width` characters."""
    value = str(value)
    dots = "." * max(1, width - len(key) - len(value) - 3)
    parts = []
    for i, k in enumerate(key.split(".")):
        if i:
            parts.append(".")
        parts.append(f'<tspan class="key">{escape(k)}</tspan>')
    return (f'{"".join(parts)}:<tspan class="cc"> {dots} </tspan>'
            f'<tspan class="value">{escape(value)}</tspan>')


def row(*fields):
    """Several fields on one line, separated by ` | `, totalling WIDTH chars."""
    sep_total = 3 * (len(fields) - 1)
    widths = [w for _, _, w in fields]
    widths[-1] = WIDTH - sep_total - sum(widths[:-1])
    return " | ".join(field(k, v, w) for (k, v, _), w in zip(fields, widths))


def render(theme, stats):
    t = THEMES[theme]
    stat_rows = [
        row(("Repos", stats["repos"], 14), ("Contributed", stats["contributed"], 20),
            ("Followers", stats["followers"], 0)),
        row(("Contributions", f'{stats["year"]:,} (past year)', 36),
            ("All-time", f'{stats["total"]:,}', 0)),
    ]

    lines = []
    for item in PROFILE:
        if item is None:
            lines.append('<tspan class="cc">. </tspan>')
        elif item == "STATS":
            lines.extend(f'<tspan class="cc">. </tspan>{r}' for r in stat_rows)
        elif isinstance(item, str):
            rule = "—" * (WIDTH - len(item) - 5)
            lines.append(f'<tspan fill="{t["section"]}">- {escape(item)}</tspan> -{rule}-—-')
        else:
            lines.append(f'<tspan class="cc">. </tspan>{field(*item, WIDTH)}')
    lines.append(f'<tspan class="cc">  </tspan><tspan fill="{t["cc"]}" font-size="12px">'
                 f'{escape(TAGLINE)}</tspan>')

    step, top = 20, 30
    height = top + step * (len(lines) + 1)
    info = [f'<tspan x="520" y="{top}" fill="{t["accent"]}" font-size="17px">'
            f'{LOGIN}@data-terminal</tspan> -{"—" * 36}-—-']
    info += [f'<tspan x="520" y="{top + step * (i + 1)}">{ln}</tspan>' for i, ln in enumerate(lines)]

    portrait = (ROOT / "assets" / "portrait.txt").read_text(encoding="utf-8").splitlines()
    art_top = (height / 0.88 - 9 * len(portrait)) / 2 - 10
    art = [f'<tspan x="-10" y="{art_top + 9 * i:.0f}">{escape(ln)}</tspan>'
           for i, ln in enumerate(portrait)]

    nl = "\n"
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="1180px" height="{height}px" font-size="15px">
<style>
@font-face {{
src: local('Consolas'), local('Consolas Bold');
font-family: 'ConsolasFallback';
font-display: swap;
-webkit-size-adjust: 109%;
size-adjust: 109%;
}}
.key {{fill: {t["key"]};}}
.value {{fill: {t["value"]};}}
.cc {{fill: {t["cc"]};}}
text, tspan {{white-space: pre;}}
</style>
<rect width="1180px" height="{height}px" fill="{t["bg"]}" rx="15"/>
<g transform="translate(22,20) scale(0.40,0.88)">
<text x="0" y="0" fill="{t["ascii"]}" class="ascii">
{nl.join(art)}
</text>
</g>
<text x="500" y="{top}" fill="{t["text"]}">
{nl.join(info)}
</text>
</svg>
"""


def main():
    stats = fetch_stats()
    print(json.dumps(stats))
    for theme in THEMES:
        (ROOT / f"{theme}.svg").write_text(render(theme, stats), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
