"""Desktop assets."""
import json
from functools import lru_cache
from pathlib import Path
from PySide6.QtGui import QPixmap

ROOT=Path(__file__).resolve().parents[2]


SCENERY=ROOT/'assets/scenery'
IMAGES=ROOT/'public/images'


@lru_cache(maxsize=1)
def scenery_catalog():
    return json.loads((SCENERY/'catalog.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=8)
def scenery_image(filename):
    image=QPixmap(str(IMAGES/filename))
    if image.isNull():
        raise RuntimeError(f'Thiếu ảnh giao diện: {filename}')
    return image

