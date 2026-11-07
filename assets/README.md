# Active pixel artwork

The shared roster is characters/characters.json.
../public/images/sprites.png contains 25 rows and seven 256x256 frames per row.
sprites.json describes frame order. The game loads this atlas directly.

scenery/catalog.json maps all 25 professions to the pixel background atlas.
Images in ../public/images are shared by desktop and web. pixel-desk.png is the
bright seaside background. Profession tiles use an ivory
backdrop. The 25 generated scenes were repacked to remove baked-in cell borders,
using uniform scaling to preserve the artwork proportions. Revealed clues are displayed directly on the card.

Generated sprite poses retain aspect ratio.
A single uniform scale is used per character when packing regenerated poses.
Prompts and provenance are in ../docs/AI-PROMPTS.md.
