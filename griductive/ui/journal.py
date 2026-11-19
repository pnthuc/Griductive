"""The solver's journal view. It displays trace records without changing them."""
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QDockWidget, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QToolButton, QVBoxLayout, QWidget,
)
from .icons import icon
from ..presentation.wording_vi import STATUS_TEXT
from .widgets import label


class JournalEntry(QFrame):
    """One accepted verdict, with the original verification data underneath."""

    def __init__(self, entry, name, portrait, clue, variables, theme, clue_names=None):
        super().__init__()
        self.setObjectName('journalEntry')
        self.entry = entry
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 13, 14, 12)
        layout.setSpacing(9)

        heading = QHBoxLayout()
        heading.setSpacing(10)
        number = label(f"{entry['step']:02d}", 'journalNumber')
        number.setFixedWidth(26)
        heading.addWidget(number, 0, Qt.AlignmentFlag.AlignTop)
        figure = QLabel()
        figure.setFixedSize(44, 50)
        figure.setAlignment(Qt.AlignmentFlag.AlignCenter)
        figure.setPixmap(portrait.scaled(
            44, 50, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation))
        heading.addWidget(figure)
        identity = QVBoxLayout()
        identity.setSpacing(3)
        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name_row.addWidget(label(name, 'journalName'))
        name_row.addWidget(label(entry['cell'], 'journalCell'))
        name_row.addStretch()
        identity.addLayout(name_row)
        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        criminal = entry['verdict'] == 'CRIMINAL'
        color = theme.criminal if criminal else '#1E9E5A'
        mark = QLabel()
        mark.setFixedSize(16, 16)
        mark.setPixmap(icon('cross' if criminal else 'check', color).pixmap(16, 16))
        status_row.addWidget(mark)
        verdict = label(STATUS_TEXT[entry['verdict']], 'journalVerdict')
        verdict.setStyleSheet(f'color:{color};')
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
        self.details_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.details_button.setArrowType(Qt.ArrowType.DownArrow)
        self.details_button.setAccessibleName(f"Chi tiết bước {entry['step']}: {name}")
        summary.addWidget(self.details_button)
        layout.addLayout(summary)

        self.details = QFrame()
        self.details.setObjectName('journalDetails')
        details = QVBoxLayout(self.details)
        details.setContentsMargins(0, 11, 0, 0)
        details.setSpacing(8)
        details.addWidget(label(f"Lời khai của {name} ({entry['cell']})", 'journalCaption'))
        details.addWidget(label(clue, 'journalClue'))
        details.addWidget(label('Lời khai có trước bước này', 'journalCaption'))
        details.addWidget(label('\n'.join((clue_names or {}).get(cid, cid) for cid in entry['active_clues']), 'journalClue'))
        details.addWidget(label('Kiểm chứng', 'journalCaption'))
        for query in entry['queries']:
            assumptions = [
                f"{variables.get(abs(literal), str(abs(literal)))} là "
                f"{STATUS_TEXT['CRIMINAL' if literal > 0 else 'INNOCENT']}"
                for literal in query['assumptions']
            ]
            condition = 'Giả sử ' + ', '.join(assumptions) if assumptions else 'Dữ kiện đã mở'
            result = {'SAT': 'Nhất quán (SAT)', 'UNSAT': 'Mâu thuẫn (UNSAT)'}[query['result']]
            details.addWidget(label(f'{condition}\n{result}', 'journalClue'))
        details.addWidget(label(
            f"KB trước bước này: {entry['primary_variables']} biến chính, "
            f"{entry['auxiliary_variables']} biến phụ, {entry['clauses']} mệnh đề.",
            'journalMuted'))
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


