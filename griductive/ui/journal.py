"""Cozy Harbor Solver Journal: floating detective notebook for DPLL trace inspection."""
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QRectF, QPointF
from PySide6.QtGui import QColor, QLinearGradient, QPalette, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QDockWidget, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QToolButton, QVBoxLayout, QWidget,
)
from .icons import icon
from ..presentation.wording_vi import STATUS_TEXT
from .widgets import label, PixelHintButton


class LedgerPaper(QWidget):
    """Warm cream notebook paper with subtle ruled lines."""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor('#FBF5E8'))
        painter.setPen(QColor('#EFE4CE'))
        for y in range(22, self.height(), 24):
            painter.drawLine(0, y, self.width(), y)


class MiniAvatar(QWidget):
    """Rounded portrait frame inside each journal step."""

    def __init__(self, portrait, criminal: bool, parent=None):
        super().__init__(parent)
        self.portrait = portrait
        self.criminal = criminal
        self.setFixedSize(46, 50)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        box = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        bg = QColor('#FADAD7') if self.criminal else QColor('#D9F2E4')
        rim = QColor('#E09B96') if self.criminal else QColor('#8BD1AB')
        p.setBrush(bg)
        p.setPen(QPen(rim, 1.3))
        p.drawRoundedRect(box, 8.0, 8.0)

        p.save()
        clip = QPainterPath()
        clip.addRoundedRect(box.adjusted(1.5, 1.5, -1.5, -1.5), 6.5, 6.5)
        p.setClipPath(clip)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        scaled = self.portrait.scaled(
            42, 48, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        p.drawPixmap(
            QPointF((self.width() - scaled.width()) * 0.5, box.bottom() - scaled.height() + 2),
            scaled,
        )
        p.restore()


class JournalEntry(QFrame):
    """One accepted verdict card inside the Cozy Harbor Solver Notebook."""

    def __init__(self, entry, name, portrait, clue, variables, theme, clue_names=None):
        super().__init__()
        self.setObjectName('journalEntry')
        self.entry = entry
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(13, 12, 13, 11)
        layout.setSpacing(8)

        criminal = entry['verdict'] == 'CRIMINAL'
        verdict_color = '#C93B4B' if criminal else '#1E8A52'

        heading = QHBoxLayout()
        heading.setSpacing(10)

        number = label(f"#{entry['step']:02d}", 'journalNumber')
        number.setFixedWidth(30)
        heading.addWidget(number, 0, Qt.AlignmentFlag.AlignVCenter)

        figure = MiniAvatar(portrait, criminal)
        heading.addWidget(figure)

        identity = QVBoxLayout()
        identity.setSpacing(3)
        name_row = QHBoxLayout()
        name_row.setSpacing(7)
        name_row.addWidget(label(name, 'journalName'))
        cell_lbl = label(entry['cell'], 'journalCell')
        cell_lbl.setWordWrap(False)
        name_row.addWidget(cell_lbl)
        name_row.addStretch()
        identity.addLayout(name_row)

        status_row = QHBoxLayout()
        status_row.setSpacing(5)
        mark = QLabel()
        mark.setFixedSize(15, 15)
        mark.setPixmap(icon('cross' if criminal else 'check', verdict_color).pixmap(15, 15))
        status_row.addWidget(mark)
        verdict = label(STATUS_TEXT[entry['verdict']], 'journalVerdict')
        verdict.setStyleSheet(f'color:{verdict_color};')
        status_row.addWidget(verdict)
        status_row.addStretch()
        identity.addLayout(status_row)
        heading.addLayout(identity, 1)
        layout.addLayout(heading)

        summary = QHBoxLayout()
        summary.addWidget(label(f'Đã mở lời khai của {name}', 'journalMuted'), 1)
        self.details_button = QToolButton()
        self.details_button.setObjectName('journalDetailsButton')
        self.details_button.setText('Chi tiết')
        self.details_button.setCheckable(True)
        self.details_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.details_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.details_button.setArrowType(Qt.ArrowType.DownArrow)
        self.details_button.setAccessibleName(f"Chi tiết bước {entry['step']}: {name}")
        summary.addWidget(self.details_button)
        layout.addLayout(summary)

        self.details = QFrame()
        self.details.setObjectName('journalDetails')
        details = QVBoxLayout(self.details)
        details.setContentsMargins(0, 10, 0, 2)
        details.setSpacing(7)
        details.addWidget(label(f"Lời khai của {name} ({entry['cell']})", 'journalCaption'))
        details.addWidget(label(clue, 'journalClue'))
        details.addWidget(label('Lời khai có trước bước này', 'journalCaption'))
        details.addWidget(label('\n'.join((clue_names or {}).get(cid, cid) for cid in entry['active_clues']), 'journalClue'))
        details.addWidget(label('Kiểm chứng DPLL', 'journalCaption'))
        for query in entry['queries']:
            assumptions = [
                f"{variables.get(abs(literal), str(abs(literal)))} là "
                f"{STATUS_TEXT['CRIMINAL' if literal > 0 else 'INNOCENT']}"
                for literal in query['assumptions']
            ]
            condition = 'Giả sử ' + ', '.join(assumptions) if assumptions else 'Dữ kiện đã mở'
            result = {'SAT': 'Nhất quán (SAT)', 'UNSAT': 'Mâu thuẫn (UNSAT)'}[query['result']]
            details.addWidget(label(f'{condition}\n→ {result}', 'journalClue'))
        details.addWidget(label(
            f"KB trước bước này: {entry['primary_variables']} biến chính, "
            f"{entry['auxiliary_variables']} biến phụ, {entry['clauses']} mệnh đề.",
            'journalMuted',
        ))
        layout.addWidget(self.details)
        self.details.hide()
        self.details_button.toggled.connect(self.show_details)

    def show_details(self, checked):
        self.details.setVisible(checked)
        self.details_button.setArrowType(Qt.ArrowType.UpArrow if checked else Qt.ArrowType.DownArrow)
        self.fit_height()

    def fit_height(self):
        self.layout().invalidate()
        self.setFixedHeight(self.layout().totalHeightForWidth(self.width()))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_height()


class NotebookShell(QFrame):
    """Rounded Cozy Harbor notebook container with navy header band & cream body."""

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        box = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)

        # Subtle harbor drop shadow
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(12, 24, 38, 85))
        p.drawRoundedRect(box.translated(0, 3.0), 13.0, 13.0)

        # Harbor navy border + cream notebook fill
        p.setBrush(QColor('#243B52'))
        p.drawRoundedRect(box, 13.0, 13.0)

        inner = box.adjusted(2.0, 2.0, -2.0, -3.5)
        p.setBrush(QColor('#F7EEDB'))
        p.drawRoundedRect(inner, 11.0, 11.0)

        # Deep Harbor Navy header cap + warm gold trim line
        p.save()
        clip = QPainterPath()
        clip.addRoundedRect(inner, 11.0, 11.0)
        p.setClipPath(clip)
        p.fillRect(QRectF(inner.left(), inner.top(), inner.width(), 52.0), QColor('#1F364D'))
        p.fillRect(QRectF(inner.left(), inner.top() + 50.0, inner.width(), 2.5), QColor('#E5A948'))
        p.restore()


