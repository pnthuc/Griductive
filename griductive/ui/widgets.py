"""Desktop UI widgets: buttons, header bar, menus, and coordinate labels."""
import os
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QSize
from PySide6.QtGui import (
    QPainterPath, QLinearGradient, QColor, QPainter, QFont, QFontDatabase,
    QPixmap, QPen, QFontMetrics,
)
from PySide6.QtWidgets import (
    QToolButton, QWidget, QLabel, QPushButton, QFrame, QMenu,
    QGraphicsOpacityEffect, QSizePolicy,
)
from .assets import ROOT


def label(value='', name=None):
    w = QLabel(value)
    w.setWordWrap(True)
    w.setTextFormat(Qt.TextFormat.PlainText)
    if name:
        w.setObjectName(name)
    return w


def pixel_frame(box, step=3):
    """Closed outline with one crisp stepped chamfer at each corner."""
    left, top, right, bottom = box.getCoords()
    path = QPainterPath()
    path.moveTo(left + step, top)
    for x, y in (
        (right - step, top), (right - step, top + step), (right, top + step),
        (right, bottom - step), (right - step, bottom - step), (right - step, bottom),
        (left + step, bottom), (left + step, bottom - step), (left, bottom - step),
        (left, top + step), (left + step, top + step),
    ):
        path.lineTo(x, y)
    path.closeSubpath()
    return path


class CozyMenu(QMenu):
    """Translucent custom-painted QMenu for clean rounded corners on Windows."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        box = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -2.5)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(14, 28, 44, 65))
        p.drawRoundedRect(box.translated(0, 2.0), 10.0, 10.0)
        p.setBrush(QColor('#FFFBF2'))
        p.setPen(QPen(QColor('#2C4359'), 2.0))
        p.drawRoundedRect(box, 10.0, 10.0)
        p.end()
        super().paintEvent(event)


BUTTON_PALETTES = {
    'amber': {
        'face': '#FFE39E', 'hover': '#FFEDBE', 'border': '#3A2D22',
        'lip': '#C98E32', 'ink': '#2A1D11', 'hi': '#FFF7DC',
    },
    'cream': {
        'face': '#FFF6E6', 'hover': '#FFECCB', 'border': '#2B4055',
        'lip': '#BFA989', 'ink': '#172A3C', 'hi': '#FFFFFF',
    },
    'mint': {
        'face': '#DDF4E6', 'hover': '#C8ECD7', 'border': '#224B39',
        'lip': '#56AD80', 'ink': '#143B2A', 'hi': '#F2FCF6',
    },
    'emerald': {
        'face': '#2FA36B', 'hover': '#27935E', 'border': '#184A32',
        'lip': '#1D6E46', 'ink': '#FFFFFF', 'hi': '#6AD29E',
    },
    'navy': {
        'face': '#235E8C', 'hover': '#1E517A', 'border': '#14334D',
        'lip': '#163E5E', 'ink': '#FFFFFF', 'hi': '#5694C4',
    },
}


def paint_cozy_keycap(painter: QPainter, rect, variant='cream', hovered=False, pressed=False, enabled=True, radius=8.0):
    pal = BUTTON_PALETTES.get(variant, BUTTON_PALETTES['cream'])
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    box = QRectF(rect).adjusted(1.0, 1.0 + (2.0 if pressed else 0.0), -1.0, -1.0)
    lip_h = 1.0 if pressed else 3.0

    if not enabled:
        painter.setOpacity(0.55)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(pal['border']))
    painter.drawRoundedRect(box, radius, radius)

    inner = box.adjusted(1.6, 1.6, -1.6, -1.6)
    painter.setBrush(QColor(pal['lip']))
    painter.drawRoundedRect(inner, max(2.0, radius - 1.5), max(2.0, radius - 1.5))

    face = inner.adjusted(0.0, 0.0, 0.0, -lip_h)
    fill_hex = pal['hover'] if (hovered and enabled) else pal['face']
    painter.setBrush(QColor(fill_hex))
    painter.drawRoundedRect(face, max(2.0, radius - 1.5), max(2.0, radius - 1.5))

    hi_col = QColor(pal['hi'])
    hi_col.setAlpha(155)
    painter.setPen(QPen(hi_col, 1.1))
    painter.drawLine(
        QPointF(face.left() + radius * 0.7, face.top() + 1.2),
        QPointF(face.right() - radius * 0.7, face.top() + 1.2),
    )
    painter.restore()
    return face, QColor(pal['ink'])


def paint_pixel_key(painter, button, variant='cream'):
    hovered = button.underMouse() or button.hasFocus()
    face, _ = paint_cozy_keycap(
        painter, button.rect(), variant=variant,
        hovered=hovered, pressed=button.isDown(), enabled=button.isEnabled(),
    )
    return face


class HeaderBar(QFrame):
    """Cozy Harbor translucent capsule framing the top HUD."""

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        box = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(11, 22, 36, 75))
        p.drawRoundedRect(box.translated(0, 2.0), 12.0, 12.0)

        grad = QLinearGradient(0, box.top(), 0, box.bottom())
        grad.setColorAt(0.0, QColor(28, 46, 68, 212))
        grad.setColorAt(1.0, QColor(20, 35, 54, 226))
        p.setBrush(grad)
        p.setPen(QPen(QColor(255, 238, 208, 72), 1.2))
        p.drawRoundedRect(box, 12.0, 12.0)


class BrandMark(QWidget):
    """2x2 puzzle-card emblem next to the application title."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(26, 26)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        colors = (
            (1.5, 1.5, '#FFE29A'),
            (14.0, 1.5, '#52C98A'),
            (1.5, 14.0, '#F57A82'),
            (14.0, 14.0, '#FFF8EC'),
        )
        p.setPen(QPen(QColor('#182B3E'), 1.3))
        for x, y, col in colors:
            p.setBrush(QColor(col))
            p.drawRoundedRect(QRectF(x, y, 10.5, 10.5), 3.0, 3.0)


