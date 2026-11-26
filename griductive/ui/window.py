"""Desktop window — Cozy Harbor Game UI with cute pixel characters & polished HUD."""
import sys
import json
from dataclasses import replace
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QElapsedTimer, QSize, QEvent, QPoint
from PySide6.QtGui import QIcon, QColor, QShortcut, QKeySequence, QPalette, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QToolButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFileDialog, QMenu, QSizePolicy,
)
from ..engine.regions import region_registry, PuzzleError
from ..engine.clues import clue_registry, clue_parts
from ..engine.cnf import build_knowledge_base
from ..engine.models import load_puzzle
from ..engine.game import GameEngine
from ..engine.sat import SolverTimeout
from ..presentation.wording_vi import clue_html, clue_text
from ..presentation.references import inspect_references
from .themes import THEMES, stylesheet
from .icons import icon
from .portraits import load_expression_frames, load_silhouette_frames
from .assets import ROOT, scenery_catalog, scenery_image
from .widgets import (
    label, configure_app, DeskSurface, PixelLabel, HudButton,
    HeaderBar, BrandMark, CaseSelectorButton, ProgressPill, CozyMenu,
)
from .cards import PortraitCard
from .dialogs import GameNotice, ModalScrim
from .journal import SolverJournal
from .game_controller import GameController


class CaseMenu(CozyMenu):
    def showEvent(self, event):
        super().showEvent(event)
        button = self.parentWidget()
        if not button:
            return
        left = button.mapToGlobal(QPoint(0, 0)).x()
        screen = button.screen().availableGeometry()
        self.move(max(screen.left(), min(left, screen.right() - self.width() + 1)), self.y() + 3)


class ToolsMenu(CozyMenu):
    def showEvent(self, event):
        super().showEvent(event)
        button = self.parentWidget()
        if not button:
            return
        right = button.mapToGlobal(QPoint(button.width(), 0)).x()
        screen = button.screen().availableGeometry()
        x = max(screen.left(), min(right - self.width(), screen.right() - self.width() + 1))
        self.move(x, self.y() + 3)


