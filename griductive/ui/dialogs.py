"""Cozy Harbor modal notices matching the coastal pixel-character aesthetic."""
from PySide6.QtCore import Qt, QSize, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QFont
from PySide6.QtWidgets import (
    QDialog, QFrame, QLabel, QToolButton, QHBoxLayout, QVBoxLayout,
    QGraphicsDropShadowEffect, QWidget,
)
from .icons import icon
from .widgets import PixelHintButton


class ModalScrim(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('noticeScrim')
        self.setStyleSheet('QFrame#noticeScrim {background:rgba(14, 28, 44, 122);border:0;}')

    def mousePressEvent(self, event):
        event.accept()

    def mouseReleaseEvent(self, event):
        event.accept()


class NoticePanel(QFrame):
    """Cozy Harbor postcard dialog surface with top tone accent ribbon."""

    def __init__(self, accent_hex='#E5A33B', parent=None):
        super().__init__(parent)
        self.accent_hex = accent_hex

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        box = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)

        # Harbor navy outer shell + bottom warm bevel
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor('#243B52'))
        p.drawRoundedRect(box, 14.0, 14.0)

        bevel = box.adjusted(2.0, 2.0, -2.0, -2.0)
        p.setBrush(QColor('#D6C5AA'))
        p.drawRoundedRect(bevel, 12.0, 12.0)

        paper = bevel.adjusted(0.0, 0.0, 0.0, -3.5)
        p.setBrush(QColor('#FFFBF2'))
        p.drawRoundedRect(paper, 12.0, 12.0)

        # Clip top accent strip cleanly inside paper's rounded top corners, then stroke outer rim on top
        p.save()
        clip = QPainterPath()
        clip.addRoundedRect(paper, 12.0, 12.0)
        p.setClipPath(clip)
        p.fillRect(QRectF(paper.left(), paper.top(), paper.width(), 6.5), QColor(self.accent_hex))
        p.restore()

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor('#243B52'), 2.2))
        p.drawRoundedRect(box, 14.0, 14.0)


class PortraitVignette(QWidget):
    """Framed character portrait vignette inside Hint and Notice modals."""

    def __init__(self, portrait, cell_text='', parent=None):
        super().__init__(parent)
        self.portrait = portrait
        self.cell_text = cell_text
        self.setFixedSize(148, 158)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        box = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)

        p.setBrush(QColor('#DFEFF4'))
        p.setPen(QPen(QColor('#BDD3DF'), 1.6))
        p.drawRoundedRect(box, 12.0, 12.0)

        # Clip pixel portrait inside the rounded vignette bounds
        p.save()
        clip = QPainterPath()
        clip.addRoundedRect(box.adjusted(2, 2, -2, -2), 10.0, 10.0)
        p.setClipPath(clip)

        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        scaled = self.portrait.scaled(
            QSize(136, 148),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        sx = (self.width() - scaled.width()) * 0.5
        sy = box.bottom() - scaled.height() + 4
        p.drawPixmap(QPointF(sx, sy), scaled)
        p.restore()

        if self.cell_text:
            chip = QRectF(10, 10, 36, 22)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor('#235E8C'))
            p.drawRoundedRect(chip, 5.0, 5.0)
            f = QFont('Segoe UI')
            f.setPixelSize(12)
            f.setWeight(QFont.Weight.ExtraBold)
            p.setFont(f)
            p.setPen(QColor('#FFFFFF'))
            p.drawText(chip, Qt.AlignmentFlag.AlignCenter, self.cell_text)


