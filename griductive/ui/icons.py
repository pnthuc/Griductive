"""Tint static desktop glyphs at the requested device scale."""
from functools import lru_cache

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap

from .assets import ROOT


GLYPHS = ('check', 'cross', 'hint', 'warning', 'step', 'export', 'pause', 'play', 'restart', 'chevron')


@lru_cache(maxsize=1)
def _atlas():
    return QPixmap(str(ROOT / 'assets/ui/glyphs.png'))


@lru_cache(maxsize=128)
def icon(name, color):
    tile = _atlas().copy(16 * GLYPHS.index(name), 0, 16, 16)
    painter = QPainter(tile)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(tile.rect(), QColor(color))
    painter.end()
    result = QIcon()
    for size in (16, 24, 32, 64, 128):
        scaled = tile.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
        result.addPixmap(scaled)
        result.addPixmap(scaled, QIcon.Mode.Disabled)
    return result
