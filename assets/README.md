# Game artwork

The desktop uses the 25 characters in `characters/characters.json`. The pixel
atlas in `characters/pixel/sprites.png` has seven 256×256 frames per character.
`sprites.json` gives the frame order and `sprites-muted.png` contains the two
unrevealed poses. Each character uses the same scale across poses.

`scenery/harbor.png` is the desktop background. `scenery/catalog.json` maps the
25 professions to tiles in `../public/images/pixel-profession-props.png`.
`ui/glyphs.png` contains the desktop glyph masks, in the order listed in
`griductive/ui/icons.py`. The settings gear has its own 24×24 image.

The web app serves its portrait, silhouette, profession and backdrop SVGs from
`../public/images/`. Artwork provenance is in `../docs/AI-PROMPTS.md`.
