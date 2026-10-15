# How the profile cards are made

`build.py` reads `profile.toml` and the public GitHub data for Faaz17, then
writes every SVG in `assets/`. The workflow in `.github/workflows/cards.yml`
runs it every morning at 07:23 Dubai time, and again whenever `profile.toml`,
the generator or the fonts change, then commits any card that came out
different.

## Two layouts of every card

Each card is drawn twice: `<name>.svg` for desktop and `<name>-mobile.svg` for
phones. On a phone GitHub narrows the README to about 300px, which shrinks a
desktop card's text to a few pixels, so the phone layouts stack everything at
full width with bigger type.

The root `README.md` chooses between them with `<picture>` and a width media
query:

```html
<picture>
  <source media="(max-width: 600px)" srcset="https://raw.githubusercontent.com/Faaz17/Faaz17/main/assets/hero-mobile.svg">
  <img src="assets/hero.svg" width="100%" alt="...">
</picture>
```

The phone source uses the full raw URL on purpose. GitHub rewrites a relative
`<img src>` to point into the repo, but nothing confirms it does the same for
`srcset`, and a relative `srcset` would otherwise resolve against
github.com/Faaz17 and 404.

## The working oscilloscope

`scope/index.html` is a real, operable oscilloscope of the same data, published
with GitHub Pages at https://faaz17.github.io/Faaz17/scope/. The scope card in
the README links to it, because a README image cannot run code: GitHub strips
scripts from it, so the card can animate but never respond to a click.

The page reads `scope/data.json`, one sample per day, which `build.py` writes
and the workflow commits with the cards. It is one self-contained file, CSS and
JavaScript included, and loads its fonts from `assets/fonts`. Controls: TIME/DIV
and POSITION (zoom and move through the year), VOLTS/DIV and POSITION per
channel, TRIG LEVEL, RUN/STOP, AUTOSET, CURSORS, and WEEKLY SUM or DAILY
acquisition. The screen itself pans when dragged, zooms on scroll and reads out
any day on hover or tap.

`.nojekyll` stops Pages from running Jekyll over the repo, and the root
`index.html` forwards to the scope.

## Changing what the cards say

Edit `profile.toml`. It holds the hero lines, the toolchain chips, the career
timeline and the papers and awards (both taken from the CV), the featured
projects with their signal-flow diagrams, and the connector badges. Push, and
the cards redraw within a couple of minutes.

A project shows up in two places: its entry in `profile.toml` draws both of its
cards, and its block in the root `README.md` links them. Add or remove both
together. The build prints a note if the README is missing a card, and deletes
any SVG it no longer draws.

The build also stops, and says which one, if a blurb runs past four lines, a
diagram label or note does not fit its block, or a chip name does not fit its
chip.

## Running it locally

```bash
pip install -r generator/requirements.txt
GITHUB_TOKEN=$(gh auth token) python generator/build.py    # Git Bash
python generator/build.py --offline                        # redraw from the last fetch
```

In PowerShell, set the token with `$env:GITHUB_TOKEN = gh auth token` first.

A local run reads the same public data as the workflow, but its contribution
numbers can differ slightly. With your own token, GitHub dates the calendar in
your time zone, while the workflow gets UTC days, so late-evening runs can shift
every rolling week by a day. The workflow's numbers are the ones that count: it
runs at 07:23 Dubai time, when both calendars agree on the date.

## Rules that hold the design together

- Every colour comes from `P` at the top of `parts.py`. The boards are green,
  exposed metal (pads, pins, mounting rings, edge fingers) is gold, component
  bodies are steel, tan or cream, and amber is kept for the scope's second
  channel and the TX/RX LEDs. Change the palette there, not card by card.
- Text is drawn as glyph outlines from the fonts in `assets/fonts`: Michroma
  for names and headings, IBM Plex Mono for labels and numbers, and IBM Plex
  Sans Condensed for running text. Do not swap this for SVG `<text>`. The
  viewer's own fonts would replace these, and the layout, which measures every
  string, would break.
- With animation off, every card still has to be complete. That is why the
  scope traces are visible by default and only animate in, the signal pulses on
  the hero and the diagrams are hidden by default, the TX/RX LEDs simply stay
  lit, and the scope's beam starts hidden.
- Browsers pause animations in images that are off screen, so the scope draws
  its trace when a visitor scrolls to it. A full-page screenshot therefore
  shows the scope without its trace; scroll it into view before judging it.
- Never edit `assets/*.svg` by hand. The next run overwrites them.

## Files

| File | What it does |
|---|---|
| `build.py` | Entry point: fetch, draw both layouts of every card, write, tidy up |
| `ghdata.py` | The single GraphQL query and the numbers derived from it |
| `parts.py` | Palette, board, copper, chips, edge connector, the SVG wrapper |
| `hero.py` | The main board: name, role, focus areas, the chip |
| `cv.py` | The career timeline (a logic analyser) and the papers and awards board |
| `matrix.py` | The contribution calendar as an LED dot matrix, lit at GitHub's own levels |
| `scope.py` | The oscilloscope of weekly contributions |
| `bench.py` | Languages as LED bar graphs and the toolchain as chips |
| `modules.py` | Project modules with their signal-flow diagrams, and connector badges |
| `typeset.py` | Shapes text with HarfBuzz and turns it into glyph outlines |

The fonts are under the SIL Open Font License. Their license files sit next to
them in `assets/fonts`.
