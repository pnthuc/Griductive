"""Desktop cards — Exact Alto's Odyssey x Reigns Lineless Flat-Vector UI."""
import math
from html import escape
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QSize
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QFont, QTextDocument
from PySide6.QtWidgets import QWidget, QPushButton, QBoxLayout, QFrame, QScrollArea
from ..presentation.wording_vi import STATUS_TEXT
from .icons import icon
from .portraits import portrait_svg_renderer, profession_renderer
from .character_animation import CharacterAnimation
from .card_feedback import CardFeedback
from .widgets import InlineClue, CardFadeEffect


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
        self.prop_category = 'detective'
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

        # Flush Reigns-style 50/50 bottom split verdict bar
        self.actions = QWidget(self)
        self.actions.setObjectName('verdictActions')
        self.actions.setStyleSheet('QWidget#verdictActions {background:transparent;border:0;}')
        self.verdict_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self.actions)
        self.verdict_layout.setContentsMargins(0, 0, 0, 0)
        self.verdict_layout.setSpacing(0)
        self.verdict_buttons = {}
        for title in ('Innocent', 'Criminal'):
            w = QPushButton(' ' + STATUS_TEXT[title.upper()])
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
        ax = math.floor(panel_rect.right())
        aw = max(48, math.ceil(rect.right() - 2) - ax)
        compact = aw < 138
        self.verdict_layout.setDirection(
            QBoxLayout.Direction.TopToBottom if compact else QBoxLayout.Direction.LeftToRight
        )
        btn_h = max(25, round(44 * s))
        action_h = 2 * btn_h if compact else btn_h
        ay = max(round(rect.y() + 44 * s), math.ceil(rect.bottom() - 2) - action_h)
        self.actions.setGeometry(ax, ay, aw, action_h)
        self.actions.setVisible(show_actions)
        font_px = max(11, round(15 * s))
        for name, w in self.verdict_buttons.items():
            w.setFixedHeight(btn_h)
            w.setIconSize(QSize(max(13, round(18 * s)), max(13, round(18 * s))))
            is_inn = name == 'Innocent'
            bg = '#45CF80' if is_inn else '#F9616E'
            hov = '#37BF71' if is_inn else '#EB4E5C'
            r_br = '0px' if (is_inn and not compact) else '10px'
            w.setStyleSheet(
                f'QPushButton {{background:{bg};color:#FFFFFF;font-size:{font_px}px;font-weight:700;'
                f'border:none;padding:0 6px;border-radius:0px;border-bottom-right-radius:{r_br};}}'
                f'QPushButton:hover {{background:{hov};}}'
            )
            w.setIcon(icon('check' if is_inn else 'cross', '#FFFFFF'))

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

    @staticmethod
    def _dome_arch_path(box: QRectF) -> QPainterPath:
        """Continuous semicircular dome top extending flush to the bottom edge of the card."""
        path = QPainterPath()
        r_top = min(box.width() * 0.5, box.height() * 0.54)
        if abs(r_top * 2.0 - box.width()) < 0.5:
            # Pure single 180-degree semicircle — zero two-arc midpoint seam!
            path.moveTo(box.right(), box.bottom())
            path.lineTo(box.right(), box.top() + r_top)
            path.arcTo(QRectF(box.left(), box.top(), box.width(), box.width()), 0, 180)
            path.lineTo(box.left(), box.bottom())
            path.closeSubpath()
            return path
        path.moveTo(box.left(), box.bottom())
        path.lineTo(box.left(), box.top() + r_top)
        path.arcTo(QRectF(box.left(), box.top(), 2 * r_top, 2 * r_top), 180, -90)
        path.lineTo(box.right() - r_top, box.top())
        path.arcTo(QRectF(box.right() - 2 * r_top, box.top(), 2 * r_top, 2 * r_top), 90, -90)
        path.lineTo(box.right(), box.bottom())
        path.closeSubpath()
        return path

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        t = self.theme
        radius = 12.0
        rect, panel_rect, content = self.content_geometry()
        s = max(0.58, min(1.65, self.height() / 200.))

        # Crisp flat-vector sky shadow under card
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(12, 58, 118, 44))
        p.drawRoundedRect(rect.translated(0, 3.5), radius, radius)

        card_path = QPainterPath()
        card_path.addRoundedRect(rect, radius, radius)

        # Render card surface + left panel + dome arch + TRUE 4K/8K VECTOR SVG portrait
        # at exact 1:1 physical device pixel coordinates (zero fractional DPI blur!)
        dpr = max(1.0, p.deviceTransform().m11(), self.devicePixelRatioF())
        w_log = max(1.0, float(self.width()))
        h_log = max(1.0, float(self.height()))
        bw = max(1, round(w_log * dpr))
        bh = max(1, round(h_log * dpr))
        sx, sy = bw / w_log, bh / h_log

        card_buf = QImage(bw, bh, QImage.Format.Format_ARGB32_Premultiplied)
        card_buf.fill(Qt.GlobalColor.transparent)

        cb = QPainter(card_buf)
        cb.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        cb.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        cb.scale(sx, sy)
        cb.setPen(Qt.PenStyle.NoPen)
        cb.setBrush(QColor('#FFFFFF'))
        cb.drawPath(card_path)

        # Left 36.5% Full-Height Tinted Panel + Semicircular Dome Arch
        if self.status == 'INNOCENT':
            panel_bg, arch_bg = '#DCF9E8', '#2CC26B'
        elif self.status == 'CRIMINAL':
            panel_bg, arch_bg = '#FFE4E8', '#EE505E'
        elif self.is_selected:
            panel_bg, arch_bg = '#DCEBFE', '#99C2F6'
        else:
            panel_bg, arch_bg = None, '#D6E9FA'

        cb.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
        if panel_bg:
            cb.setBrush(QColor(panel_bg))
            cb.drawRect(panel_rect)

        inset_x = max(5., round(8.5 * s))
        inset_top = max(8., round(13 * s))
        arch_box = QRectF(
            panel_rect.left() + inset_x,
            panel_rect.top() + inset_top,
            max(0., panel_rect.width() - 2 * inset_x),
            max(0., panel_rect.height() - inset_top),
        )

        arch_buf = QImage(bw, bh, QImage.Format.Format_ARGB32_Premultiplied)
        arch_buf.fill(Qt.GlobalColor.transparent)
        ab = QPainter(arch_buf)
        ab.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        ab.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        ab.scale(sx, sy)
        ab.setPen(Qt.PenStyle.NoPen)
        ab.setBrush(QColor(arch_bg))
        ab.drawPath(self._dome_arch_path(arch_box))

        silhouette = (not self.status and not self.is_selected)
        frame = self.expression.frame if self.motion else {None: 0, 'INNOCENT': 4, 'CRIMINAL': 6}[self.status]
        blink = self.expression.blink_amount if self.motion else 0.

        ab.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
        side = min(arch_box.height(), arch_box.width() * 1.18)
        px = arch_box.center().x() - side / 2.0
        dest = QRectF(px, arch_box.bottom() - side, side, side)

        pid = self.character.portrait
        portrait_svg_renderer(pid, frame, silhouette).render(ab, dest)
        if blink > 0.02:
            ab.setOpacity(blink)
            portrait_svg_renderer(pid, self.expression.blink_frame, silhouette).render(ab, dest)
        ab.end()

        cb.drawImage(QRectF(0, 0, w_log, h_log), arch_buf)
        cb.end()

        p.drawImage(QRectF(0, 0, w_log, h_log), card_buf)

        # Subtle monochrome vector profession emblem on unopened, unselected cards (scaled generously!)
        if not self.clue and not self.is_selected:
            p.save()
            p.setOpacity(0.92)
            icon_sz = max(36., min(content.width() * 0.42, rect.height() * 0.42, 112. * s))
            pad = max(8., round(13 * s))
            icon_rect = QRectF(
                rect.right() - icon_sz - pad,
                rect.bottom() - icon_sz - pad,
                icon_sz,
                icon_sz,
            )
            profession_renderer(self.prop_category, '#C4DCF5').render(p, icon_rect)
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
        r_chip = max(6., 7.5 * min(1.3, s))
        p.drawRoundedRect(chip, r_chip, r_chip)
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
            p.setBrush(QColor('#34C772' if is_inn else '#F45866'))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(badge)
            mark_pen = QPen(QColor('#FFFFFF'), max(2.0, 2.4 * s))
            mark_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            mark_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            p.setPen(mark_pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            cx, cy = badge.center().x(), badge.center().y()
            if is_inn:
                chk = QPainterPath()
                chk.moveTo(QPointF(cx - bsz * 0.22, cy + bsz * 0.01))
                chk.lineTo(QPointF(cx - bsz * 0.05, cy + bsz * 0.19))
                chk.lineTo(QPointF(cx + bsz * 0.24, cy - bsz * 0.16))
                p.drawPath(chk)
            else:
                d = bsz * 0.18
                p.drawLine(QPointF(cx - d, cy - d), QPointF(cx + d, cy + d))
                p.drawLine(QPointF(cx + d, cy - d), QPointF(cx - d, cy + d))
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
        if self.is_selected:
            p.setPen(QPen(QColor(t.selected), 3.5))
            p.drawRoundedRect(rect, radius, radius)
        elif colors:
            for i, color in enumerate(colors):
                p.setPen(QPen(QColor(color), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
                p.drawPath(card_path if len(colors) == 1 else card_path.trimmed(i / len(colors), (i + 1) / len(colors)))
        elif self.anchor:
            p.setPen(QPen(QColor(t.anchor), 3.5))
            p.drawRoundedRect(rect, radius, radius)
        else:
            rim = '#B7ECCE' if self.status == 'INNOCENT' else '#FCD2D7' if self.status == 'CRIMINAL' else '#D3E5F8'
            p.setPen(QPen(QColor(rim), 1.4))
            p.drawRoundedRect(rect, radius, radius)
