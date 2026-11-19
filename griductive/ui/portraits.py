"""Load the desktop pixel sprite atlases."""
import json
from functools import lru_cache
from pathlib import Path
PORTRAIT_COUNT = 25


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
    atlas_path = Path(asset_dir).parent / 'public/pixel/sprites.png'
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
    sil_path = Path(asset_dir).parent / 'public/pixel/sprites-muted.png'
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
