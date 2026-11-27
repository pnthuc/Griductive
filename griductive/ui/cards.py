"""Desktop character cards with pixel portraits and verdict buttons."""
import math
from html import escape
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QSize
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QFont, QTextDocument
from PySide6.QtWidgets import QWidget, QPushButton, QBoxLayout, QFrame, QScrollArea
from ..presentation.wording_vi import STATUS_TEXT
from .icons import icon
from .character_animation import CharacterAnimation
from .card_feedback import CardFeedback
from .widgets import InlineClue, CardFadeEffect


class VerdictButton(QPushButton):
    """Cozy tactile 3D keycap for Innocent / Criminal verdicts."""

    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        innocent = self.objectName() == 'innocent'
        if innocent:
            border_c, lip_c, face_c, hover_c, hi_c = (
                '#184D33', '#1E6E47', '#2BA368', '#24915B', '#7CE2AE',
            )
        else:
            border_c, lip_c, face_c, hover_c, hi_c = (
                '#6E212B', '#9E303D', '#DE5260', '#CC4350', '#FBA3AC',
            )

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        pressed = self.isDown() and self.isEnabled()
        hovered = (self.underMouse() or self.hasFocus()) and self.isEnabled()
        if not self.isEnabled():
            p.setOpacity(0.58)

        rad = min(7.5, self.height() * 0.24)
        box = QRectF(self.rect()).adjusted(0.8, 0.8 + (1.8 if pressed else 0.0), -0.8, -0.8)
        lip_h = 1.0 if pressed else max(2.2, self.height() * 0.09)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(border_c))
        p.drawRoundedRect(box, rad, rad)

        inner = box.adjusted(1.4, 1.4, -1.4, -1.4)
        p.setBrush(QColor(lip_c))
        p.drawRoundedRect(inner, max(2.0, rad - 1.2), max(2.0, rad - 1.2))

        face = inner.adjusted(0.0, 0.0, 0.0, -lip_h)
        p.setBrush(QColor(hover_c if hovered else face_c))
        p.drawRoundedRect(face, max(2.0, rad - 1.2), max(2.0, rad - 1.2))

        hi_col = QColor(hi_c)
        hi_col.setAlpha(135)
        p.setPen(QPen(hi_col, 1.0))
        p.drawLine(QPointF(face.left() + rad * 0.7, face.top() + 1.1), QPointF(face.right() - rad * 0.7, face.top() + 1.1))

        font = QFont('Segoe UI')
        font.setWeight(QFont.Weight.Bold)
        fpx = max(10, round(self.height() * 0.39))
        label_txt = self.text().strip()
        show_ico = face.width() >= 72.0
        ico_sz = max(10.0, round(self.height() * 0.35)) if show_ico else 0.0
        gap = 4.5 if show_ico else 0.0
        while fpx > 9:
            font.setPixelSize(fpx)
            p.setFont(font)
            if ico_sz + gap + p.fontMetrics().horizontalAdvance(label_txt) <= face.width() - 8.0:
                break
            fpx -= 1
        font.setPixelSize(fpx)
        p.setFont(font)

        draw_txt = p.fontMetrics().elidedText(
            label_txt, Qt.TextElideMode.ElideRight, max(20, int(face.width() - ico_sz - gap - 6.0))
        )
        tw = p.fontMetrics().horizontalAdvance(draw_txt)
        total_w = ico_sz + gap + tw
        sx = face.center().x() - total_w * 0.5
        cy = face.center().y()

        ink = QColor('#FFFDF9' if self.isEnabled() else '#E2DDD5')
        if show_ico:
            p.setPen(QPen(ink, max(1.8, ico_sz * 0.16), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            if innocent:
                chk = QPainterPath()
                chk.moveTo(sx + ico_sz * 0.12, cy + ico_sz * 0.04)
                chk.lineTo(sx + ico_sz * 0.40, cy + ico_sz * 0.32)
                chk.lineTo(sx + ico_sz * 0.88, cy - ico_sz * 0.26)
                p.drawPath(chk)
            else:
                pad = ico_sz * 0.18
                p.drawLine(QPointF(sx + pad, cy - ico_sz * 0.32), QPointF(sx + ico_sz - pad, cy + ico_sz * 0.32))
                p.drawLine(QPointF(sx + ico_sz - pad, cy - ico_sz * 0.32), QPointF(sx + pad, cy + ico_sz * 0.32))

        p.setPen(ink)
        p.drawText(
            QRectF(sx + ico_sz + gap, face.top(), tw + 4, face.height()),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            draw_txt,
        )


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
        self.region_colors = ()
        self.name_color = None
        self.motion = True
        self.pixel_style = True
        self.feedback = CardFeedback()
        self.fade_effect = CardFadeEffect(self)
        self.fade_effect.setOpacity(1.0)
        self.setGraphicsEffect(self.fade_effect)
        self.expression_frames = ()
        self.silhouette_frames = ()
        self.expression = CharacterAnimation(status)
        self.expression.elapsed = 0.5 + (character.portrait * 0.731) % 3.5
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
            'QScrollBar::handle:vertical {background:#D1C4B0;border-radius:2px;}'
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
        s = max(0.52, min(1.65, self.height() / 200.0))
        rect = QRectF(4, 3, self.width() - 8, self.height() - 7)
        panel_w = max(50.0, min(rect.width() * 0.375, rect.height() * 0.90))
        panel = QRectF(rect.left(), rect.top(), panel_w, rect.height())
        pad = max(5.0, round(10 * s))
        text_left = panel.right() + max(8.0, round(14 * s))
        content = QRectF(text_left, rect.top(), max(32.0, rect.right() - text_left - pad), rect.height())
        return rect, panel, content

    def paper_geometry(self, content, scale):
        header_h = max(33.0, round(66 * scale)) if self.height() < 168 else max(39.0, round(70 * scale))
        top = content.y() + header_h
        bottom = content.bottom() - max(5.0, round(8 * scale))
        return QRectF(content.x(), top, content.width(), max(22.0, bottom - top))

    def place_actions(self):
        rect, panel_rect, content = self.content_geometry()
        s = max(0.58, min(1.65, self.height() / 200.0))
        show_actions = self.is_selected and not self.status
        ax = math.floor(content.left())
        aw = max(48, math.floor(content.right()) - ax)
        gap = max(4, round(6 * s))
        self.verdict_layout.setSpacing(gap)
        compact = aw < max(138, round(170 * s))
        self.verdict_layout.setDirection(
            QBoxLayout.Direction.TopToBottom if compact else QBoxLayout.Direction.LeftToRight
        )
        btn_h = max(24, round(35 * s))
        action_h = 2 * btn_h + gap if compact else btn_h
        ay = max(round(rect.y() + 44 * s), math.floor(rect.bottom() - max(4, round(8 * s))) - action_h)
        self.actions.setGeometry(ax, ay, aw, action_h)
        self.actions.setVisible(show_actions)
        for button in self.verdict_buttons.values():
            button.setFixedHeight(btn_h)

        if self.clue:
            raw_html = self.active_html if self.source and self.active_html else escape(self.clue)
            html = f'<div style="line-height:130%;">{raw_html}</div>'
            self.clue_text.active = self.source
            if self.clue_text.text() != html:
                self.clue_text.setText(html)

            paper = self.paper_geometry(content, s)
            x0, y0 = math.ceil(paper.left()), math.ceil(paper.top())
            w0 = max(16, math.floor(paper.right()) - x0)
            h0 = max(14, math.floor(paper.bottom()) - y0)
            self.note_scroll.setGeometry(x0, y0, w0, h0)
            text_width = max(16, w0 - 5)

            max_px = max(12, round(15.0 * s)) if rect.width() < 260 else max(15, round(18.5 * s))
            min_px = (9 if self.height() < 165 else 10) if rect.width() < 260 else max(11, round(12.0 * s))
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
                if math.ceil(probe.size().height()) + 3 <= h0:
                    font_size = cand
                    break

            self.clue_text.setStyleSheet(
                f'font-family:"Segoe UI";font-size:{font_size}px;font-weight:500;'
                f'background:transparent;color:#1D2D3E;'
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
            needed = math.ceil(doc.size().height()) + 3
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
        radius = 10.0
        rect, panel_rect, content = self.content_geometry()
        s = max(0.58, min(1.65, self.height() / 200.0))

        # Soft harbor shadow beneath card (stronger when selected/enlarged)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(14, 32, 52, 78 if self.is_selected else 52))
        sh_path = QPainterPath()
        sh_path.addRoundedRect(rect.translated(0, 3.2 if self.is_selected else 2.4), radius, radius)
        p.drawPath(sh_path)

        card_path = QPainterPath()
        card_path.addRoundedRect(rect, radius, radius)

        paper = {'INNOCENT': t.card_innocent, 'CRIMINAL': t.card_criminal}.get(self.status, t.card_unknown)
        p.fillPath(card_path, QColor(paper))

        p.save()
        p.setClipPath(card_path)
        p.setClipRect(panel_rect, Qt.ClipOperation.IntersectClip)
        panel_color = {
            'INNOCENT': '#CDEBD8',
            'CRIMINAL': '#F5CFCB',
        }.get(self.status, '#CEE2EC' if self.is_selected else '#DFE8EB')
        p.fillRect(panel_rect, QColor(panel_color))

        silhouette = (not self.status and not self.is_selected)
        frame = self.expression.frame if self.motion else {None: 0, 'INNOCENT': 4, 'CRIMINAL': 6}[self.status]
        blink = self.expression.blink_amount if self.motion else 0.0

        side = min(panel_rect.width() * 1.06, panel_rect.height())
        dest = QRectF(
            panel_rect.center().x() - side / 2,
            panel_rect.center().y() - side * 0.53,
            side,
            side * 1.5,
        )

        frames = self.silhouette_frames if silhouette else self.expression_frames
        sprite = frames[0 if silhouette else frame] if frames else self.portrait
        crop = QRectF(sprite.width() * 0.16, 0.0, sprite.width() * 0.68, sprite.height())
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        p.drawPixmap(dest, sprite, crop)
        if blink > 0.02 and frames:
            p.setOpacity(blink)
            p.drawPixmap(dest, frames[1 if silhouette else self.expression.blink_frame], crop)
        p.setOpacity(1.0)

        if self.status == 'CRIMINAL':
            progress = self.expression.bars_progress if self.motion else 1.0
            top = panel_rect.top() - (1.0 - progress) * panel_rect.height()
            bar_width = max(3.0, panel_rect.width() * 0.035)
            for fraction in (0.18, 0.39, 0.61, 0.82):
                x = panel_rect.left() + panel_rect.width() * fraction
                p.fillRect(QRectF(x, top, bar_width, panel_rect.height()), QColor('#34494E'))
                p.fillRect(QRectF(x, top, bar_width * 0.32, panel_rect.height()), QColor('#A9BBB2'))
            for fraction in (0.17, 0.86):
                p.fillRect(
                    QRectF(panel_rect.left(), top + panel_rect.height() * fraction, panel_rect.width(), bar_width),
                    QColor('#465A5A'),
                )
        p.restore()

        # Subtle vertical divider between portrait panel & note content
        p.setPen(QPen(QColor(30, 52, 72, 22), 1.0))
        p.drawLine(QPointF(panel_rect.right(), rect.top() + 2), QPointF(panel_rect.right(), rect.bottom() - 2))

        if self.props and not self.clue and not self.is_selected:
            pad = max(6.0, round(9 * s))
            space = self.paper_geometry(content, s)
            scale = min(space.width() * 0.85 / self.props.width(), (space.height() - pad) / self.props.height())
            width, height = self.props.width() * scale, self.props.height() * scale
            dest = QRectF(content.right() - width, rect.bottom() - pad - height, width, height)
            p.save()
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
            p.drawPixmap(dest, self.props, QRectF(self.props.rect()))
            p.restore()

        # Top-left coordinate pill (A1..E5)
        chip_pad = max(6.0, round(8 * s))
        chip_h = max(19.0, round(24 * s))
        chip_w = max(30.0, round(38 * s))
        chip = QRectF(rect.x() + chip_pad, rect.y() + chip_pad, chip_w, chip_h)
        chip_bg = (
            '#279B60' if self.status == 'INNOCENT'
            else '#D84856' if self.status == 'CRIMINAL'
            else '#1E5B88' if self.is_selected
            else '#6E8BA4'
        )
        p.setBrush(QColor(chip_bg))
        p.setPen(QPen(QColor(255, 255, 255, 90), 1.0))
        p.drawRoundedRect(chip, 5.5, 5.5)
        f_chip = QFont('Segoe UI')
        f_chip.setPixelSize(max(11, round(13.0 * s)))
        f_chip.setWeight(QFont.Weight.Bold)
        p.setFont(f_chip)
        p.setPen(QColor('#FFFFFF'))
        p.drawText(chip, Qt.AlignmentFlag.AlignCenter, self.character.cell)

        # Top-right rounded status badge when solved
        compact_h = self.height() < 168
        badge_reserved = 0.0
        badge_bottom = 0.0
        if self.status:
            bsz = 17.0 if compact_h else max(20.0, round(26 * s))
            bpad = 5.0 if compact_h else max(7.0, round(10 * s))
            badge = QRectF(rect.right() - bsz - bpad, rect.y() + bpad, bsz, bsz)
            badge_bottom = badge.bottom()
            is_inn = self.status == 'INNOCENT'
            p.setBrush(QColor('#2BA368' if is_inn else '#DE5260'))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(badge, 5.5 if compact_h else 6.5, 5.5 if compact_h else 6.5)
            symbol = icon('check' if is_inn else 'cross', '#FFFFFF')
            symbol.paint(p, badge.adjusted(2, 2, -2, -2).toRect())
            badge_reserved = bsz + round(6 * s)

        # Character name, profession, and hairline divider
        tx = content.x()
        tw = max(24.0, content.width() - badge_reserved)
        name_size = max(12 if compact_h else 14, round(22.0 * s))
        name_color = self.name_color or '#122436'
        f_name = QFont('Segoe UI')
        f_name.setWeight(QFont.Weight.ExtraBold)
        while name_size > 10:
            f_name.setPixelSize(name_size)
            p.setFont(f_name)
            if p.fontMetrics().horizontalAdvance(self.character.name) <= tw - 2.0:
                break
            name_size -= 1
        f_name.setPixelSize(name_size)
        p.setFont(f_name)
        p.setPen(QColor(name_color))
        name_y = rect.y() + (max(3.5, round(6.5 * s)) if compact_h else max(6.0, round(10 * s)))
        name_h = max(float(p.fontMetrics().height() + 2), round((24 if compact_h else 30) * s))
        name_str = p.fontMetrics().elidedText(self.character.name, Qt.TextElideMode.ElideRight, max(20, int(tw)))
        p.drawText(
            QRectF(tx, name_y, tw + 2.0, name_h),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextDontClip,
            name_str,
        )

        prof_y = rect.y() + (max(21.0, round(33 * s)) if compact_h else max(25.0, round(42 * s)))
        prof_reserve = badge_reserved if (self.status and prof_y < badge_bottom) else 1.0
        prof_w = max(24.0, content.width() - prof_reserve)
        prof_size = max(9 if compact_h else 11, round(13.8 * s))
        f_prof = QFont('Segoe UI')
        f_prof.setWeight(QFont.Weight.DemiBold)
        while prof_size > 7:
            f_prof.setPixelSize(prof_size)
            p.setFont(f_prof)
            if p.fontMetrics().horizontalAdvance(self.character.profession) <= prof_w - 2.0:
                break
            prof_size -= 1
        f_prof.setPixelSize(prof_size)
        p.setFont(f_prof)
        p.setPen(QColor('#596D82'))
        prof_h = max(float(p.fontMetrics().height() + 2), round((18 if compact_h else 21) * s))
        prof_str = p.fontMetrics().elidedText(self.character.profession, Qt.TextElideMode.ElideRight, max(20, int(prof_w)))
        p.drawText(
            QRectF(tx, prof_y, prof_w + 2.0, prof_h),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextDontClip,
            prof_str,
        )

        div_y = rect.y() + (max(31.0, round(58 * s)) if compact_h else max(38.0, round(66 * s)))
        p.setPen(QPen(QColor('#E7DFD2'), max(1.0, 1.15 * min(1.3, s))))
        p.drawLine(QPointF(tx, div_y), QPointF(content.right(), div_y))

        # Card rim & semantic clue region highlight borders
        colors = self.region_colors
        p.setClipping(False)
        p.setBrush(Qt.BrushStyle.NoBrush)
        status_rim = {'INNOCENT': '#429B6D', 'CRIMINAL': '#CF5B65'}.get(self.status)
        if self.is_selected:
            p.setPen(QPen(QColor(status_rim or t.selected), 4.2))
            p.drawPath(card_path)
        elif colors:
            for i, color in enumerate(colors):
                p.setPen(QPen(QColor(color), 6.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
                p.drawPath(card_path if len(colors) == 1 else card_path.trimmed(i / len(colors), (i + 1) / len(colors)))
        elif self.anchor:
            p.setPen(QPen(QColor(t.anchor), 3.4))
            p.drawPath(card_path)
        else:
            p.setPen(QPen(QColor(status_rim or '#C6B9A5'), 2.2))
            p.drawPath(card_path)