class CaseSelectorButton(QToolButton):
    """Responsive case switcher pill that elides text on narrow windows."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.size_tag = '3×3'
        self.case_title = ''
        self._ideal_w = 240
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(36)
        self.setMinimumWidth(126)
        self.setMaximumWidth(330)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def set_case_info(self, title: str, size: int):
        self.case_title = title
        self.size_tag = f'{size}×{size}'
        self.setText(title)
        fm = QFontMetrics(self._title_font())
        self._ideal_w = min(330, max(165, fm.horizontalAdvance(title) + 92))
        self.updateGeometry()
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(self._ideal_w, 36)

    @staticmethod
    def _title_font():
        f = QFont('Segoe UI')
        f.setPixelSize(13)
        f.setWeight(QFont.Weight.Bold)
        return f

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        face, ink = paint_cozy_keycap(
            p, self.rect(), variant='cream',
            hovered=self.underMouse() or self.hasFocus(),
            pressed=self.isDown(), enabled=self.isEnabled(), radius=8.0,
        )
        chip = QRectF(face.left() + 6, face.center().y() - 9.5, 35, 19)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor('#234666'))
        p.drawRoundedRect(chip, 5.0, 5.0)
        fc = QFont('Segoe UI')
        fc.setPixelSize(11)
        fc.setWeight(QFont.Weight.ExtraBold)
        p.setFont(fc)
        p.setPen(QColor('#FFF9EE'))
        p.drawText(chip, Qt.AlignmentFlag.AlignCenter, self.size_tag)

        ft = self._title_font()
        p.setFont(ft)
        p.setPen(ink)
        avail_w = max(24.0, face.right() - chip.right() - 25.0)
        text_rect = QRectF(chip.right() + 7, face.top(), avail_w, face.height())
        elided = QFontMetrics(ft).elidedText(self.case_title, Qt.TextElideMode.ElideRight, int(avail_w))
        p.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided)

        cx = face.right() - 12.5
        cy = face.center().y() + 0.5
        p.setPen(QPen(QColor('#2B4661'), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        path = QPainterPath()
        path.moveTo(cx - 4.0, cy - 2.0)
        path.lineTo(cx, cy + 2.2)
        path.lineTo(cx + 4.0, cy - 2.0)
        p.drawPath(path)


class ProgressPill(QWidget):
    """Responsive solved-card counter pill (switches to compact '2/9' when header is narrow)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.solved = 0
        self.total = 0
        self.compact = False
        self.setFixedHeight(28)
        self._sync_width()

    def _sync_width(self):
        done = self.total > 0 and self.solved >= self.total
        if self.compact:
            self.setFixedWidth(68 if done else 58)
        else:
            self.setFixedWidth(132 if done else 108)

    def set_compact(self, compact: bool):
        if self.compact != compact:
            self.compact = compact
            self._sync_width()
            self.update()

    def set_progress(self, solved: int, total: int):
        self.solved = solved
        self.total = total
        self._sync_width()
        self.update()

    def paintEvent(self, event):
        if self.total <= 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        done = self.solved >= self.total
        box = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        bg = QColor(42, 152, 98, 228) if done else QColor(255, 248, 234, 38)
        border = QColor(134, 239, 172, 195) if done else QColor(255, 244, 220, 82)
        p.setBrush(bg)
        p.setPen(QPen(border, 1.2))
        p.drawRoundedRect(box, 13.0, 13.0)

        f = QFont('Segoe UI')
        f.setPixelSize(11 if self.compact else 12)
        f.setWeight(QFont.Weight.Bold)
        p.setFont(f)
        p.setPen(QColor('#FFFFFF' if done else '#FFF5E0'))
        if self.compact:
            txt = f'★ {self.solved}/{self.total}' if done else f'{self.solved}/{self.total}'
        else:
            txt = f'★ Hoàn thành {self.solved}/{self.total}' if done else f'Đã mở {self.solved} / {self.total}'
        p.drawText(box, Qt.AlignmentFlag.AlignCenter, txt)


