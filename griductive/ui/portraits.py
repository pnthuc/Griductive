"""Portrait atlas layout shared by validation and the Qt renderer."""
from functools import lru_cache

PORTRAIT_COUNT = 25


def load_expression_frames(asset_dir):
    """Shared, validated Qt frame bank. Called on the UI thread after QApplication."""
    return _cached_frames(str(asset_dir))


@lru_cache(maxsize=1)
def _cached_frames(asset_dir):
    import json
    from pathlib import Path
    from PySide6.QtGui import QPixmap

    root = Path(asset_dir) / 'characters' / 'pixel'
    manifest = json.loads((root / 'sprites.json').read_text(encoding='utf-8'))
    tile = manifest['tile_size']
    columns = len(manifest['slots'])
    atlas = QPixmap(str(root / 'sprites.png'))
    if atlas.isNull() or atlas.width() != tile * columns or atlas.height() != tile * PORTRAIT_COUNT:
        raise ValueError('Invalid character sprite sheet dimensions')
    return {
        portrait: tuple(atlas.copy(col * tile, portrait * tile, tile, tile)
                        for col in range(columns))
        for portrait in range(PORTRAIT_COUNT)
    }