class SolverJournal(QDockWidget):
    run_requested = Signal()
    pause_requested = Signal()
    step_requested = Signal()
    export_requested = Signal()

    def __init__(self, theme, parent=None):
        super().__init__('Tự động giải', parent)
        self.setObjectName('solverDock')
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.setMinimumWidth(360)
        self.setMaximumWidth(460)
        self.setMinimumHeight(440)
        self.running = False
        self.complete = False
        self.entries = []

        heading = QFrame()
        heading.setObjectName('journalHeading')
        heading.setToolTip('Kéo để di chuyển; nhấn đúp để tách hoặc ghim bảng.')
        title_row = QHBoxLayout(heading)
        title_row.setContentsMargins(17, 14, 12, 8)
        title_row.addWidget(label('Tự động giải', 'journalTitle'), 1)
        self.close_button = QToolButton()
        self.close_button.setObjectName('journalClose')
        self.close_button.setAccessibleName('Đóng nhật ký')
        self.close_button.setToolTip('Đóng và tạm dừng')
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.close)
        title_row.addWidget(self.close_button)
        self.setTitleBarWidget(heading)

        panel = QFrame()
        panel.setObjectName('journalPanel')
        self.setWidget(panel)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(17, 0, 17, 14)
        layout.setSpacing(12)
        self.case_title = label('', 'journalMuted')
        layout.addWidget(self.case_title)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.play_button = QPushButton('Chạy tự động')
        self.play_button.setObjectName('journalPrimary')
        self.play_button.setIconSize(QSize(18, 18))
        self.play_button.clicked.connect(self.request_play)
        self.step_button = QPushButton('Bước tiếp')
        self.step_button.setObjectName('journalSecondary')
        self.step_button.setIconSize(QSize(18, 18))
        self.step_button.clicked.connect(self.step_requested.emit)
        controls.addWidget(self.play_button, 1)
        controls.addWidget(self.step_button, 1)
        layout.addLayout(controls)

        progress = QHBoxLayout()
        self.status = label('Sẵn sàng', 'journalStatus')
        progress.addWidget(self.status, 1)
        self.count = label('0 bước', 'journalMuted')
        self.count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        progress.addWidget(self.count)
        layout.addLayout(progress)

        self.scroll = QScrollArea()
        self.scroll.setObjectName('journalScroll')
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content = QWidget()
        self.content.setObjectName('journalPaper')
        self.rows = QVBoxLayout(self.content)
        self.rows.setContentsMargins(9, 10, 9, 10)
        self.rows.setSpacing(10)
        self.rows.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.empty = label('Chưa có bước suy luận.\n\nChạy tự động hoặc chọn Bước tiếp để xem từng phán quyết.', 'journalEmpty')
        self.rows.addWidget(self.empty)
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll, 1)

        self.latest_button = QPushButton('Đến bước mới nhất ↓')
        self.latest_button.setObjectName('journalQuiet')
        self.latest_button.clicked.connect(self.scroll_to_latest)
        self.latest_button.hide()
        layout.addWidget(self.latest_button)
        self.scroll.verticalScrollBar().valueChanged.connect(self.update_latest_button)

        footer = QHBoxLayout()
        self.stats_button = QToolButton()
        self.stats_button.setObjectName('journalQuiet')
        self.stats_button.setText('Thông số KB')
        self.stats_button.setCheckable(True)
        self.stats = label('', 'journalMuted')
        self.stats.hide()
        self.stats_button.toggled.connect(self.stats.setVisible)
        footer.addWidget(self.stats_button)
        footer.addStretch()
        self.export_button = QPushButton('Xuất JSON')
        self.export_button.setObjectName('journalQuiet')
        self.export_button.setIconSize(QSize(16, 16))
        self.export_button.clicked.connect(self.export_requested.emit)
        footer.addWidget(self.export_button)
        layout.addLayout(footer)
        layout.addWidget(self.stats)
        self.set_theme(theme)
        self.reset('')

    def set_theme(self, theme):
        self.theme = theme
        self.setStyleSheet(f'''
QFrame#journalHeading {{background:#FFFFFF;border:1.5px solid #CBD5E1;border-bottom:1px solid #E2E8F0;border-top-left-radius:12px;border-top-right-radius:12px;}}
QFrame#journalPanel {{background:#FFFFFF;border:1.5px solid #CBD5E1;border-top:0;border-bottom-left-radius:12px;border-bottom-right-radius:12px;}}
QDockWidget#solverDock QLabel {{border:0;background:transparent;color:{theme.text};font-family:"Segoe UI";font-size:14px;}}
QDockWidget#solverDock QLabel#journalTitle {{font-family:"Segoe UI";font-size:20px;font-weight:800;color:{theme.text};}}
QDockWidget#solverDock QLabel#journalName {{font-family:"Segoe UI";font-size:18px;font-weight:700;}}
QDockWidget#solverDock QLabel#journalNumber {{font-size:14px;font-weight:700;color:{theme.primary};}}
QDockWidget#solverDock QLabel#journalCell {{font-size:11px;font-weight:700;color:#FFFFFF;background:#83A3C4;border-radius:2px;padding:1px 6px;}}
QDockWidget#solverDock QLabel#journalVerdict {{font-size:13px;font-weight:700;}}
QDockWidget#solverDock QLabel#journalMuted {{color:{theme.muted};font-size:12px;}}
QDockWidget#solverDock QLabel#journalStatus {{font-size:13px;font-weight:600;}}
QDockWidget#solverDock QLabel#journalCaption {{font-size:12px;font-weight:700;color:{theme.primary};}}
QDockWidget#solverDock QLabel#journalEmpty {{padding:22px 14px;color:{theme.muted};font-size:14px;}}
QScrollArea#journalScroll, QWidget#journalPaper {{background:#F1F5F9;border:0;border-radius:2px;}}
QFrame#journalEntry {{background:#FAF8F2;border:2px solid #C7BBA6;border-radius:2px;}}
QFrame#journalDetails {{background:transparent;border:0;border-top:1px solid #E2E8F0;}}
QPushButton#journalPrimary, QPushButton#journalSecondary {{font-size:13px;font-weight:700;border-radius:2px;padding:8px 10px;}}
QPushButton#journalPrimary {{background:{theme.primary};color:#FFFFFF;border:2px solid #243D67;border-bottom-width:4px;}}
QPushButton#journalPrimary:hover {{background:#1E40AF;}}
QPushButton#journalSecondary {{background:#FFFFFF;color:{theme.text};border:1.5px solid #CBD5E1;}}
QPushButton#journalSecondary:hover {{background:#F1F5F9;}}
QPushButton#journalPrimary:disabled, QPushButton#journalSecondary:disabled {{background:#E2E8F0;color:#94A3B8;border:1px solid #CBD5E1;}}
QToolButton#journalClose {{background:transparent;border:1px solid transparent;border-radius:2px;padding:3px;}}
QToolButton#journalClose:hover {{background:#F1F5F9;border-color:#CBD5E1;}}
QToolButton#journalDetailsButton, QPushButton#journalQuiet, QToolButton#journalQuiet {{background:transparent;border:1px solid transparent;border-radius:2px;color:{theme.primary};font-size:12px;font-weight:600;padding:4px 6px;}}
QToolButton#journalDetailsButton:hover, QPushButton#journalQuiet:hover, QToolButton#journalQuiet:hover {{background:#EFF6FF;border-color:#BFDBFE;}}
QToolButton#journalClose:focus, QToolButton#journalDetailsButton:focus, QToolButton#journalQuiet:focus, QToolButton#journalQuiet:focus {{border-color:{theme.selected};}}
QPushButton#journalPrimary:focus, QPushButton#journalSecondary:focus {{border-color:{theme.selected};}}
QScrollArea#journalScroll QScrollBar:vertical {{width:6px;background:transparent;margin:3px 0;}}
QScrollArea#journalScroll QScrollBar::handle:vertical {{background:#CBD5E1;min-height:28px;border-radius:3px;}}
QScrollArea#journalScroll QScrollBar::add-line:vertical, QScrollArea#journalScroll QScrollBar::sub-line:vertical {{height:0;}}
QScrollArea#journalScroll QScrollBar::add-page:vertical, QScrollArea#journalScroll QScrollBar::sub-page:vertical {{background:transparent;}}
''')
        for widget in (self.scroll.viewport(), self.content):
            palette = widget.palette()
            palette.setColor(QPalette.ColorRole.Window, QColor('#F1F5F9'))
            palette.setColor(QPalette.ColorRole.Base, QColor('#F1F5F9'))
            widget.setPalette(palette)
            widget.setAutoFillBackground(True)
        self.close_button.setIcon(icon('cross', theme.muted))
        self.step_button.setIcon(icon('step', theme.text))
        self.export_button.setIcon(icon('export', theme.primary))
        self.set_running(self.running)

    def reset(self, title):
        for row in self.entries:
            self.rows.removeWidget(row)
            row.hide()
            row.deleteLater()
        self.entries.clear()
        self.complete = False
        self.case_title.setText(title)
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
        self.play_button.setText('Tạm dừng' if running else 'Chạy tiếp' if self.entries else 'Chạy tự động')
        self.play_button.setIcon(icon('pause' if running else 'play', '#FFFFFF'))
        self.play_button.setEnabled(not self.complete)
        self.step_button.setEnabled(not running and not self.complete)
        message = 'Đang tự động giải…' if running else 'Đã tạm dừng' if self.entries else 'Sẵn sàng'
        self.set_message('Đã hoàn thành màn chơi' if self.complete else message,
                         'success' if self.complete else 'info')

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
        color = {'info': self.theme.primary, 'success': '#1E9E5A',
                 'warning': self.theme.criminal}[tone]
        self.status.setText(message)
        self.status.setStyleSheet(f'color:{color};')

    def closeEvent(self, event):
        self.pause_requested.emit()
        super().closeEvent(event)