class GameNotice(QDialog):
    def __init__(self, parent, theme, title, message, *, tone='info', subject=None, action='Đã hiểu'):
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setWindowTitle(title)
        self.setAccessibleName(title)
        self.setFixedWidth(500 if subject else 448)

        tone_cfg = {
            'success': ('#2FA36B', '#DCF5E7', '#1E7A4D', 'check', 'emerald'),
            'warning': ('#E05A5A', '#FDE8E8', '#B83838', 'warning', 'amber'),
            'info': ('#E5A33B', '#FFF0C9', '#9A6316', 'hint', 'amber'),
        }.get(tone, ('#E5A33B', '#FFF0C9', '#9A6316', 'hint', 'amber'))
        ribbon_hex, badge_bg, icon_hex, glyph_name, btn_variant = tone_cfg

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 22)

        self.panel = NoticePanel(accent_hex=ribbon_hex)
        self.panel.setObjectName('gameNotice')
        outer.addWidget(self.panel)

        self.setStyleSheet(f'''
QFrame#gameNotice {{background:transparent;border:0;}}
QFrame#gameNotice QLabel {{background:transparent;border:0;color:{theme.text};}}
QFrame#gameNotice QLabel#noticeBadge {{
    background:{badge_bg};
    border:1.5px solid {ribbon_hex};
    border-radius:10px;
}}
QLabel#noticeTitle {{
    font-family:"Segoe UI";
    font-size:19px;
    font-weight:800;
    color:#15283B;
}}
QLabel#noticeSubject {{
    font-family:"Segoe UI";
    font-size:21px;
    font-weight:800;
    color:#132536;
}}
QLabel#noticeProfession {{
    font-family:"Segoe UI";
    font-size:13px;
    font-weight:600;
    color:#586C80;
}}
QLabel#noticeMessage {{
    font-family:"Segoe UI";
    font-size:14.5px;
    font-weight:500;
    color:#2B3E50;
}}
QToolButton#noticeClose {{
    background:rgba(226, 214, 194, 90);
    border:1px solid transparent;
    border-radius:7px;
    padding:3px;
}}
QToolButton#noticeClose:hover {{
    background:#F5E5C8;
    border-color:#C9B08A;
}}
''')

        shadow = QGraphicsDropShadowEffect(self.panel)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(12, 26, 42, 115))
        self.panel.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(22, 20, 20, 20)
        layout.setSpacing(16)

        # Header row
        heading = QHBoxLayout()
        heading.setSpacing(12)
        symbol = QLabel()
        symbol.setObjectName('noticeBadge')
        symbol.setFixedSize(38, 38)
        symbol.setAlignment(Qt.AlignmentFlag.AlignCenter)
        symbol.setPixmap(icon(glyph_name, icon_hex).pixmap(QSize(22, 22)))
        heading.addWidget(symbol)

        self.title_label = QLabel(title)
        self.title_label.setObjectName('noticeTitle')
        heading.addWidget(self.title_label, 1)

        self.close_button = QToolButton()
        self.close_button.setObjectName('noticeClose')
        self.close_button.setIcon(icon('cross', '#524336'))
        self.close_button.setIconSize(QSize(16, 16))
        self.close_button.setFixedSize(28, 28)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.setAccessibleName('Đóng thông báo')
        self.close_button.setToolTip('Đóng (Esc)')
        self.close_button.clicked.connect(self.reject)
        heading.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(heading)

        # Body row
        body = QHBoxLayout()
        body.setSpacing(16)
        if subject:
            first, portrait = subject
            if hasattr(first, 'name'):
                subj_name = first.name
                subj_cell = getattr(first, 'cell', '')
                subj_prof = getattr(first, 'profession', '')
            else:
                subj_name = str(first)
                subj_cell = ''
                subj_prof = ''
            figure = PortraitVignette(portrait, cell_text=subj_cell)
            figure.setObjectName('noticeFigure')
            body.addWidget(figure, 0, Qt.AlignmentFlag.AlignTop)

            words = QVBoxLayout()
            words.setSpacing(4)
            name_label = QLabel(subj_name)
            name_label.setObjectName('noticeSubject')
            words.addWidget(name_label)
            if subj_prof:
                prof_label = QLabel(subj_prof)
                prof_label.setObjectName('noticeProfession')
                words.addWidget(prof_label)
            words.addSpacing(6)
        else:
            words = QVBoxLayout()
            words.setSpacing(8)

        self.message = QLabel(message)
        self.message.setObjectName('noticeMessage')
        self.message.setWordWrap(True)
        self.message.setTextFormat(Qt.TextFormat.PlainText)
        words.addWidget(self.message)
        words.addStretch(1)
        body.addLayout(words, 1)
        layout.addLayout(body)

        # Footer action row
        actions = QHBoxLayout()
        actions.addStretch(1)
        self.action_button = PixelHintButton(action, variant=btn_variant)
        self.action_button.setObjectName('noticeAction')
        btn_w = max(118, self.action_button.fontMetrics().horizontalAdvance(action) + 46)
        self.action_button.setFixedSize(btn_w, 38)
        self.action_button.setDefault(True)
        self.action_button.clicked.connect(self.accept)
        actions.addWidget(self.action_button)
        layout.addLayout(actions)
        self.adjustSize()
