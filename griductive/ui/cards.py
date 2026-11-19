"""Desktop cards — Exact Alto's Odyssey x Reigns Lineless Flat-Vector UI."""
import math
from html import escape
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QSize
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QFont, QTextDocument
from PySide6.QtWidgets import QWidget, QPushButton, QBoxLayout, QFrame, QScrollArea
from ..presentation.wording_vi import STATUS_TEXT
from .icons import icon
from .character_animation import CharacterAnimation
from .card_feedback import CardFeedback
from .widgets import pixel_frame, InlineClue, CardFadeEffect


class VerdictButton(QPushButton):
    """A stepped pixel keycap with a recessed pressed state."""

    def paintEvent(self, event):
        innocent = self.objectName() == 'innocent'
        outline, shadow, face, light = (
            ('#244D42', '#276547', '#327F58', '#81BC85') if innocent else
            ('#632F39', '#8B3745', '#B54954', '#E69588')
        )
        painter = QPainter(self)
        unit = max(2, round(self.height()/16))
        top = unit if self.isDown() else 0
        width, height = self.width(), self.height()
        def slab(x, y, w, h, color):
            painter.fillRect(x+unit, y, w-2*unit, h, QColor(color))
            painter.fillRect(x, y+unit, w, h-2*unit, QColor(color))

        slab(0, top, width, height-top, outline)
        slab(unit, top+unit, width-2*unit, height-top-2*unit, shadow)
        depth = unit if self.isDown() else 2*unit
        slab(unit, top+unit, width-2*unit, height-top-unit-depth, face)
        painter.fillRect(3*unit, top+unit, width-6*unit, unit, QColor(light))
        if self.hasFocus() or self.underMouse():
            painter.fillRect(3*unit, height-depth-unit, width-6*unit, unit, QColor(light))
        font = self.font()
        font.setBold(True)
        font.setPixelSize(max(11, round(height*.38)))
        painter.setFont(font)
        label = self.text().strip()
        size = painter.fontMetrics().horizontalAdvance(label)
        pattern = ('00001','00010','10100','01000') if innocent else ('10001','01010','00100','01010','10001')
        start = (width-size-7*unit)//2
        mid = (height+top-depth)//2
        ink = QColor('#FFF8E9' if self.isEnabled() else '#C6C1B8')
        for row, bits in enumerate(pattern):
            for col, bit in enumerate(bits):
                if bit == '1':
                    painter.fillRect(start+col*unit, mid+(row-len(pattern)//2)*unit, unit, unit, ink)
        painter.setPen(ink)
        painter.drawText(QRectF(start+7*unit, top, size+2, height-top-depth),
                         Qt.AlignmentFlag.AlignVCenter, label)


class PortraitCard(QWidget):
    selected = Signal(str)
    verdict_requested = Signal(str, str)

    def __init__(self, character, status, clue, portrait, theme, parent=None):
        super().__init__(parent)
        self.character = character
        self.status = status
        self.clue = clue
        self.portrait = portrait
        self.theme = theme
        self.is_selected = False
        self.counted = False
        self.anchor = False
        self.source = False
        self.dimmed = False
        self.preview_role = None
        self.region_roles = ()
        self.name_role = None
        self.motion = True
        self.pixel_style = True
        self.feedback = CardFeedback()
        self.fade_effect = CardFadeEffect(self)
        self.fade_effect.setOpacity(1.)
        self.setGraphicsEffect(self.fade_effect)
        self.expression_frames = ()
        self.silhouette_frames = ()
        self.expression = CharacterAnimation(status)
        self.expression.elapsed = .5 + (character.portrait * .731) % 3.5
        self.setMinimumSize(152, 90)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(f'{character.cell} {character.name}')

        self.actions = QWidget(self)
        self.actions.setObjectName('verdictActions')
        self.actions.setStyleSheet('QWidget#verdictActions {background:transparent;border:0;}')
        self.verdict_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self.actions)
        self.verdict_layout.setContentsMargins(0, 0, 0, 0)
        self.verdict_layout.setSpacing(0)
        self.verdict_buttons = {}
        for title in ('Innocent', 'Criminal'):
            w = VerdictButton(STATUS_TEXT[title.upper()])
            w.setObjectName(title.lower())
            w.setFixedHeight(38)
            w.setIconSize(QSize(16, 16))
            self.verdict_buttons[title] = w
            w.clicked.connect(
                lambda checked=False, v=title.upper(): self.verdict_requested.emit(self.character.cell, v)
            )
            w.setToolTip('Chỉ chấp nhận khi suy ra được từ lời khai đã mở.')
            self.verdict_layout.addWidget(w, 1)
        self.actions.hide()

        self.clue_text = InlineClue(self)
        self.clue_text.chosen.connect(lambda: self.selected.emit(self.character.cell))
        self.note_scroll = QScrollArea(self)
        self.note_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.note_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.note_scroll.setWidget(self.clue_text)
        self.note_scroll.setWidgetResizable(False)
        self.note_scroll.setStyleSheet(
            'QScrollArea, QScrollArea > QWidget > QWidget {background:transparent;border:0;}'
            'QScrollBar:vertical {width:4px;background:transparent;}'
            'QScrollBar::handle:vertical {background:#CBD5E1;border-radius:2px;}'
            'QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {height:0px;}'
        )
        self.note_scroll.viewport().setAutoFillBackground(False)
        self.active_html = None
        self.props = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.motion:
                self.expression.react()
            self.setFocus()
            self.selected.emit(self.character.cell)
            self.update()
            event.accept()
        else:
            super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            if self.motion:
                self.expression.react()
            self.selected.emit(self.character.cell)
            self.update()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        self.place_actions()
        super().resizeEvent(event)

    def content_geometry(self):
        # Unclamped proportional scale so 1080p / 2K / 4K cards scale typography & icons lushly!
        s = max(0.58, min(1.65, self.height() / 200.))
        rect = QRectF(4, 3, self.width() - 8, self.height() - 7)
        panel_w = max(56., min(rect.width() * 0.385, rect.height() * 0.92))
        panel = QRectF(rect.left(), rect.top(), panel_w, rect.height())
        pad = max(6., round(12 * s))
        text_left = panel.right() + max(10., round(18 * s))
        content = QRectF(text_left, rect.top(), max(32., rect.right() - text_left - pad), rect.height())
        return rect, panel, content

    def paper_geometry(self, content, scale):
        top = content.y() + max(40., round(74 * scale))
        bottom = content.bottom() - max(6., round(10 * scale))
        return QRectF(content.x(), top, content.width(), max(22., bottom - top))

    def place_actions(self):
        rect, panel_rect, content = self.content_geometry()
        s = max(0.58, min(1.65, self.height() / 200.))
        show_actions = self.is_selected and not self.status
        ax = math.floor(content.left())
        aw = max(48, math.floor(content.right()) - ax)
        gap = max(3, round(6*s))
        self.verdict_layout.setSpacing(gap)
        compact = aw < max(138, round(170*s))
        self.verdict_layout.setDirection(
            QBoxLayout.Direction.TopToBottom if compact else QBoxLayout.Direction.LeftToRight
        )
        btn_h = max(23, round(34 * s))
        action_h = 2 * btn_h + gap if compact else btn_h
        ay = max(round(rect.y() + 44 * s), math.floor(rect.bottom() - gap) - action_h)
        self.actions.setGeometry(ax, ay, aw, action_h)
        self.actions.setVisible(show_actions)
        for button in self.verdict_buttons.values():
            button.setFixedHeight(btn_h)

        if self.clue:
            raw_html = self.active_html if self.source and self.active_html else escape(self.clue)
            html = f'<div style="line-height:132%;">{raw_html}</div>'
            self.clue_text.active = self.source
            if self.clue_text.text() != html:
                self.clue_text.setText(html)

            paper = self.paper_geometry(content, s)
            x0, y0 = math.ceil(paper.left()), math.ceil(paper.top())
            w0 = max(16, math.floor(paper.right()) - x0)
            h0 = max(14, math.floor(paper.bottom()) - y0)
            self.note_scroll.setGeometry(x0, y0, w0, h0)
            text_width = max(16, w0 - 6)

            # Adaptive editorial clue sizing: lush for short clues, steps down so 5-6 line clues fit with zero scroll!
            max_px = max(13, round(15.5 * s)) if rect.width() < 260 else max(15, round(19.0 * s))
            min_px = max(11, round(11.8 * s)) if rect.width() < 260 else max(12, round(12.5 * s))
            font_size = min_px
            for cand in range(max_px, min_px - 1, -1):
                probe = QTextDocument()
                probe.setDocumentMargin(0)
                fp = QFont('Segoe UI')
                fp.setPixelSize(cand)
                fp.setWeight(QFont.Weight.Medium)
                probe.setDefaultFont(fp)
                probe.setHtml(html)
                probe.setTextWidth(text_width)
                if math.ceil(probe.size().height()) + 4 <= h0:
                    font_size = cand
                    break

            self.clue_text.setStyleSheet(
                f'font-family:"Segoe UI";font-size:{font_size}px;font-weight:500;'
                f'background:transparent;color:#1E293B;'
            )
            self.note_scroll.show()
            doc = QTextDocument()
            doc.setDocumentMargin(0)
            f = QFont('Segoe UI')
            f.setPixelSize(font_size)
            f.setWeight(QFont.Weight.Medium)
            doc.setDefaultFont(f)
            doc.setHtml(html)
            doc.setTextWidth(text_width)
            needed = math.ceil(doc.size().height()) + 4
            self.clue_text.resize(text_width, max(self.note_scroll.viewport().height(), needed))
            self.clue_text.show()
        else:
            self.note_scroll.hide()
            self.clue_text.hide()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        t = self.theme
        corner = 4
        rect, panel_rect, content = self.content_geometry()
        s = max(0.58, min(1.65, self.height() / 200.))

        # Crisp flat-vector sky shadow under card
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(12, 58, 118, 44))
        p.drawPath(pixel_frame(rect.translated(0, 3), corner))

        card_path = pixel_frame(rect, corner)

        paper = {'INNOCENT': t.card_innocent, 'CRIMINAL': t.card_criminal}.get(self.status, t.card_unknown)
        p.fillPath(card_path, QColor(paper))
        p.save()
        p.setClipPath(card_path)
        p.setClipRect(panel_rect, Qt.ClipOperation.IntersectClip)
        panel_color = {
            'INNOCENT': '#CDE9D6',
            'CRIMINAL': '#F3CCC6',
        }.get(self.status, '#D0E1EB' if self.is_selected else '#E0E8EA')
        p.fillRect(panel_rect, QColor(panel_color))

        silhouette = (not self.status and not self.is_selected)
        frame = self.expression.frame if self.motion else {None: 0, 'INNOCENT': 4, 'CRIMINAL': 6}[self.status]
        blink = self.expression.blink_amount if self.motion else 0.

        # Center the face in the panel; extend the bust through its lower edge.
        side = min(panel_rect.width()*1.06, panel_rect.height())
        dest = QRectF(panel_rect.center().x()-side/2, panel_rect.center().y()-side*.53,
                      side, side*1.5)

        frames = self.silhouette_frames if silhouette else self.expression_frames
        sprite = frames[0 if silhouette else frame] if frames else self.portrait
        # Frame the upper body consistently across all registered animation poses.
        crop = QRectF(sprite.width()*.16, 0.,
                      sprite.width()*.68, sprite.height())
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        p.drawPixmap(dest, sprite, crop)
        if blink > 0.02 and frames:
            p.setOpacity(blink)
            p.drawPixmap(dest, frames[1 if silhouette else self.expression.blink_frame], crop)
        p.setOpacity(1.)
        if self.status == 'CRIMINAL':
            progress = self.expression.bars_progress if self.motion else 1.
            top = panel_rect.top() - (1. - progress) * panel_rect.height()
            bar_width = max(3., panel_rect.width() * .035)
            for fraction in (.18, .39, .61, .82):
                x = panel_rect.left() + panel_rect.width() * fraction
                p.fillRect(QRectF(x, top, bar_width, panel_rect.height()), QColor('#34494E'))
                p.fillRect(QRectF(x, top, bar_width*.32, panel_rect.height()), QColor('#A9BBB2'))
            for fraction in (.17, .86):
                p.fillRect(QRectF(panel_rect.left(), top + panel_rect.height()*fraction,
                                   panel_rect.width(), bar_width), QColor('#465A5A'))
        p.restore()

        if self.props and not self.clue and not self.is_selected:
            pad = max(6., round(9 * s))
            space = self.paper_geometry(content, s)
            scale = min(space.width() * .85 / self.props.width(),
                        (space.height() - pad) / self.props.height())
            width, height = self.props.width() * scale, self.props.height() * scale
            dest = QRectF(content.right() - width, rect.bottom() - pad - height, width, height)
            p.save()
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
            p.drawPixmap(dest, self.props, QRectF(self.props.rect()))
            p.restore()

        # Top-left coordinate pill (A1..E5)
        chip_pad = max(6., round(9 * s))
        chip_h = max(20., round(26 * s))
        chip_w = max(31., round(40 * s))
        chip = QRectF(rect.x() + chip_pad, rect.y() + chip_pad, chip_w, chip_h)
        chip_bg = (
            '#27AE60' if self.status == 'INNOCENT'
            else '#DF4A57' if self.status == 'CRIMINAL'
            else '#2454D8' if self.is_selected
            else '#85A2BF'
        )
        p.setBrush(QColor(chip_bg))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(pixel_frame(chip))
        f_chip = QFont('Segoe UI')
        f_chip.setPixelSize(max(11, round(13.5 * s)))
        f_chip.setWeight(QFont.Weight.Bold)
        p.setFont(f_chip)
        p.setPen(QColor('#FFFFFF'))
        p.drawText(chip, Qt.AlignmentFlag.AlignCenter, self.character.cell)

        # Top-right circular status mark ONLY when solved (vector-sharp floating-point strokes!)
        badge_reserved = 0.0
        if self.status:
            bsz = max(20., round(27 * s))
            bpad = max(7., round(11 * s))
            badge = QRectF(rect.right() - bsz - bpad, rect.y() + bpad, bsz, bsz)
            is_inn = self.status == 'INNOCENT'
            p.setBrush(QColor('#327F58' if is_inn else '#B54954'))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(pixel_frame(badge))
            symbol = icon('check' if is_inn else 'cross', '#FFFFFF')
            symbol.paint(p, badge.toRect())
            badge_reserved = bsz + round(8 * s)

        # Character Name, Profession & subtle editorial divider
        tx = content.x()
        tw = max(24., content.width() - badge_reserved)
        name_size = max(14, round(23.5 * s))
        name_color = {
            'result': t.selected, 'a': t.operand_a, 'b': t.operand_b, 'anchor': t.anchor,
        }.get(self.name_role, '#0B192C')
        f_name = QFont('Segoe UI')
        f_name.setPixelSize(name_size)
        f_name.setWeight(QFont.Weight.ExtraBold)
        p.setFont(f_name)
        p.setPen(QColor(name_color))
        p.drawText(
            QRectF(tx, rect.y() + max(7., round(12 * s)), tw, max(20., round(31 * s))),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self.character.name,
        )
        f_prof = QFont('Segoe UI')
        f_prof.setPixelSize(max(11, round(14.5 * s)))
        f_prof.setWeight(QFont.Weight.Medium)
        p.setFont(f_prof)
        p.setPen(QColor('#52637A'))
        p.drawText(
            QRectF(tx, rect.y() + max(25., round(43 * s)), content.width() - 2, max(15., round(22 * s))),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self.character.profession,
        )
        # Subtle hairline divider anchoring the header area
        div_y = rect.y() + max(39., round(68 * s))
        p.setPen(QPen(QColor('#EBF2FA'), max(1.0, 1.15 * min(1.3, s))))
        p.drawLine(QPointF(tx, div_y), QPointF(content.right(), div_y))

        # Perimeter border: exact original region highlight rules
        colors = []
        if not self.is_selected:
            colors = [
                {'result': t.selected, 'a': t.operand_a, 'b': t.operand_b}[role]
                for role in self.region_roles
            ]
        p.setClipping(False)
        p.setBrush(Qt.BrushStyle.NoBrush)
        status_rim = {'INNOCENT': '#478453', 'CRIMINAL': '#BB5751'}.get(self.status)
        if self.is_selected:
            p.setPen(QPen(QColor(status_rim or t.selected), 5.5))
            p.drawPath(card_path)
        elif colors:
            for i, color in enumerate(colors):
                p.setPen(QPen(QColor(color), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
                p.drawPath(card_path if len(colors) == 1 else card_path.trimmed(i / len(colors), (i + 1) / len(colors)))
        elif self.anchor:
            p.setPen(QPen(QColor(t.anchor), 3.5))
            p.drawPath(card_path)
        else:
            p.setPen(QPen(QColor(status_rim or '#AAA398'), 3.5))
            p.drawPath(card_path)
