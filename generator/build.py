"""Draw the profile cards into assets/.

    python generator/build.py            fetch from GitHub, then draw
    python generator/build.py --offline  redraw from the last fetch (generator/.cache.json)

A fetch needs GITHUB_TOKEN. Any token works because everything read is
public, so the token the Action gets for free is enough. Locally:

    GITHUB_TOKEN=$(gh auth token) python generator/build.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib
from pathlib import Path

import cards
import ghdata
from typeset import Face

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CACHE = Path(__file__).resolve().parent / ".cache.json"

FONTS = {
    "display": "Michroma-Regular.ttf",          # names and headings, used sparingly
    "mono": "IBMPlexMono-Regular.ttf",          # labels, data
    "mono_md": "IBMPlexMono-Medium.ttf",
    "mono_sb": "IBMPlexMono-SemiBold.ttf",
    "sans": "IBMPlexSansCondensed-Regular.ttf",  # running text
    "sans_md": "IBMPlexSansCondensed-Medium.ttf",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Draw the profile cards into assets/.")
    parser.add_argument("--offline", action="store_true", help="redraw from the last fetch")
    args = parser.parse_args()

    cfg = tomllib.loads((ROOT / "profile.toml").read_text(encoding="utf-8"))
    if args.offline:
        user = json.loads(CACHE.read_text(encoding="utf-8"))
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            sys.exit("GITHUB_TOKEN is not set. Locally: GITHUB_TOKEN=$(gh auth token) python generator/build.py")
        user = ghdata.fetch(cfg["login"], token)
        CACHE.write_text(json.dumps(user, indent=1), encoding="utf-8")

    F = {role: Face(key, ASSETS / "fonts" / name) for key, (role, name) in zip("abcdef", FONTS.items())}
    act = ghdata.activity(user)
    lang = cfg["languages"]
    langs = ghdata.languages(user, lang["exclude_repos"], lang["exclude_languages"], lang["rows"])

    out = {
        "hero.svg": cards.hero(F, cfg["hero"], act.today),
        "activity.svg": cards.activity_card(F, act),
        "languages.svg": cards.languages_card(F, langs),
        "toolchain.svg": cards.toolchain_card(F, cfg["toolchain"]["parts"]),
    }
    for proj in cfg["projects"]:
        repo = ghdata.repo(user, proj["repo"])
        out[f"project-{proj['repo'].lower()}.svg"] = cards.project_card(F, proj, repo, lang["exclude_languages"])
    for link in cfg["links"]:
        out[f"link-{link['label'].lower()}.svg"] = cards.link_badge(F, link["label"], link["handle"])

    changed = 0
    for name, svg in out.items():
        path = ASSETS / name
        if not path.exists() or path.read_text(encoding="utf-8") != svg:
            path.write_text(svg, encoding="utf-8", newline="\n")
            changed += 1
    # A project or link taken out of profile.toml takes its card with it.
    for stale in [*ASSETS.glob("project-*.svg"), *ASSETS.glob("link-*.svg")]:
        if stale.name not in out:
            stale.unlink()
            print(f"removed {stale.name}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for name in out:
        if f"assets/{name}" not in readme:
            print(f"note: README.md does not show assets/{name}")
    print(f"{len(out)} cards drawn, {changed} changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