class DockDuskWrap(QWidget):
    """Matches DeskSurface's coastal dusk gradient so the floating notebook blends seamlessly."""

    def paintEvent(self, event):
        p = QPainter(self)
        b = QRectF(self.rect())
        dusk = QLinearGradient(0, 0, 0, b.height())
        dusk.setColorAt(0.0, QColor(34, 42, 66))
        dusk.setColorAt(0.24, QColor(82, 62, 82))
        dusk.setColorAt(0.68, QColor(52, 68, 90))
        dusk.setColorAt(1.0, QColor(34, 58, 74))
        p.fillRect(b, dusk)


class SolverJournal(QDockWidget):
    run_requested = Signal()
    pause_requested = Signal()
    step_requested = Signal()
    export_requested = Signal()

    def __init__(self, theme, parent=None):
        super().__init__('Sổ tay suy luận', parent)
        self.setObjectName('solverDock')
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.setMinimumWidth(360)
        self.setMaximumWidth(460)
        self.setMinimumHeight(440)
        self.running = False
        self.complete = False
        self.entries = []

        # Hide native dock title bar and render an integrated notebook shell
        empty_title = QWidget(self)
        empty_title.setFixedHeight(0)
        self.setTitleBarWidget(empty_title)

        outer_wrap = DockDuskWrap()
        outer_wrap.setObjectName('journalOuter')
        outer_lay = QVBoxLayout(outer_wrap)
        outer_lay.setContentsMargins(4, 10, 22, 26)
        outer_lay.setSpacing(0)

        shell = NotebookShell()
        shell.setObjectName('journalShell')
        outer_lay.addWidget(shell, 1)
        self.setWidget(outer_wrap)

        layout = QVBoxLayout(shell)
        layout.setContentsMargins(15, 11, 15, 14)
        layout.setSpacing(10)

        # Integrated Navy Header Row inside shell
        title_row = QHBoxLayout()
        title_row.setContentsMargins(2, 0, 0, 8)
        title_lbl = label('Sổ tay suy luận', 'journalTitle')
        title_lbl.setWordWrap(False)
        title_row.addWidget(title_lbl, 1)

        self.close_button = QToolButton()
        self.close_button.setObjectName('journalClose')
        self.close_button.setAccessibleName('Đóng bảng Tự động giải')
        self.close_button.setToolTip('Đóng và tạm dừng')
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.setFixedSize(28, 28)
        self.close_button.clicked.connect(self.close)
        title_row.addWidget(self.close_button)
        layout.addLayout(title_row)

        self.case_title = label('', 'journalCaseSubtitle')
        layout.addWidget(self.case_title)

        # Primary solver buttons
        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.play_button = PixelHintButton('Chạy tự động', variant='emerald')
        self.play_button.setObjectName('journalPrimary')
        self.play_button.setIconSize(QSize(16, 16))
        self.play_button.clicked.connect(self.request_play)

        self.step_button = PixelHintButton('Bước tiếp', variant='cream')
        self.step_button.setObjectName('journalSecondary')
        self.step_button.setIconSize(QSize(16, 16))
        self.step_button.clicked.connect(self.step_requested.emit)

        self.play_button.setFixedHeight(38)
        self.step_button.setFixedHeight(38)
        controls.addWidget(self.play_button, 1)
        controls.addWidget(self.step_button, 1)
        layout.addLayout(controls)

        # Status & step counter strip
        progress = QHBoxLayout()
        self.status = label('Sẵn sàng', 'journalStatus')
        progress.addWidget(self.status, 1)
        self.count = label('0 bước', 'journalCountPill')
        self.count.setWordWrap(False)
        self.count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress.addWidget(self.count)
        layout.addLayout(progress)

        # Notebook scroll area
        self.scroll = QScrollArea()
        self.scroll.setObjectName('journalScroll')
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content = LedgerPaper()
        self.content.setObjectName('journalPaper')
        self.rows = QVBoxLayout(self.content)
        self.rows.setContentsMargins(9, 10, 9, 10)
        self.rows.setSpacing(9)
        self.rows.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Wrap empty message inside a QFrame layout to avoid HiDPI QSS QLabel clipping
        self.empty = QFrame()
        self.empty.setObjectName('journalEmptyFrame')
        empty_lay = QVBoxLayout(self.empty)
        empty_lay.setContentsMargins(14, 13, 14, 13)
        empty_lay.setSpacing(6)
        empty_title_lbl = label('Chưa có bước suy luận nào.', 'journalEmptyTitle')
        empty_desc_lbl = label(
            'Bấm Chạy tự động hoặc Bước tiếp để theo dõi bộ giải DPLL chứng minh từng nghi phạm.',
            'journalEmptyBody',
        )
        empty_lay.addWidget(empty_title_lbl)
        empty_lay.addWidget(empty_desc_lbl)
        self.rows.addWidget(self.empty)
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll, 1)

        self.latest_button = QPushButton('Đến bước mới nhất ↓')
        self.latest_button.setObjectName('journalQuiet')
        self.latest_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.latest_button.clicked.connect(self.scroll_to_latest)
        self.latest_button.hide()
        layout.addWidget(self.latest_button)
        self.scroll.verticalScrollBar().valueChanged.connect(self.update_latest_button)

        footer = QHBoxLayout()
        self.stats_button = QToolButton()
        self.stats_button.setObjectName('journalQuiet')
        self.stats_button.setText('Thông số KB')
        self.stats_button.setCheckable(True)
        self.stats_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stats = label('', 'journalStatsBox')
        self.stats.hide()
        self.stats_button.toggled.connect(self.stats.setVisible)
        footer.addWidget(self.stats_button)
        footer.addStretch()

        self.export_button = QPushButton('Xuất JSON')
        self.export_button.setObjectName('journalQuiet')
        self.export_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_button.setIconSize(QSize(15, 15))
        self.export_button.clicked.connect(self.export_requested.emit)
        footer.addWidget(self.export_button)
        layout.addLayout(footer)
        layout.addWidget(self.stats)

        self.set_theme(theme)
        self.reset('')

    def set_theme(self, theme):
        self.theme = theme
        self.setStyleSheet(f'''
QDockWidget#solverDock {{background:transparent;border:0;}}
QWidget#journalOuter {{background:transparent;border:0;}}
QFrame#journalShell {{background:transparent;border:0;}}
QDockWidget#solverDock QLabel {{
    border:0;
    background:transparent;
    color:{theme.text};
    font-family:"Segoe UI";
    font-size:13.5px;
}}
QDockWidget#solverDock QLabel#journalTitle {{
    font-family:"Segoe UI";
    font-size:17.5px;
    font-weight:800;
    color:#FFF8EA;
}}
QDockWidget#solverDock QLabel#journalCaseSubtitle {{
    color:#5C4B3B;
    font-size:12.5px;
    font-weight:700;
}}
QDockWidget#solverDock QLabel#journalName {{
    font-family:"Segoe UI";
    font-size:16px;
    font-weight:800;
    color:#142536;
}}
QDockWidget#solverDock QLabel#journalNumber {{
    font-size:12.5px;
    font-weight:800;
    color:#1E5B88;
}}
QDockWidget#solverDock QLabel#journalCell {{
    font-size:11px;
    font-weight:800;
    color:#FFFFFF;
    background:#2B4C6B;
    border-radius:5px;
    padding:1px 6px;
}}
QDockWidget#solverDock QLabel#journalVerdict {{
    font-size:12.5px;
    font-weight:700;
}}
QDockWidget#solverDock QLabel#journalMuted {{
    color:#64748B;
    font-size:12px;
}}
QDockWidget#solverDock QLabel#journalStatus {{
    font-size:12.5px;
    font-weight:700;
}}
QDockWidget#solverDock QLabel#journalCountPill {{
    font-size:11.5px;
    font-weight:700;
    color:#3A2E21;
    background:#EFE2C6;
    border:1px solid #D4BF98;
    border-radius:9px;
    padding:2px 9px;
}}
QDockWidget#solverDock QLabel#journalCaption {{
    font-size:12px;
    font-weight:800;
    color:#1E5B88;
}}
QDockWidget#solverDock QLabel#journalClue {{
    font-size:13px;
    color:#1E293B;
}}
QDockWidget#solverDock QLabel#journalStatsBox {{
    font-size:12px;
    font-weight:600;
    color:#3E3124;
    background:#EFE4CC;
    border:1px solid #D4C19E;
    border-radius:6px;
    padding:6px 8px;
}}
QFrame#journalEmptyFrame {{
    background:#FFFDF7;
    border:1.5px dashed #CBB899;
    border-radius:8px;
}}
QDockWidget#solverDock QLabel#journalEmptyTitle {{
    color:#2B2118;
    font-size:13.5px;
    font-weight:700;
}}
QDockWidget#solverDock QLabel#journalEmptyBody {{
    color:#5F5243;
    font-size:12.5px;
}}
QScrollArea#journalScroll {{
    background:#FBF5E8;
    border:1.5px solid #D5C3A5;
    border-radius:9px;
}}
QFrame#journalEntry {{
    background:#FFFDF8;
    border:1.5px solid #D5C2A3;
    border-bottom:3px solid #BDA682;
    border-radius:9px;
}}
QFrame#journalDetails {{
    background:transparent;
    border:0;
    border-top:1px solid #E8DEC9;
}}
QToolButton#journalClose {{
    background:rgba(255, 248, 232, 32);
    border:1px solid rgba(255, 248, 232, 55);
    border-radius:7px;
    padding:3px;
}}
QToolButton#journalClose:hover {{
    background:rgba(255, 232, 184, 72);
    border-color:#FFE29A;
}}
QToolButton#journalDetailsButton, QPushButton#journalQuiet, QToolButton#journalQuiet {{
    background:#FFF7E6;
    border:1.5px solid #C6B08E;
    border-bottom:2.5px solid #AD9572;
    border-radius:6px;
    color:#2B2118;
    font-size:12px;
    font-weight:700;
    padding:4px 9px;
}}
QToolButton#journalDetailsButton:hover, QPushButton#journalQuiet:hover, QToolButton#journalQuiet:hover {{
    background:#FFECC4;
    border-color:#C88E3B;
}}
QToolButton#journalDetailsButton:checked, QToolButton#journalQuiet:checked {{
    background:#FFE5AF;
    border-color:#C2872C;
    border-bottom:2px solid #A36E1E;
    color:#1E150C;
}}
QToolButton#journalDetailsButton:disabled, QPushButton#journalQuiet:disabled, QToolButton#journalQuiet:disabled {{
    background:#EFE8DA;
    color:#9C9284;
    border:1px solid #D8CEBE;
}}
QScrollArea#journalScroll QScrollBar:vertical {{width:6px;background:transparent;margin:4px 1px;}}
QScrollArea#journalScroll QScrollBar::handle:vertical {{background:#C9B79B;min-height:28px;border-radius:3px;}}
QScrollArea#journalScroll QScrollBar::add-line:vertical, QScrollArea#journalScroll QScrollBar::sub-line:vertical {{height:0;}}
QScrollArea#journalScroll QScrollBar::add-page:vertical, QScrollArea#journalScroll QScrollBar::sub-page:vertical {{background:transparent;}}
''')
        for widget in (self.scroll.viewport(), self.content):
            palette = widget.palette()
            palette.setColor(QPalette.ColorRole.Window, QColor('#FBF5E8'))
            palette.setColor(QPalette.ColorRole.Base, QColor('#FBF5E8'))
            widget.setPalette(palette)
            widget.setAutoFillBackground(True)
        self.close_button.setIcon(icon('cross', '#FFF8EA'))
        self.step_button.setIcon(icon('step', '#172A3C'))
        self.export_button.setIcon(icon('export', '#1E5B88'))
        self.set_running(self.running)

    def reset(self, title):
        for row in self.entries:
            self.rows.removeWidget(row)
            row.hide()
            row.deleteLater()
        self.entries.clear()
        self.complete = False
        self.case_title.setText(f'Hồ sơ: {title}' if title else '')
        self.empty.show()
        self.count.setText('0 bước')
        self.latest_button.hide()
        self.export_button.setEnabled(False)
        self.stats_button.setEnabled(False)
        self.stats_button.setChecked(False)
        self.stats.setText('')
        self.set_running(False)

    def request_play(self):
        if self.running:
            self.pause_requested.emit()
        else:
            self.run_requested.emit()

    def set_running(self, running):
        self.running = running
        self.play_button.variant = 'amber' if running else 'emerald'
        self.play_button.setText('Tạm dừng' if running else 'Chạy tiếp' if self.entries else 'Chạy tự động')
        self.play_button.setIcon(icon('pause' if running else 'play', '#2A1D11' if running else '#FFFFFF'))
        self.play_button.setEnabled(not self.complete)
        self.step_button.setEnabled(not running and not self.complete)
        message = 'Đang tự động giải…' if running else 'Đã tạm dừng' if self.entries else 'Sẵn sàng'
        self.set_message(
            '★ Đã hoàn thành màn chơi' if self.complete else message,
            'success' if self.complete else 'info',
        )

    def append_entry(self, entry, name, portrait, clue, variables, clue_names=None):
        bar = self.scroll.verticalScrollBar()
        follow = bar.value() >= bar.maximum() - 24
        self.empty.hide()
        row = JournalEntry(entry, name, portrait, clue, variables, self.theme, clue_names)
        self.rows.addWidget(row)
        self.entries.append(row)
        self.count.setText(f'{len(self.entries)} bước')
        self.export_button.setEnabled(True)
        self.stats_button.setEnabled(True)
        if not self.running:
            self.set_message('Đang xem từng bước')
            self.play_button.setText('Chạy tiếp')
        if follow:
            QTimer.singleShot(0, self.scroll_to_latest)
        else:
            self.latest_button.show()

    def scroll_to_latest(self):
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())
        self.latest_button.hide()

    def update_latest_button(self):
        bar = self.scroll.verticalScrollBar()
        if bar.value() >= bar.maximum() - 24:
            self.latest_button.hide()

    def set_complete(self):
        self.complete = True
        self.set_running(False)

    def set_message(self, message, tone='info'):
        color = {
            'info': '#1E5B88',
            'success': '#1E8A52',
            'warning': '#C93B4B',
        }[tone]
        self.status.setText(message)
        self.status.setStyleSheet(f'color:{color};')

    def closeEvent(self, event):
        self.pause_requested.emit()
        super().closeEvent(event)
