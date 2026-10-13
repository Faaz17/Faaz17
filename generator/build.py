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

import bench
import cv
import ghdata
import hero
import modules
import scope
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

    # Every card comes in two layouts: <name>.svg for desktop, <name>-mobile.svg for
    # phones. README.md picks between them with <picture> and a width media query.
    parts = cfg["toolchain"]["parts"]
    hide = lang["exclude_languages"]
    out = {
        "hero.svg": hero.hero_desktop(F, cfg["hero"], act.today),
        "hero-mobile.svg": hero.hero_mobile(F, cfg["hero"], act.today),
        "career.svg": cv.career_desktop(F, cfg["career"], act.today),
        "career-mobile.svg": cv.career_mobile(F, cfg["career"], act.today),
        "record.svg": cv.record_desktop(F, cfg["record"]),
        "record-mobile.svg": cv.record_mobile(F, cfg["record"]),
        "activity.svg": scope.activity_desktop(F, act),
        "activity-mobile.svg": scope.activity_mobile(F, act),
        "bench.svg": bench.bench_desktop(F, langs, parts),
        "bench-mobile.svg": bench.bench_mobile(F, langs, parts),
    }
    for proj in cfg["projects"]:
        repo = ghdata.repo(user, proj["repo"])
        slug = proj["repo"].lower()
        out[f"project-{slug}.svg"] = modules.project_desktop(F, proj, repo, hide)
        out[f"project-{slug}-mobile.svg"] = modules.project_mobile(F, proj, repo, hide)
    for link in cfg["links"]:
        out[f"link-{link['id']}.svg"] = modules.link_badge(F, link["label"], link["handle"])

    changed = 0
    for name, svg in out.items():
        path = ASSETS / name
        if not path.exists() or path.read_text(encoding="utf-8") != svg:
            path.write_text(svg, encoding="utf-8", newline="\n")
            changed += 1
    # A card that is no longer drawn (a project taken out of profile.toml, say) goes too.
    for stale in ASSETS.glob("*.svg"):
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