class HudButton(QToolButton):
    """Raised HUD button."""

    def __init__(self, variant='cream', parent=None):
        super().__init__(parent)
        self.variant = variant
        self.active_badge = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        v = 'emerald' if self.active_badge else self.variant
        box, ink = paint_cozy_keycap(
            painter, self.rect(), variant=v,
            hovered=self.underMouse() or self.hasFocus(),
            pressed=self.isDown(), enabled=self.isEnabled(), radius=8.0,
        )
        if not self.isEnabled():
            painter.setOpacity(0.55)
        font = QFont('Segoe UI')
        font.setWeight(QFont.Weight.Bold)
        font.setPixelSize(13)
        painter.setFont(font)
        text = self.text().strip()
        width = painter.fontMetrics().horizontalAdvance(text) if text else 0
        has_icon = not self.icon().isNull()
        side = self.iconSize().width() if has_icon else 0
        gap = 5 if (text and has_icon) else 0
        total = side + gap + width
        x = box.center().x() - total * 0.5
        if has_icon:
            y = box.center().y() - side * 0.5
            pix = self.icon().pixmap(side * 2, side * 2)
            painter.drawPixmap(QRectF(x, y, side, side), pix, QRectF(pix.rect()))
            x += side + gap
        if text:
            painter.setPen(ink)
            painter.drawText(QRectF(x, box.y(), width + 4, box.height()), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)


class PixelLabel(QLabel):
    """Compact centered Cozy Harbor coordinate badge."""

    def __init__(self, value='', name=None, *, bg=(255, 247, 230, 238), border=(45, 69, 94, 220), fg='#14283C', radius=8, font_px=13, is_row=False):
        super().__init__(value)
        if name:
            self.setObjectName(name)
        self._bg = QColor(*bg)
        self._border = QColor(*border) if border else QColor('#2D455E')
        self._fg = QColor(fg)
        self._radius = radius or 7
        self._font_px = font_px
        self._is_row = is_row
        self.highlighted = False
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        bw = min(float(self.width()) - 2.0, 26.0 if self._is_row else 42.0)
        bh = min(float(self.height()) - 2.0, 34.0 if self._is_row else 22.0)
        cx = (self.width() - bw) * 0.5
        cy = (self.height() - bh) * 0.5
        pill = QRectF(cx, cy, bw, bh)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(14, 28, 44, 70))
        p.drawRoundedRect(pill.translated(0, 1.5), self._radius, self._radius)

        fill = QColor('#FFE39E') if self.highlighted else self._bg
        rim = QColor('#C88728') if self.highlighted else self._border
        p.setBrush(fill)
        p.setPen(QPen(rim, 1.5))
        p.drawRoundedRect(pill, self._radius, self._radius)

        f = QFont('Segoe UI')
        f.setPixelSize(self._font_px)
        f.setWeight(QFont.Weight.ExtraBold)
        p.setFont(f)
        p.setPen(self._fg)
        p.drawText(pill, Qt.AlignmentFlag.AlignCenter, self.text())


