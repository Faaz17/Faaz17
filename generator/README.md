# How the profile cards are made

`build.py` reads `profile.toml` and the public GitHub data for Faaz17, then
writes every SVG in `assets/`. The workflow in `.github/workflows/cards.yml` runs it every morning
at 07:23 Dubai time, and again whenever `profile.toml`, the generator or the
fonts change, then commits any card that came out different.

## Changing what the cards say

Edit `profile.toml`. It holds the hero lines, the toolchain chips, the featured
projects and the LinkedIn badge. Push, and the cards redraw within a couple of
minutes.

A project shows up in two places: its entry in `profile.toml` draws the card, and
its line in the root `README.md` links it. Add or remove both together. The build
prints a note if the README is missing a card, and deletes the SVG of any project
you take out of `profile.toml`.

Blurbs have to fit in three lines on the card. If one is too long, the build
stops and says which.

## Running it locally

```bash
pip install -r generator/requirements.txt
GITHUB_TOKEN=$(gh auth token) python generator/build.py    # Git Bash
python generator/build.py --offline                        # redraw from the last fetch
```

In PowerShell, set the token with `$env:GITHUB_TOKEN = gh auth token` first.

A local run reads the same public data as the workflow, so it draws the same
cards. The contribution total can still differ by a few, because a personal
token may see contributions that the public count leaves out.

## Rules that hold the design together

- Every colour comes from `P` at the top of `cards.py`, and all of them are
  greens. Change the palette there, not card by card.
- Text is drawn as glyph outlines from the fonts in `assets/fonts`: Michroma
  for names and headings, IBM Plex Mono for labels and numbers, and IBM Plex
  Sans Condensed for running text. Do not swap this for SVG `<text>`. The
  viewer's own fonts would replace these, and the layout, which measures every
  string, would break.
- With animation off, every card still has to be complete. That is why the
  scope trace is visible by default and only animates in, the signal pulses on
  the hero are hidden by default, and the scope's beam starts hidden.
- Never edit `assets/*.svg` by hand. The next run overwrites them.

## Files

| File | What it does |
|---|---|
| `build.py` | Entry point: fetch, draw, write, tidy up |
| `ghdata.py` | The single GraphQL query and the numbers derived from it |
| `cards.py` | Palette and every card's drawing |
| `typeset.py` | Shapes text with HarfBuzz and turns it into glyph outlines |

The fonts are under the SIL Open Font License. Their license files sit next to
them in `assets/fonts`.
