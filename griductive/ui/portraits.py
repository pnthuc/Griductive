"""Qt SVG renderers and validated legacy sprite frames."""
import json
from functools import lru_cache
from pathlib import Path
from ..vector_art import PORTRAIT_COUNT, portrait_svg, profession_svg

ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=128)
def portrait_svg_renderer(portrait: int, slot: int = 0, silhouette: bool = False):
    from PySide6.QtCore import QByteArray
    from PySide6.QtSvg import QSvgRenderer

    svg = portrait_svg(portrait, slot, silhouette)
    return QSvgRenderer(QByteArray(svg.encode('utf-8')))


@lru_cache(maxsize=1)
def backdrop_svg_renderer():
    from PySide6.QtSvg import QSvgRenderer

    return QSvgRenderer(str(ROOT / 'public/images/backdrop.svg'))


@lru_cache(maxsize=64)
def profession_renderer(category: str, color: str = '#BDD7F2'):
    from PySide6.QtCore import QByteArray
    from PySide6.QtSvg import QSvgRenderer

    return QSvgRenderer(QByteArray(profession_svg(category, color).encode('utf-8')))


def load_expression_frames(asset_dir):
    """Shared, validated Qt frame bank (25 characters x 7 slots of 256x256)."""
    return _cached_frames(str(asset_dir))


def load_silhouette_frames(asset_dir):
    """Shared ice-blue mystery silhouette frame bank (25 characters x 2 slots of 256x256)."""
    return _cached_silhouettes(str(asset_dir))


@lru_cache(maxsize=1)
def _cached_frames(asset_dir):
    from PySide6.QtGui import QPixmap

    root = Path(asset_dir) / 'characters' / 'pixel'
    manifest = json.loads((root / 'sprites.json').read_text(encoding='utf-8'))
    tile = manifest['tile_size']
    columns = len(manifest['slots'])
    atlas_path = Path(asset_dir).parent / 'public/images/sprites.png'
    if not atlas_path.is_file():
        atlas_path = root / 'sprites.png'
    atlas = QPixmap(str(atlas_path))
    if atlas.isNull() or atlas.width() != tile * columns or atlas.height() != tile * PORTRAIT_COUNT:
        raise ValueError('Invalid character sprite sheet dimensions')
    return {
        portrait: tuple(atlas.copy(col * tile, portrait * tile, tile, tile)
                        for col in range(columns))
        for portrait in range(PORTRAIT_COUNT)
    }


@lru_cache(maxsize=1)
def _cached_silhouettes(asset_dir):
    from PySide6.QtGui import QPixmap

    tile = 256
    sil_path = Path(asset_dir).parent / 'public/images/sprites-silhouette.png'
    atlas = QPixmap(str(sil_path))
    if atlas.isNull() or atlas.height() != tile * PORTRAIT_COUNT:
        frames = _cached_frames(asset_dir)
        return {p: (frames[p][0], frames[p][1]) for p in range(PORTRAIT_COUNT)}
    cols = max(1, atlas.width() // tile)
    return {
        portrait: tuple(atlas.copy(min(col, cols - 1) * tile, portrait * tile, tile, tile)
                        for col in range(2))
        for portrait in range(PORTRAIT_COUNT)
    }
