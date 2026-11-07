"""Desktop widgets."""
import os
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QColor, QPainter, QFont, QFontDatabase
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QGraphicsOpacityEffect
from .assets import scenery_image

def label(value='',name=None):
    w=QLabel(value);w.setWordWrap(True);w.setTextFormat(Qt.TextFormat.PlainText)
    if name:w.setObjectName(name)
    return w


def button(value,slot=None,primary=False):
    w=QPushButton(value)
    if primary:w.setObjectName('primary')
    if slot:w.clicked.connect(slot)
    return w


def configure_app(app):
    fonts=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
    for name in ('segoeui.ttf','segoeuib.ttf','cambria.ttc','cambriab.ttf'):
        if (fonts/name).exists():QFontDatabase.addApplicationFont(str(fonts/name))
    app.setFont(QFont('Segoe UI',10));app.setStyle('Fusion')


def painter_font(p,size,bold=False,serif=False):
    f=QFont('Cambria' if serif else 'Segoe UI');f.setPixelSize(size);f.setBold(bold);p.setFont(f)


class InlineClue(QLabel):
    chosen=Signal()

    def __init__(self,parent):
        super().__init__(parent);self.active=False;self._selecting=False
        self.setWordWrap(True);self.setTextFormat(Qt.TextFormat.RichText)
        self.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.LinksAccessibleByKeyboard)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setOpenExternalLinks(False)

    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton and not self.active:
            self._selecting=True;self.chosen.emit();event.accept();return
        super().mousePressEvent(event)
        event.accept()

    def mouseReleaseEvent(self,event):
        if self._selecting:
            self._selecting=False;event.accept();return
        super().mouseReleaseEvent(event)
        event.accept()


class CardFadeEffect(QGraphicsOpacityEffect):
    """Fade into card paper rather than making the busy seaside show through."""
    def __init__(self,card):
        super().__init__(card);self.card=card

    def draw(self,painter):
        if self.opacity()<1.:
            painter.save();painter.setRenderHint(QPainter.RenderHint.Antialiasing,True)
            painter.setPen(Qt.PenStyle.NoPen);painter.setBrush(QColor(self.card.theme.card_unknown))
            painter.drawRoundedRect(QRectF(5,5,self.card.width()-10,self.card.height()-10),7,7)
            painter.restore()
        super().draw(painter)


class DeskSurface(QWidget):
    def __init__(self):
        super().__init__()
        self.art=scenery_image('pixel-desk.png');self.pixel_style=True

    def paintEvent(self,event):
        p=QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, not self.pixel_style)
        if not self.art.isNull():
            p.drawPixmap(QRectF(self.rect()),self.art,QRectF(self.art.rect()))
        else:p.fillRect(self.rect(),QColor('#DCEFF6'))