class PixelHintButton(QPushButton):
    """Action button used in dialogs and Solver Journal."""

    def __init__(self, value='', slot=None, variant='cream'):
        super().__init__(value)
        self.variant = variant
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        if slot:
            self.clicked.connect(slot)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        v = self.variant
        if self.objectName() in ('noticeAction', 'journalPrimary') and v == 'cream':
            v = 'emerald' if self.objectName() == 'journalPrimary' else 'navy'

        box, ink = paint_cozy_keycap(
            p, self.rect(), variant=v,
            hovered=self.underMouse() or self.hasFocus(),
            pressed=self.isDown(), enabled=self.isEnabled(), radius=8.0,
        )
        if not self.isEnabled():
            p.setOpacity(0.55)

        f = QFont('Segoe UI')
        f.setPixelSize(13)
        f.setWeight(QFont.Weight.Bold)
        p.setFont(f)
        text = self.text().strip()
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(text)
        ico = self.icon()
        isz = 16
        gap = 6 if not ico.isNull() else 0
        total_w = (isz + gap if not ico.isNull() else 0) + tw
        sx = box.center().x() - total_w * 0.5
        if not ico.isNull():
            iy = box.center().y() - isz * 0.5
            pix = ico.pixmap(64, 64)
            p.drawPixmap(QRectF(sx, iy, isz, isz), pix, QRectF(pix.rect()))
            sx += isz + gap
        p.setPen(ink)
        p.drawText(QRectF(sx, box.top(), tw + 4, box.height()), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)


def configure_app(app):
    fonts = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
    for name in ('segoeui.ttf', 'segoeuib.ttf', 'segoeuisl.ttf'):
        if (fonts / name).exists():
            QFontDatabase.addApplicationFont(str(fonts / name))
    app.setFont(QFont('Segoe UI', 10))
    app.setStyle('Fusion')


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
    """Softly fade non-focused cards into the warm harbor sky backdrop."""

    def __init__(self, card):
        super().__init__(card)
        self.card = card

    def draw(self, painter):
        if self.opacity() < 1.0:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(226, 236, 244, 165))
            painter.drawRoundedRect(
                QRectF(4, 3, self.card.width() - 8, self.card.height() - 7), 10, 10
            )
            painter.restore()
        super().draw(painter)


class DeskSurface(QWidget):
    """Harbor at dusk, with a warm golden-hour coastal atmosphere behind the board."""

    def __init__(self):
        super().__init__()
        self.harbor = QPixmap(str(ROOT / 'assets/ui/harbor.png'))

    def paintEvent(self, event):
        painter = QPainter(self)
        bounds = QRectF(self.rect())
        if not self.harbor.isNull():
            scale = max(bounds.width() / self.harbor.width(), bounds.height() / self.harbor.height())
            source = QRectF(0, 0, bounds.width() / scale, bounds.height() / scale)
            source.moveCenter(QRectF(self.harbor.rect()).center())
            painter.drawPixmap(bounds, self.harbor, source)
        dusk = QLinearGradient(0, 0, 0, bounds.height())
        dusk.setColorAt(0.0, QColor(28, 38, 62, 185))
        dusk.setColorAt(0.22, QColor(98, 64, 82, 108))
        dusk.setColorAt(0.68, QColor(52, 68, 92, 92))
        dusk.setColorAt(1.0, QColor(26, 52, 68, 128))
        painter.fillRect(bounds, dusk)
