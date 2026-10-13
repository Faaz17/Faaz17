"""Everything the cards show, from one GitHub GraphQL call.

Only public data is read (repositories are queried with privacy: PUBLIC), so a
local run with a personal token draws the same cards as the daily Action run
with its built-in token. The contribution calendar includes private work as
an anonymous count only when the profile setting "Include private
contributions" is on, which is how the public profile graph counts it too.
"""
from __future__ import annotations

import json
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import date

QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    name
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name
        description
        url
        stargazerCount
        isArchived
        pushedAt
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""

MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def fetch(login: str, token: str) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{login}-profile-cards",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError("GitHub API: " + "; ".join(e.get("message", "?") for e in payload["errors"]))
    user = payload["data"]["user"]
    if user is None:
        raise RuntimeError(f"GitHub API: no user called {login!r}")
    return user


@dataclass
class Activity:
    total: int               # contributions in the last year, as the profile graph counts them
    weeks: list[int]         # 52 seven-day totals, oldest first; the last one ends on `today`
    week_starts: list[date]
    days: list[date]         # the 364 days behind `weeks`, for placing month labels
    today: date
    peak: int
    peak_start: date
    active_days: int         # days with at least one contribution, out of the last 365
    longest_streak: int


def activity(user: dict) -> Activity:
    calendar = user["contributionsCollection"]["contributionCalendar"]
    days = sorted(
        (date.fromisoformat(d["date"]), d["contributionCount"])
        for week in calendar["weeks"]
        for d in week["contributionDays"]
    )
    # Rolling seven-day windows ending today, rather than calendar weeks, so the
    # newest point is a full week and the chart does not dip at its right edge.
    window = days[-364:]
    window = [(None, 0)] * (364 - len(window)) + window  # a young account has less than a year
    weeks = [sum(c for _, c in window[i:i + 7]) for i in range(0, 364, 7)]
    starts = [window[i][0] or window[-1][0] for i in range(0, 364, 7)]
    peak_index = max(range(len(weeks)), key=lambda i: (weeks[i], i))  # latest of any tie

    longest = run = 0
    for _, count in days:
        run = run + 1 if count else 0
        longest = max(longest, run)

    return Activity(
        total=calendar["totalContributions"],
        weeks=weeks,
        week_starts=starts,
        days=[d for d, _ in window],
        today=days[-1][0],
        peak=weeks[peak_index],
        peak_start=starts[peak_index],
        active_days=sum(1 for _, c in days[-365:] if c),
        longest_streak=longest,
    )


def languages(user: dict, exclude_repos: list[str], exclude_languages: list[str],
              rows: int) -> list[tuple[str, float]]:
    """Share of code by bytes across public repos, largest first, at most `rows` entries."""
    totals: Counter[str] = Counter()
    for repo in user["repositories"]["nodes"]:
        if repo["name"] in exclude_repos:
            continue
        for edge in repo["languages"]["edges"]:
            if edge["node"]["name"] not in exclude_languages:
                totals[edge["node"]["name"]] += edge["size"]
    grand = sum(totals.values())
    if not grand:
        return []
    ranked = [(name, size / grand) for name, size in totals.most_common()]
    if len(ranked) <= rows:
        return ranked
    return ranked[:rows - 1] + [("Other", sum(share for _, share in ranked[rows - 1:]))]


def repo(user: dict, name: str) -> dict:
    for node in user["repositories"]["nodes"]:
        if node["name"].lower() == name.lower():
            return node
    raise KeyError(f"{name!r} is not a public, non-fork repository of {user['login']}")


def month_label(d: date) -> str:
    return f"{MONTHS[d.month - 1]} {d.year}"
