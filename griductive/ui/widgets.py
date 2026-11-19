"""Desktop widgets — Alto's Odyssey x Gamma 5 flat-vector landscape backdrop."""
import os
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QLinearGradient, QColor, QPainter, QFont, QFontDatabase, QPixmap
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QGraphicsOpacityEffect
from .assets import ROOT


def label(value='', name=None):
    w = QLabel(value)
    w.setWordWrap(True)
    w.setTextFormat(Qt.TextFormat.PlainText)
    if name:
        w.setObjectName(name)
    return w


def button(value, slot=None, primary=False):
    w = QPushButton(value)
    if primary:
        w.setObjectName('primary')
    if slot:
        w.clicked.connect(slot)
    return w


class SmoothPillLabel(QLabel):
    """True QPainter-antialiased capsule label (avoids Qt QSS faceted border-radius)."""

    def __init__(self, value='', name=None, *, bg=(255, 255, 255, 76), border=None, fg='#0D2744', radius=None, font_px=15):
        super().__init__(value)
        if name:
            self.setObjectName(name)
        self._bg = QColor(*bg)
        self._border = QColor(*border) if border else None
        self._fg = QColor(fg)
        self._radius = radius
        self._font_px = font_px
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        box = QRectF(self.rect()).adjusted(0.75, 0.75, -0.75, -0.75)
        r = (box.height() * 0.5) if self._radius is None else min(float(self._radius), box.height() * 0.5)
        p.setBrush(self._bg)
        if self._border:
            from PySide6.QtGui import QPen
            p.setPen(QPen(self._border, 1.2))
        else:
            p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(box, r, r)
        f = QFont('Segoe UI')
        f.setPixelSize(self._font_px)
        f.setWeight(QFont.Weight.ExtraBold if self._radius is not None else QFont.Weight.Bold)
        p.setFont(f)
        p.setPen(self._fg)
        p.drawText(box, Qt.AlignmentFlag.AlignCenter, self.text())


class SmoothPillButton(QPushButton):
    """True QPainter-antialiased stadium pill button (avoids Qt QSS polygonal corners)."""

    def __init__(self, value='', slot=None):
        super().__init__(value)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        if slot:
            self.clicked.connect(slot)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        box = QRectF(self.rect()).adjusted(0.75, 0.75, -0.75, -0.75)
        r = box.height() * 0.5
        if not self.isEnabled():
            bg = QColor(255, 255, 255, 130)
            fg = QColor(15, 32, 56, 130)
        elif self.underMouse():
            bg = QColor('#EEF6FF')
            fg = QColor('#0F2038')
        else:
            bg = QColor('#FFFFFF')
            fg = QColor('#0F2038')
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(box, r, r)

        f = QFont('Segoe UI')
        f.setPixelSize(15)
        f.setWeight(QFont.Weight.Bold)
        p.setFont(f)
        text = self.text().strip()
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(text)
        ico = self.icon()
        isz = 18
        gap = 6 if not ico.isNull() else 0
        total_w = (isz + gap if not ico.isNull() else 0) + tw
        sx = box.center().x() - total_w * 0.5
        if not ico.isNull():
            iy = box.center().y() - isz * 0.5
            p.drawPixmap(QRectF(sx, iy, isz, isz), ico.pixmap(128, 128), QRectF(0, 0, 128, 128))
            sx += isz + gap
        p.setPen(fg)
        p.drawText(QRectF(sx, box.top(), tw + 4, box.height()), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)


def configure_app(app):
    fonts = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
    for name in ('segoeui.ttf', 'segoeuib.ttf', 'segoeuisl.ttf'):
        if (fonts / name).exists():
            QFontDatabase.addApplicationFont(str(fonts / name))
    app.setFont(QFont('Segoe UI', 10))
    app.setStyle('Fusion')


def painter_font(p, size, bold=False, serif=False):
    f = QFont('Segoe UI')
    f.setPixelSize(size)
    f.setWeight(QFont.Weight.ExtraBold if bold else QFont.Weight.Medium)
    p.setFont(f)


class InlineClue(QLabel):
    chosen = Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self.active = False
        self._selecting = False
        self.setWordWrap(True)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.LinksAccessibleByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByKeyboard
        )
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setOpenExternalLinks(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.active:
            self._selecting = True
            self.chosen.emit()
            event.accept()
            return
        super().mousePressEvent(event)
        event.accept()

    def mouseReleaseEvent(self, event):
        if self._selecting:
            self._selecting = False
            event.accept()
            return
        super().mouseReleaseEvent(event)
        event.accept()


class CardFadeEffect(QGraphicsOpacityEffect):
    """Softly fade non-focused cards into the airy sky backdrop."""

    def __init__(self, card):
        super().__init__(card)
        self.card = card

    def draw(self, painter):
        if self.opacity() < 1.:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(215, 236, 253, 180))
            painter.drawRoundedRect(
                QRectF(4, 3, self.card.width() - 8, self.card.height() - 7), 12, 12
            )
            painter.restore()
        super().draw(painter)


class DeskSurface(QWidget):
    """Harbor at dusk, with a shaded skyline behind the board controls."""

    def __init__(self):
        super().__init__()
        self.harbor = QPixmap(str(ROOT / 'assets/scenery/harbor.png'))

    def paintEvent(self, event):
        painter = QPainter(self)
        bounds = QRectF(self.rect())
        scale = max(bounds.width()/self.harbor.width(), bounds.height()/self.harbor.height())
        source = QRectF(0, 0, bounds.width()/scale, bounds.height()/scale)
        source.moveCenter(QRectF(self.harbor.rect()).center())
        painter.drawPixmap(bounds, self.harbor, source)
        dusk = QLinearGradient(0, 0, 0, bounds.height())
        dusk.setColorAt(0, QColor(37, 32, 63, 212))
        dusk.setColorAt(.16, QColor(115, 65, 85, 128))
        dusk.setColorAt(.65, QColor(60, 63, 94, 100))
        dusk.setColorAt(1, QColor(29, 57, 72, 135))
        painter.fillRect(bounds, dusk)
