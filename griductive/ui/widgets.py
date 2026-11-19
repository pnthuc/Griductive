"""Desktop widgets — Alto's Odyssey x Gamma 5 flat-vector landscape backdrop."""
import os
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QPainterPath, QLinearGradient, QColor, QPainter, QFont, QFontDatabase, QPixmap
from PySide6.QtWidgets import QToolButton, QWidget, QLabel, QPushButton, QGraphicsOpacityEffect
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


def pixel_frame(box, step=3):
    """Closed outline with one square step at each corner."""
    left, top, right, bottom = box.getCoords()
    path = QPainterPath()
    path.moveTo(left+step, top)
    for x, y in ((right-step, top), (right-step, top+step), (right, top+step),
                 (right, bottom-step), (right-step, bottom-step), (right-step, bottom),
                 (left+step, bottom), (left+step, bottom-step), (left, bottom-step),
                 (left, top+step), (left+step, top+step)):
        path.lineTo(x, y)
    path.closeSubpath()
    return path


HUD_BACKGROUND = QColor('#F5DEAD')
HUD_BORDER = QColor('#463D39')


def paint_label_frame(p, rect, background, border):
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    box = QRectF(rect).adjusted(0.75, 0.75, -0.75, -0.75)
    p.setBrush(background)
    if border:
        from PySide6.QtGui import QPen
        p.setPen(QPen(border, 1.2))
    else:
        p.setPen(Qt.PenStyle.NoPen)
    p.drawPath(pixel_frame(box))
    return box


def paint_pixel_key(painter, button):
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    box = QRectF(button.rect()).adjusted(0, 2 if button.isDown() else 0, -1, -1)
    painter.fillPath(pixel_frame(box), HUD_BORDER)
    face = box.adjusted(2, 2, -2, -2 if button.isDown() else -5)
    fill = QColor('#FFEDBF') if button.underMouse() or button.hasFocus() else HUD_BACKGROUND
    painter.fillPath(pixel_frame(face, 2), fill if button.isEnabled() else QColor(255, 255, 255, 130))
    return face


class HudButton(QToolButton):
    def paintEvent(self, event):
        painter = QPainter(self)
        box = paint_pixel_key(painter, self)
        painter.setOpacity(1 if self.isEnabled() else .55)
        font = QFont('Segoe UI')
        font.setBold(True)
        font.setPixelSize(15)
        painter.setFont(font)
        text = self.text()
        width = painter.fontMetrics().horizontalAdvance(text)
        side = self.iconSize().width()
        gap = 3 if text else 0
        x = round(box.center().x() - (side + gap + width)/2)
        y = round(box.center().y() - side/2)
        painter.drawPixmap(x, y, self.icon().pixmap(side, side))
        painter.setPen(QColor('#0F2942'))
        painter.drawText(QRectF(x+side+gap, box.y(), width+1, box.height()),
                         Qt.AlignmentFlag.AlignVCenter, text)


class PixelLabel(QLabel):
    """Stepped board label."""

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
        box = paint_label_frame(p, self.rect(), self._bg, self._border)
        f = QFont('Segoe UI')
        f.setPixelSize(self._font_px)
        f.setWeight(QFont.Weight.ExtraBold if self._radius is not None else QFont.Weight.Bold)
        p.setFont(f)
        p.setPen(self._fg)
        p.drawText(box, Qt.AlignmentFlag.AlignCenter, self.text())


class PixelHintButton(QPushButton):
    """Raised hint key with a recessed pressed state."""

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
        box = paint_pixel_key(p, self)
        fg = QColor('#0F2038')
        if not self.isEnabled():
            fg.setAlpha(130)

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