class Window(QMainWindow):
    def __init__(self, path=None):
        super().__init__()
        self.setWindowTitle('Griductive')
        self.resize(1460, 860)
        self.setMinimumSize(1050, 760)
        self.regions = region_registry()
        self.clues = clue_registry(self.regions)
        self.path = Path(path) if path else ROOT / 'puzzles/case-3x3-01.json'
        self.theme_key = 'pixel'
        self.theme = THEMES[self.theme_key]
        self.state = None
        self.engine = None
        self.cards = {}
        self.selected_cell = None
        self.active_clue = None
        self.zoom_card = None
        self.zoom_slot = None
        self.card_slots = {}
        self.notice = None
        self.notice_overlay = None
        self.parts = {}
        self.preview_key = None
        self.pinned_key = None
        self._col_labels = []
        self._row_labels = []
        self._case_actions = {}
        self.load_visual_assets()
        self.build()
        self.apply_theme('pixel')
        self.controller = GameController(self)
        self.controller.finished.connect(self.engine_finished)
        self.controller.failed.connect(self.engine_failed)
        self.controller.busy_changed.connect(self.set_busy)
        self.load(self.path)
        self.set_busy(False)
        self.elapsed_clock = QElapsedTimer()
        self.elapsed_clock.start()
        self.clock = QTimer(self)
        self.clock.setInterval(33)
        self.clock.timeout.connect(self.tick)
        self.clock.start()
        self.escape = QShortcut(QKeySequence('Escape'), self)
        self.escape.activated.connect(self.clear_selection)

    def load_visual_assets(self):
        catalog = scenery_catalog()
        self.character_backgrounds = catalog['character_backgrounds']
        spec = catalog['profession_atlas']
        atlas = scenery_image(spec['image'])
        self.profession_props = {}
        for name, (col, row) in spec['tiles'].items():
            left, right = (round(i * atlas.width() / spec['columns']) for i in (col, col + 1))
            top, bottom = (round(i * atlas.height() / spec['rows']) for i in (row, row + 1))
            self.profession_props[name] = atlas.copy(left, top, right - left, bottom - top)
        self.expression_bank = load_expression_frames(ROOT / 'assets')
        self.silhouette_bank = load_silhouette_frames(ROOT / 'assets')
        self.portraits = [frames[0] for frames in self.expression_bank.values()]

    def build(self):
        root = DeskSurface()
        self.desk = root
        self.setCentralWidget(root)
        root.installEventFilter(self)

        # Safe margins so 1.10x enlarged corner cards always stay strictly inside `self.desk`
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 10, 30, 26)
        layout.setSpacing(8)

        # Cozy Harbor Floating Capsule Header HUD
        self.header = HeaderBar()
        self.header.setObjectName('header')
        self.header.setFixedHeight(50)
        self.header.installEventFilter(self)
        hl = QHBoxLayout(self.header)
        hl.setContentsMargins(12, 6, 10, 6)
        hl.setSpacing(10)
        self._header_layout = hl

        hl.addWidget(BrandMark())
        brand = label('Griductive', 'brand')
        brand.setWordWrap(False)
        brand.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self._brand_label = brand
        hl.addWidget(brand)
        hl.addSpacing(2)

        # Interactive Case Selector Pill with grouped 3x3 / 4x4 / 5x5 menu + Load JSON
        self._case_btn = CaseSelectorButton()
        self._case_btn.setObjectName('caseSelector')
        self._case_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._case_menu = CaseMenu(self._case_btn)
        self._populate_case_menu()
        self._case_btn.setMenu(self._case_menu)
        hl.addWidget(self._case_btn)

        self.progress_pill = ProgressPill()
        hl.addWidget(self.progress_pill)

        hl.addStretch(1)

        # Tactile Cozy Harbor Action Keycaps
        self.hint_button = HudButton(variant='amber')
        self.hint_button.setText('Gợi ý')
        self.hint_button.setObjectName('hint')
        self.hint_button.setFixedSize(96, 36)
        self.hint_button.clicked.connect(self.show_hint)
        self.hint_button.setToolTip('Tìm một nhân vật suy ra được từ thông tin đã mở.')
        hl.addWidget(self.hint_button)

        self.restart_button = HudButton(variant='cream')
        self.restart_button.setText('Làm lại')
        self.restart_button.setObjectName('restartHud')
        self.restart_button.setFixedSize(102, 36)
        self.restart_button.clicked.connect(self.restart)
        self.restart_button.setToolTip('Chơi lại màn hiện tại từ đầu.')
        hl.addWidget(self.restart_button)

        self.solver_button = HudButton(variant='mint')
        self.solver_button.setText('Sổ giải')
        self.solver_button.setObjectName('solverHud')
        self.solver_button.setFixedSize(98, 36)
        self.solver_button.clicked.connect(self.toggle_solver)
        self.solver_button.setToolTip('Mở hoặc đóng Sổ tay suy luận DPLL.')
        hl.addWidget(self.solver_button)

        # Secondary Tools Menu button
        self.tools_button = HudButton(variant='cream')
        self.tools_button.setObjectName('menuButton')
        self.tools_button.setFixedSize(42, 36)
        self.tools_button.setToolTip('Menu công cụ & mở tệp')
        self.tools_button.setAccessibleName('Menu chính')
        self.tools_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.tools_menu = ToolsMenu(self.tools_button)
        self.solve_action = self.tools_menu.addAction(icon('play', '#1E5B88'), 'Tự động giải', self.open_solver)
        self.open_action = self.tools_menu.addAction(icon('export', '#1E5B88'), 'Mở màn chơi JSON…', self.open_case_file)
        self.tools_menu.addAction(icon('restart', '#5C4338'), 'Làm lại màn này', self.restart)
        self.tools_menu.addSeparator()
        self.motion_action = self.tools_menu.addAction('Hiệu ứng chuyển động')
        self.motion_action.setCheckable(True)
        self.motion_action.setChecked(True)
        self.motion_action.toggled.connect(self.toggle_motion)
        self._sync_motion_action_icon(True)
        self.tools_button.setMenu(self.tools_menu)
        hl.addWidget(self.tools_button)

        self.motion_enabled = True
        layout.addWidget(self.header)

        # Coordinate Grid + Board Canvas
        self._grid_area = QWidget()
        self._grid_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._grid_area.installEventFilter(self)
        cgrid = QGridLayout(self._grid_area)
        cgrid.setContentsMargins(0, 2, 0, 0)
        cgrid.setHorizontalSpacing(8)
        cgrid.setVerticalSpacing(6)

        self._col_bar = QWidget()
        self._col_layout = QHBoxLayout(self._col_bar)
        self._col_layout.setContentsMargins(0, 0, 0, 0)
        self._col_layout.setSpacing(12)
        self._col_bar.setFixedHeight(26)
        cgrid.addWidget(self._col_bar, 0, 1)

        self._row_bar = QWidget()
        self._row_layout = QVBoxLayout(self._row_bar)
        self._row_layout.setContentsMargins(0, 0, 0, 0)
        self._row_layout.setSpacing(10)
        self._row_bar.setFixedWidth(30)
        cgrid.addWidget(self._row_bar, 1, 0)

        self.board_holder = QWidget()
        self.board_holder.setObjectName('boardCanvas')
        self.board_holder.installEventFilter(self)
        self.board_layout = QGridLayout(self.board_holder)
        self.board_layout.setContentsMargins(0, 0, 0, 0)
        self.board_layout.setHorizontalSpacing(12)
        self.board_layout.setVerticalSpacing(10)
        cgrid.addWidget(self.board_holder, 1, 1)
        cgrid.setColumnStretch(1, 1)
        cgrid.setRowStretch(1, 1)

        layout.addWidget(self._grid_area, 1)

        self.solver = SolverJournal(self.theme, self)
        self.solver.run_requested.connect(self.start_auto)
        self.solver.pause_requested.connect(self.pause_auto)
        self.solver.step_requested.connect(self.solve_step)
        self.solver.export_requested.connect(self.export_trace)
        self.solver.visibilityChanged.connect(self._on_solver_visibility_changed)
        self.auto_clock = QTimer(self)
        self.auto_clock.setInterval(650)
        self.auto_clock.timeout.connect(self.solve_step)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.solver)
        self.solver.hide()
        self.statusBar().hide()

    def _populate_case_menu(self):
        self._case_menu.clear()
        self._case_actions.clear()
        last_size = None
        for path in sorted((ROOT / 'puzzles').glob('case-*.json')):
            data = json.loads(path.read_text(encoding='utf-8'))
            size = data['size']
            if size != last_size:
                if last_size is not None:
                    self._case_menu.addSeparator()
                hdr = self._case_menu.addAction(f'BÀN CỜ {size}×{size}')
                hdr.setEnabled(False)
                last_size = size
            act = self._case_menu.addAction(
                f"   {data['title']}",
                lambda checked=False, p=path: self.load(p),
            )
            self._case_actions[path.resolve()] = (act, data['title'])
        self._case_menu.addSeparator()
        self._case_menu.addAction(icon('export', '#1E5B88'), 'Mở màn chơi JSON…', self.open_case_file)

    def _sync_case_menu_check(self):
        resolved = self.path.resolve() if self.path else None
        for p, (act, title) in self._case_actions.items():
            prefix = '● ' if p == resolved else '   '
            act.setText(f'{prefix}{title}')

    def _update_progress_pill(self):
        if self.state:
            self.progress_pill.set_progress(len(self.state.statuses), len(self.state.board.cells))
            self.progress_pill.show()
        else:
            self.progress_pill.set_progress(0, 0)
            self.progress_pill.hide()

    def _sync_motion_action_icon(self, enabled: bool):
        if not hasattr(self, 'motion_action'):
            return
        if enabled:
            self.motion_action.setIcon(icon('check', '#1E8A52'))
        else:
            blank = QPixmap(16, 16)
            blank.fill(Qt.GlobalColor.transparent)
            self.motion_action.setIcon(QIcon(blank))

    def _sync_header_density(self):
        if not hasattr(self, 'header') or not hasattr(self, '_header_layout'):
            return
        w = self.header.width() if self.header.width() > 200 else max(400, self.desk.width() - 58)
        if w < 740:
            self._header_layout.setContentsMargins(10, 6, 8, 6)
            self._header_layout.setSpacing(6)
            self.progress_pill.set_compact(True)
            self.hint_button.setText('Gợi ý')
            self.hint_button.setFixedSize(84, 36)
            self.restart_button.setText('')
            self.restart_button.setFixedSize(38, 36)
            self.solver_button.setText('')
            self.solver_button.setFixedSize(38, 36)
            self.tools_button.setFixedSize(38, 36)
        elif w < 880:
            self._header_layout.setContentsMargins(11, 6, 9, 6)
            self._header_layout.setSpacing(7)
            self.progress_pill.set_compact(True)
            self.hint_button.setText('Gợi ý')
            self.hint_button.setFixedSize(88, 36)
            self.restart_button.setText('Làm lại')
            self.restart_button.setFixedSize(92, 36)
            self.solver_button.setText('Sổ giải')
            self.solver_button.setFixedSize(90, 36)
            self.tools_button.setFixedSize(40, 36)
        else:
            self._header_layout.setContentsMargins(12, 6, 10, 6)
            self._header_layout.setSpacing(10)
            self.progress_pill.set_compact(False)
            self.hint_button.setText('Gợi ý')
            self.hint_button.setFixedSize(96, 36)
            self.restart_button.setText('Làm lại')
            self.restart_button.setFixedSize(102, 36)
            self.solver_button.setText('Sổ giải')
            self.solver_button.setFixedSize(98, 36)
            self.tools_button.setFixedSize(42, 36)

    def _on_solver_visibility_changed(self, visible: bool):
        self.solver_button.active_badge = visible
        self.solver_button.setIcon(icon('play', '#FFFFFF' if visible else '#143B2A'))
        self.solver_button.update()
        QTimer.singleShot(0, self._sync_header_density)
        QTimer.singleShot(0, self.position_cards)

    def toggle_solver(self):
        if self.solver.isVisible():
            self.solver.close()
        else:
            self.open_solver()

    def open_case_file(self):
        self.pause_auto()
        chosen, _ = QFileDialog.getOpenFileName(
            self, 'Mở tệp màn chơi JSON', str(ROOT / 'puzzles'), 'JSON (*.json)',
        )
        if chosen:
            self.load(Path(chosen))

    def _rebuild_coordinates(self, size):
        h_gap = 10 if size >= 5 else 14
        v_gap = 9 if size >= 5 else 13
        self._col_layout.setSpacing(h_gap)
        self._row_layout.setSpacing(v_gap)
        self.board_layout.setHorizontalSpacing(h_gap)
        self.board_layout.setVerticalSpacing(v_gap)
        self._col_bar.setFixedHeight(26)
        self._row_bar.setFixedWidth(30)
        for item_list, bar_layout in ((self._col_labels, self._col_layout), (self._row_labels, self._row_layout)):
            for w in item_list:
                bar_layout.removeWidget(w)
                w.hide()
                w.deleteLater()
            item_list.clear()
        for col in range(size):
            pill = PixelLabel(chr(65 + col), 'coordHeader', font_px=13, is_row=False)
            self._col_layout.addWidget(pill, 1)
            self._col_labels.append(pill)
        for row in range(size):
            pill = PixelLabel(str(row + 1), 'coordHeader', font_px=13, is_row=True)
            self._row_layout.addWidget(pill, 1)
            self._row_labels.append(pill)

    def apply_theme(self, key):
        if key not in THEMES:
            return
        self.theme_key = key
        self.theme = THEMES[key]
        self.setStyleSheet(stylesheet(self.theme))
        self.desk.update()
        self.paper_theme = replace(
            self.theme,
            gold=self.theme.selected,
            criminal=self.theme.text,
            innocent=self.theme.text,
        )
        palette = QPalette(self.palette())
        for role, value in (
            (QPalette.ColorRole.Window, self.theme.background),
            (QPalette.ColorRole.Base, self.theme.surface),
            (QPalette.ColorRole.Button, self.theme.surface),
            (QPalette.ColorRole.WindowText, self.theme.text),
            (QPalette.ColorRole.Text, self.theme.text),
            (QPalette.ColorRole.ButtonText, self.theme.text),
            (QPalette.ColorRole.Highlight, self.theme.primary),
            (QPalette.ColorRole.HighlightedText, '#FFFFFF'),
        ):
            palette.setColor(role, QColor(value))
        self.setPalette(palette)
        self.hint_button.setIcon(icon('hint', '#2A1D11'))
        self.hint_button.setIconSize(QSize(16, 16))
        self.restart_button.setIcon(icon('restart', '#172A3C'))
        self.restart_button.setIconSize(QSize(15, 15))
        self.solver_button.setIcon(icon('play', '#143B2A'))
        self.solver_button.setIconSize(QSize(15, 15))
        self.tools_button.setIcon(QIcon(str(ROOT / 'public/pixel/gear.png')))
        self.tools_button.setIconSize(QSize(20, 20))
        self.solver.set_theme(self.theme)
        for card in self.cards.values():
            card.theme = self.theme
            card.update()
        self.refresh_cards()

    def open_solver(self):
        self.solver.show()
        self.solver.raise_()
        dock_w = 365 if self.width() < 1200 else 395
        self.resizeDocks([self.solver], [dock_w], Qt.Orientation.Horizontal)
        QTimer.singleShot(0, self._sync_header_density)

    def start_auto(self):
        if self.engine and not self.engine.solved:
            self.auto_clock.start()
            self.solver.set_running(True)

    def pause_auto(self):
        if hasattr(self, 'controller'):
            self.controller.cancel()
        self.auto_clock.stop()
        self.solver.set_running(False)
        if hasattr(self, 'controller'):
            self.set_busy(self.controller.busy)

    def show_hint(self):
        self.pause_auto()
        self.controller.request('hint')

    def show_hint_result(self, cell, verdict):
        if cell:
            self.select_person(cell)
            self.show_notice(
                'Gợi ý suy luận',
                'Các lời khai đã mở đủ để xác định chắc chắn trạng thái của nhân vật này.',
                person=cell,
                action='Xem nhân vật',
            )
        else:
            self.show_notice(
                'Gợi ý suy luận',
                'INCONSISTENT — Các lời khai mâu thuẫn.'
                if verdict == 'INCONSISTENT'
                else 'UNKNOWN — Chưa có phán quyết nào suy ra được.',
            )

    def set_busy(self, busy):
        ready = self.state is not None
        self.hint_button.setEnabled(ready and not busy)
        self.restart_button.setEnabled(ready)
        self.solver_button.setEnabled(ready)
        self.solver.play_button.setEnabled(ready and not self.solver.complete)
        self.solver.step_button.setEnabled(
            ready and not busy and not self.auto_clock.isActive() and not self.solver.complete
        )
        for card in self.cards.values():
            for control in card.verdict_buttons.values():
                control.setEnabled(not busy)
        if busy:
            self.solver.set_message('Đang suy luận…')

    def engine_failed(self, error):
        self.pause_auto()
        message = 'Hết thời gian suy luận. Bạn có thể thử lại.' if isinstance(error, SolverTimeout) else str(error)
        self.solver.set_message(message, 'warning')
        self.show_notice('Suy luận', message, tone='warning')

    def engine_finished(self, kind, result, view, metrics):
        self.engine = view
        if kind == 'hint':
            self.show_hint_result(result['cell'], result['result'])
            self.solver.set_running(self.auto_clock.isActive())
            return
        if result['result'] == 'ACCEPTED':
            self.apply_verdict(result, metrics)
        else:
            self.pause_auto()
            messages = {
                'UNKNOWN': 'Chưa đủ thông tin để suy ra bước tiếp theo.',
                'INCONSISTENT': 'Các dữ kiện hiện có mâu thuẫn.',
                'NOT_PROVABLE': 'NOT_PROVABLE — Chưa đủ thông tin để xác định người này.',
                'CONTRADICTED': 'CONTRADICTED — Thông tin hiện có chứng minh trạng thái ngược lại.',
                'ALREADY_REVEALED': 'Nhân vật này đã được xác định.',
            }
            self.solver.set_message(messages[result['result']], 'warning')
            if kind == 'submit':
                self.show_notice(
                    'Phán quyết chưa hợp lệ',
                    messages[result['result']],
                    tone='warning',
                    person=result.get('cell'),
                )

    def closeEvent(self, event):
        self.auto_clock.stop()
        self.controller.shutdown()
        super().closeEvent(event)

    def show_notice(self, title, message, *, tone='info', person=None, action='Đã hiểu'):
        self.pause_auto()
        if self.notice:
            self.notice.reject()
        self.notice_overlay = ModalScrim(self.desk)
        self.notice_overlay.setGeometry(self.desk.rect())
        self.notice_overlay.show()
        self.notice_overlay.raise_()
        subject = None
        if person and person in self.cards:
            card = self.cards[person]
            portrait = (
                card.expression_frames[0]
                if (card.status or card.is_selected)
                else card.silhouette_frames[0]
            )
            subject = (card.character, portrait)
        dialog = GameNotice(self, self.theme, title, message, tone=tone, subject=subject, action=action)
        self.notice = dialog
        dialog.finished.connect(lambda result, d=dialog, c=person: self.close_notice(d, c))
        self.position_notice()
        dialog.open()
        dialog.action_button.setFocus()

    def position_notice(self):
        if self.notice:
            self.notice.move(self.desk.mapToGlobal(self.desk.rect().center()) - self.notice.rect().center())

    def close_notice(self, dialog, person=None):
        if self.notice is dialog:
            self.notice = None
            if self.notice_overlay:
                self.notice_overlay.hide()
                self.notice_overlay.deleteLater()
                self.notice_overlay = None
            if person in self.cards:
                self.cards[person].setFocus()
        dialog.deleteLater()

    def submit_verdict(self, cell, verdict):
        return self.controller.request('submit', (cell, verdict))

    def apply_verdict(self, result, metrics):
        cell, verdict = result['cell'], result['verdict']
        self.state = self.engine.public_state()
        self._update_progress_pill()
        card = self.cards[cell]
        card.status = verdict
        card.clue = clue_text(self.state.clues[cell], self.state.board, self.clues, self.names)
        card.expression.set_status(verdict)
        self.select_person(cell)
        primary, auxiliary, clauses = metrics
        self.solver.stats.setText(f'{primary} biến chính, {auxiliary} biến phụ, {clauses} mệnh đề.')
        variables = {i + 1: f'{self.names[c]} ({c})' for i, c in enumerate(self.state.board.cells)}
        clue_names = {spec['id']: f'{self.names[c]} ({c})' for c, spec in self.state.clues.items()}
        self.solver.append_entry(
            self.engine.trace[-1],
            self.names[cell],
            card.expression_frames[0],
            card.clue,
            variables,
            clue_names,
        )
        if self.engine.solved:
            self.pause_auto()
            self.solver.set_complete()
            self.show_notice('Hoàn thành vụ án!', 'Đã chứng minh được trạng thái của tất cả nhân vật.', tone='success')
        return True

    def solve_step(self):
        if not self.engine or self.engine.solved:
            self.pause_auto()
            return
        self.controller.request('step')

    def export_trace(self):
        self.pause_auto()
        path, _ = QFileDialog.getSaveFileName(self, 'Xuất nhật ký', 'trace.json', 'JSON (*.json)')
        if path:
            try:
                Path(path).write_text(json.dumps(self.engine.trace, ensure_ascii=False, indent=2), encoding='utf-8')
            except OSError as exc:
                self.show_notice('Không thể lưu', str(exc), tone='warning')

    def restart(self):
        self.load(self.path)

    def load(self, path):
        try:
            engine = GameEngine(load_puzzle(path, self.clues), self.clues)
            public = engine.public_state()
            if any(c.portrait not in self.expression_bank for c in public.characters):
                raise PuzzleError('Màn chơi tham chiếu sprite không có trong bộ ảnh hiện tại.')
        except (PuzzleError, TypeError, KeyError) as exc:
            self.show_notice('Không thể mở màn chơi', str(exc), tone='warning')
            return False
        if self.notice:
            self.notice.reject()
        self.pause_auto()
        self.engine = self.controller.replace(engine)
        self.solver.reset(public.title)
        try:
            initial_kb = build_knowledge_base(public, self.clues)
        except NotImplementedError:
            initial_kb = None
        if initial_kb is not None:
            self.solver.stats.setText(
                f'{len(initial_kb.primary)} biến chính, {initial_kb.auxiliary_count} biến phụ, {len(initial_kb.clauses)} mệnh đề.'
            )
            self.solver.stats_button.setEnabled(True)
        self.path = Path(path)
        self.state = public
        self.selected_cell = None
        self.active_clue = None
        self.zoom_card = None
        self.zoom_slot = None
        for card in self.cards.values():
            card.hide()
            card.deleteLater()
        self.card_slots = {}
        self.preview_key = None
        self.pinned_key = None
        self.parts = {}
        self.solver.hide()
        while self.board_layout.count():
            item = self.board_layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()
        for i in range(6):
            self.board_layout.setColumnStretch(i, 0)
            self.board_layout.setRowStretch(i, 0)
        self.cards = {}
        board = public.board
        self._rebuild_coordinates(board.size)
        self.names = {c.cell: c.name for c in public.characters}
        self._case_btn.set_case_info(public.title, board.size)
        self._sync_case_menu_check()
        self._update_progress_pill()
        for char in public.characters:
            spec = public.clues.get(char.cell)
            desc = clue_text(spec, board, self.clues, self.names) if spec else None
            card = PortraitCard(
                char, public.statuses.get(char.cell), desc,
                self.portraits[char.portrait], self.theme, self.desk,
            )
            card.expression_frames = self.expression_bank[char.portrait]
            card.silhouette_frames = self.silhouette_bank[char.portrait]
            card.props = self.profession_props[self.character_backgrounds[str(char.portrait)]]
            card.motion = self.motion_enabled
            card.selected.connect(self.select_person)
            card.verdict_requested.connect(self.submit_verdict)
            card.clue_text.linkHovered.connect(
                lambda key, c=char.cell: self.hover_part(key) if c == self.active_clue else None
            )
            card.clue_text.linkActivated.connect(
                lambda key, c=char.cell: self.pin_part(key) if c == self.active_clue else None
            )
            slot = QWidget(self.board_holder)
            slot.setMinimumSize(card.minimumSize())
            slot.setSizePolicy(card.sizePolicy())
            self.card_slots[char.cell] = slot
            row, col = board.position(char.cell)
            self.board_layout.addWidget(slot, row, col)
            slot.show()
            self.board_layout.setColumnStretch(col, 1)
            self.board_layout.setRowStretch(row, 1)
            self.cards[char.cell] = card
        self.refresh_cards()
        self.set_busy(self.controller.busy)
        return True

    def select_person(self, cell):
        self.selected_cell = cell
        if cell in self.state.clues:
            self.inspect_clue(cell)
        else:
            self.clear_clue()

    def inspect_clue(self, cell):
        if cell not in self.state.clues:
            return
        self.active_clue = cell
        self.preview_key = None
        self.pinned_key = None
        spec = self.state.clues[cell]
        self.parts = {p.key: p for p in clue_parts(spec, self.state.board, self.clues)}
        self.refresh_cards()
        self.pulse_regions()

    def hover_part(self, key):
        self.preview_key = key if key in self.parts else self.pinned_key
        self.refresh_cards()

    def pin_part(self, key):
        if key not in self.parts:
            return
        if not (self.parts[key].is_region or self.parts[key].named_cells):
            return
        self.pinned_key = key
        self.preview_key = key
        self.refresh_cards()
        self.pulse_regions()

    def pulse_regions(self):
        if self.pinned_key:
            cells = self.parts[self.pinned_key].cells
        else:
            regions = [part for part in self.parts.values() if part.is_region]
            if regions:
                cells = set().union(*(part.cells for part in regions))
            else:
                cells = self.parts['result'].cells if self.parts else ()
        for cell, card in self.cards.items():
            card.feedback.pulse(self.motion_enabled and cell in cells)
            if cell in cells:
                card.raise_()
        if self.zoom_card:
            self.zoom_card.raise_()
        self.position_cards()

    def clear_clue(self):
        self.active_clue = None
        self.parts = {}
        self.preview_key = None
        self.pinned_key = None
        for card in self.cards.values():
            card.feedback.pulse(False)
        self.refresh_cards()

    def clear_selection(self):
        self.selected_cell = None
        self.clear_clue()

    def sync_zoom(self):
        """All original cards use fixed grid slots, so visual motion never reflows the board."""
        self.zoom_card = self.cards.get(self.selected_cell)
        self.zoom_slot = self.card_slots.get(self.selected_cell)
        self._grid_area.layout().activate()
        self.board_layout.activate()
        self.position_cards()
        if self.zoom_card:
            self.zoom_card.raise_()

    def position_cards(self):
        for cell, card in self.cards.items():
            slot = self.card_slots[cell]
            origin = slot.mapTo(self.desk, QPoint())
            factor = card.feedback.scale * (1 + 0.04 * card.feedback.pop)
            width = round(slot.width() * factor)
            height = round(slot.height() * factor)
            x = origin.x() - (width - slot.width()) // 2
            y = origin.y() - (height - slot.height()) // 2 - round(5 * card.feedback.pop)
            card.setGeometry(x, y, width, height)
            card.fade_effect.setOpacity(card.feedback.opacity)
            card.show()

    def eventFilter(self, watched, event):
        if watched is getattr(self, 'header', None) and event.type() == QEvent.Type.Resize:
            self._sync_header_density()
        if watched is self.desk and event.type() == QEvent.Type.Resize:
            self._sync_header_density()
            if self.notice_overlay:
                self.notice_overlay.setGeometry(self.desk.rect())
            if self.notice:
                QTimer.singleShot(0, self.position_notice)
            QTimer.singleShot(0, self.position_cards)
        if watched in (getattr(self, 'board_holder', None), getattr(self, '_grid_area', None)):
            if event.type() in (QEvent.Type.Resize, QEvent.Type.Move):
                QTimer.singleShot(0, self.position_cards)
        if watched in (self.desk, getattr(self, 'board_holder', None), getattr(self, '_grid_area', None)):
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self.clear_selection()
        return super().eventFilter(watched, event)

    def refresh_cards(self):
        markup = ''
        if self.active_clue:
            markup = clue_html(
                self.state.clues[self.active_clue], self.state.board,
                self.clues, self.paper_theme, self.names,
            )
        markup, focus = inspect_references(
            markup, self.parts, self.paper_theme,
            self.active_clue, self.pinned_key, self.preview_key,
        )
        for cell, card in self.cards.items():
            card.is_selected = cell == self.selected_cell
            card.source = cell == self.active_clue
            card.active_html = markup if card.source else None
            card.counted = cell in focus.counted
            card.anchor = cell in focus.anchors
            card.preview_role = focus.preview_role(cell)
            card.region_colors = focus.colors_for(cell)
            card.name_color = focus.named.get(cell)
            card.dimmed = bool(self.active_clue and cell not in focus.focused)
            card.feedback.emphasize(card.is_selected, card.dimmed, self.motion_enabled)
            card.place_actions()
            card.update()

        # Light up compact row/column badges when an entire row/column is in active focus!
        if self.state:
            n = self.state.board.size
            for c_idx, pill in enumerate(self._col_labels):
                col_cells = {f'{chr(65 + c_idx)}{r + 1}' for r in range(n)}
                hl = bool(self.active_clue and col_cells.issubset(focus.counted))
                if pill.highlighted != hl:
                    pill.highlighted = hl
                    pill.update()
            for r_idx, pill in enumerate(self._row_labels):
                row_cells = {f'{chr(65 + c)}{r_idx + 1}' for c in range(n)}
                hl = bool(self.active_clue and row_cells.issubset(focus.counted))
                if pill.highlighted != hl:
                    pill.highlighted = hl
                    pill.update()

        self.sync_zoom()

    def toggle_motion(self, enabled):
        self.motion_enabled = enabled
        if hasattr(self, 'motion_action') and self.motion_action.isChecked() != enabled:
            self.motion_action.blockSignals(True)
            self.motion_action.setChecked(enabled)
            self.motion_action.blockSignals(False)
        self._sync_motion_action_icon(enabled)
        for card in self.cards.values():
            card.motion = enabled
            if not enabled:
                card.feedback.finish()
            card.update()
        self.position_cards()
        if hasattr(self, 'clock'):
            self.elapsed_clock.restart()
            if enabled:
                self.clock.start()
            else:
                self.clock.stop()

    def tick(self):
        delta = min(0.1, self.elapsed_clock.restart() / 1000.0)
        if not self.isVisible() or self.isMinimized():
            return
        for card in self.cards.values():
            if card.motion:
                card.expression.advance(delta)
                card.feedback.advance(delta)
                card.update()
        self.position_cards()


def run():
    if QApplication.instance() is None:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    app = QApplication.instance() or QApplication(sys.argv)
    configure_app(app)
    window = Window(sys.argv[1] if len(sys.argv) > 1 else None)
    if window.state and window.state.board.size == 5:
        window.showMaximized()
    else:
        window.show()
    sys.exit(app.exec())
