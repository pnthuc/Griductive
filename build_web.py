"""Prepare existing artwork for Vercel's static CDN; no artwork generation."""
from pathlib import Path
from shutil import copy2

ROOT = Path(__file__).resolve().parent


def main():
    destination = ROOT / 'public' / 'images'
    destination.mkdir(parents=True, exist_ok=True)
    for source in ('assets/characters/pixel/sprites.png',
                   'assets/scenery/pixel-desk.png',
                   'assets/scenery/pixel-profession-props.png'):
        copy2(ROOT / source, destination / Path(source).name)
    print('Prepared 3 existing artwork files for the static CDN.')


if __name__ == '__main__':
    main()
