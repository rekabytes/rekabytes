"""Generate the profile activity SVG using the workflow's GitHub token."""

import datetime as dt
import html
import json
import pathlib
import subprocess

QUERY = """query {
  user(login: "rekabytes") {
    contributionsCollection {
      startedAt endedAt
      totalCommitContributions totalIssueContributions
      totalPullRequestContributions totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays {
          contributionCount contributionLevel date weekday
        } }
      }
    }
  }
}"""


def render(collection):
    calendar = collection["contributionCalendar"]
    colors = {
        "NONE": "#24352e",
        "FIRST_QUARTILE": "#365d2c",
        "SECOND_QUARTILE": "#5a8e32",
        "THIRD_QUARTILE": "#86bd3c",
        "FOURTH_QUARTILE": "#b1ff47",
    }
    end = dt.datetime.fromisoformat(collection["endedAt"].replace("Z", "+00:00"))
    start = dt.datetime.fromisoformat(collection["startedAt"].replace("Z", "+00:00"))
    total = calendar["totalContributions"]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="420" viewBox="0 0 1200 420" role="img" aria-labelledby="title desc">',
        '<title id="title">GitHub activity overview</title>',
        f'<desc id="desc">{total:,} contributions from {start:%d %b %Y} to {end:%d %b %Y}. Daily heatmap, commit, pull request, issue, and review counts.</desc>',
        '<rect x="1" y="1" width="1198" height="418" rx="16" fill="#101b19" stroke="#34443d"/>',
        '<g font-family="Arial, Helvetica, sans-serif">',
        '<text x="36" y="44" fill="#8faaa0" font-size="13" letter-spacing="1.6">GITHUB / ACTIVITY OVERVIEW</text>',
        f'<text x="36" y="87" fill="#f0ecdf" font-size="28" font-weight="700">{total:,} contributions in the past year</text>',
        f'<text x="1164" y="43" text-anchor="end" fill="#8faaa0" font-size="12">UPDATED {end:%d %b %Y}</text>',
    ]
    month = None
    for week_index, week in enumerate(calendar["weeks"]):
        x = 66 + week_index * 20
        first = dt.date.fromisoformat(week["contributionDays"][0]["date"])
        if first.month != month:
            if week_index < len(calendar["weeks"]) - 2:
                parts.append(f'<text x="{x}" y="123" fill="#8faaa0" font-size="12">{first:%b}</text>')
            month = first.month
        for day in week["contributionDays"]:
            y = 138 + day["weekday"] * 20
            count = day["contributionCount"]
            label = html.escape(f'{day["date"]}: {count} contributions')
            parts.append(f'<rect x="{x}" y="{y}" width="16" height="16" rx="3" fill="{colors[day["contributionLevel"]]}"><title>{label}</title></rect>')
    for label, weekday in [("Mon", 1), ("Wed", 3), ("Fri", 5)]:
        parts.append(f'<text x="34" y="{150 + weekday * 20}" fill="#8faaa0" font-size="11">{label}</text>')
    parts.append('<text x="66" y="302" fill="#8faaa0" font-size="12">Less</text>')
    for i, color in enumerate(colors.values()):
        parts.append(f'<rect x="{106+i*22}" y="289" width="16" height="16" rx="3" fill="{color}"/>')
    parts.append('<text x="222" y="302" fill="#8faaa0" font-size="12">More</text>')
    parts.append('<path d="M36 325H1164" stroke="#34443d"/>')
    stats = [
        ("COMMITS", collection["totalCommitContributions"]),
        ("PULL REQUESTS", collection["totalPullRequestContributions"]),
        ("ISSUES", collection["totalIssueContributions"]),
        ("REVIEWS", collection["totalPullRequestReviewContributions"]),
    ]
    for i, (label, value) in enumerate(stats):
        x = 66 + i * 280
        parts.append(f'<text x="{x}" y="365" fill="#b1ff47" font-size="28" font-weight="700">{value:,}</text>')
        parts.append(f'<text x="{x}" y="389" fill="#8faaa0" font-size="12" letter-spacing="1">{label}</text>')
    parts.append('</g></svg>')
    return "\n".join(parts) + "\n"


def main():
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", "query=" + QUERY],
        check=True, capture_output=True, text=True,
    )
    data = json.loads(result.stdout)
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    collection = data["data"]["user"]["contributionsCollection"]
    output = pathlib.Path(__file__).resolve().parents[1] / "assets" / "activity.svg"
    output.write_text(render(collection), encoding="utf-8")
    print("Updated assets/activity.svg")


if __name__ == "__main__":
    main()
