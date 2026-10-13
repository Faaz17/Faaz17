# Faaz17 profile repo

This repository is my GitHub profile. `README.md` is what visitors see on
github.com/Faaz17, so treat it as a public page, not as documentation.

The cards in `assets/` are generated. Read `generator/README.md` before
changing anything visual: it covers how the cards are built, how to run the
generator, and the rules that hold the design together (green-only palette from
`P` in `generator/parts.py`, text drawn as glyph outlines, every card complete
with animation off, and a phone layout for every card).

- Change content in `profile.toml`, never in the generated SVGs.
- After a change, run `python generator/build.py --offline` and look at the
  result before pushing.
- Prose on the profile: plain and specific, no em dashes.
- Nothing private goes on this page: no private repo names or links, no email
  addresses, and no one else's personal details.
