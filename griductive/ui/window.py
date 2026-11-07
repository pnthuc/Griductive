"""Desktop window."""
import sys
import json
from dataclasses import replace
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QElapsedTimer, QSize, QEvent, QPoint
from PySide6.QtGui import QColor, QShortcut, QKeySequence, QPalette
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QToolButton, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QFileDialog, QMenu
from ..engine.regions import region_registry, PuzzleError
from ..engine.clues import clue_registry
from ..engine.models import load_puzzle
from ..engine.game import GameEngine
from .themes import THEMES, stylesheet
from ..presentation.wording_vi import clue_html, clue_text
from ..engine.clues import clue_parts
from .icons import icon
from .portraits import load_expression_frames
from .assets import ROOT, scenery_catalog, scenery_image
from .widgets import label, button, configure_app, DeskSurface
from .cards import PortraitCard
from .dialogs import GameNotice,ModalScrim
from .journal import SolverJournal
from .game_controller import GameController
from ..engine.sat import SolverTimeout
from ..presentation.references import reference_focus

class Window(QMainWindow):
    def __init__(self,path=None):
        super().__init__();self.setWindowTitle('Griductive — Phố biển')
        self.resize(1500,900);self.setMinimumSize(1050,760)
        self.regions=region_registry();self.clues=clue_registry(self.regions)
        self.path=Path(path) if path else ROOT/'puzzles/case-3x3-01.json'
        self.theme_key='pixel';self.theme=THEMES[self.theme_key]
        self.state=None;self.engine=None;self.cards={};self.selected_cell=None;self.active_clue=None;self.zoom_card=None
        self.zoom_slot=None
        self.card_slots={}
        self.notice=None;self.notice_overlay=None
        self.parts={};self.preview_key=None;self.pinned_key=None;self.ticks=0
        self.load_visual_assets()
        self.build();self.apply_theme('pixel')
        self.controller=GameController(self)
        self.controller.finished.connect(self.engine_finished)
        self.controller.failed.connect(self.engine_failed)
        self.controller.busy_changed.connect(self.set_busy)
        self.load(self.path)
        self.set_busy(False)
        self.elapsed_clock=QElapsedTimer();self.elapsed_clock.start()
        self.clock=QTimer(self);self.clock.setInterval(33);self.clock.timeout.connect(self.tick);self.clock.start()
        self.escape=QShortcut(QKeySequence('Escape'),self);self.escape.activated.connect(self.clear_selection)

    def load_visual_assets(self):
        catalog=scenery_catalog()
        spec=catalog['profession_atlas']
        filename=spec['image']
        atlas=scenery_image(filename)
        self.profession_scenes={}
        for name,(col,row) in spec['tiles'].items():
            x0,x1=(round(i*atlas.width()/spec['columns']) for i in (col,col+1))
            y0,y1=(round(i*atlas.height()/spec['rows']) for i in (row,row+1))
            self.profession_scenes[name]=atlas.copy(x0,y0,x1-x0,y1-y0)
        self.character_backgrounds=catalog['character_backgrounds']
        self.expression_bank=load_expression_frames(ROOT/'assets')
        self.portraits=[frames[0] for frames in self.expression_bank.values()]

    def build(self):
        root=DeskSurface();self.desk=root;self.setCentralWidget(root);root.installEventFilter(self)
        board_gutter=20;chrome_gutter=board_gutter+3
        layout=QVBoxLayout(root);layout.setContentsMargins(18,14,18,14);layout.setSpacing(12)
        self.header=QFrame();header=self.header;header.setObjectName('header');hl=QHBoxLayout(header);hl.setContentsMargins(20,8,20,8);hl.setSpacing(17)
        hl.addWidget(label('Griductive','brand'));hl.addStretch()
        self.title=label('','title');hl.addWidget(self.title);hl.addStretch();self.progress=label('','progress');hl.addWidget(self.progress)
        self.load_button=QToolButton();self.load_button.setText('Mở tệp màn chơi');self.load_button.setObjectName('chrome')
        self.load_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon);self.load_button.clicked.connect(self.choose_file)
        self.restart_button=QToolButton();self.restart_button.setText('Làm lại');self.restart_button.setObjectName('chrome')
        self.restart_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon);self.restart_button.clicked.connect(self.restart)
        header_row=QHBoxLayout();header_row.setContentsMargins(chrome_gutter,0,chrome_gutter,0);header_row.addWidget(header);layout.addLayout(header_row)
        self.board_holder=QWidget();self.board_holder.setObjectName('boardCanvas');self.board_layout=QGridLayout(self.board_holder)
        self.board_holder.installEventFilter(self)
        self.board_layout.setContentsMargins(board_gutter,14,board_gutter,14);self.board_layout.setSpacing(10)
        self.board_layout.setVerticalSpacing(8)
        layout.addWidget(self.board_holder,1)
        self.footer=QFrame();footer=self.footer;footer.setObjectName('footer');fl=QHBoxLayout(footer);fl.setContentsMargins(18,6,18,6);fl.setSpacing(12)
        instruction=label('Chọn thẻ để đọc lời khai','muted');instruction.setWordWrap(False)
        fl.addWidget(instruction);fl.addStretch()
        self.motion=button('Chuyển động');self.motion.setObjectName('motion');self.motion.setCheckable(True)
        self.motion.setChecked(True);self.motion.toggled.connect(self.toggle_motion);fl.addWidget(self.motion)
        self.hint_button=button('Gợi ý');self.hint_button.setObjectName('hint');self.hint_button.clicked.connect(self.show_hint)
        self.hint_button.setToolTip('Tìm một nhân vật suy ra được từ thông tin đã mở.');fl.addWidget(self.hint_button)
        self.auto_button=button('Tự động giải',self.open_solver);self.auto_button.hide();self.load_button.hide();self.motion.hide()
        self.tools_button=QToolButton();self.tools_button.setText('Công cụ');self.tools_button.setObjectName('chrome')
        self.tools_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.tools_menu=QMenu(self.tools_button)
        self.tools_menu.addAction('Mở tệp màn chơi…',self.choose_file)
        for path in sorted((ROOT/'puzzles').glob('case-*.json')):
            title = json.loads(path.read_text(encoding='utf-8'))['title']
            self.tools_menu.addAction(title, lambda checked=False,p=path:self.load(p))
        self.tools_menu.addSeparator();self.solve_action=self.tools_menu.addAction('Tự động giải',self.open_solver)
        self.motion_action=self.tools_menu.addAction('Chuyển động');self.motion_action.setCheckable(True);self.motion_action.setChecked(True)
        self.motion_action.toggled.connect(self.motion.setChecked)
        self.tools_button.setMenu(self.tools_menu);hl.addWidget(self.tools_button)
        fl.addWidget(self.restart_button)
        footer_row=QHBoxLayout();footer_row.setContentsMargins(chrome_gutter,0,chrome_gutter,0);footer_row.addWidget(footer);layout.addLayout(footer_row)
        self.solver=SolverJournal(self.theme,self)
        self.solver.run_requested.connect(self.start_auto)
        self.solver.pause_requested.connect(self.pause_auto)
        self.solver.step_requested.connect(self.solve_step)
        self.solver.export_requested.connect(self.export_trace)
        self.auto_clock = QTimer(self)
        self.auto_clock.setInterval(650)
        self.auto_clock.timeout.connect(self.solve_step)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,self.solver);self.solver.hide()
        self.statusBar().hide()

    def apply_theme(self,key):
        if key not in THEMES:return
        self.theme_key=key;self.theme=THEMES[key];self.setStyleSheet(stylesheet(self.theme))
        self.desk.update()
        self.paper_theme=replace(self.theme,gold=self.theme.selected,
            criminal=self.theme.text,innocent=self.theme.text)
        palette=QPalette(self.palette())
        for role,value in ((QPalette.ColorRole.Window,self.theme.background),
            (QPalette.ColorRole.Base,self.theme.surface),(QPalette.ColorRole.Button,self.theme.surface),
            (QPalette.ColorRole.WindowText,self.theme.text),(QPalette.ColorRole.Text,self.theme.text),
            (QPalette.ColorRole.ButtonText,self.theme.text),(QPalette.ColorRole.Highlight,self.theme.primary),
            (QPalette.ColorRole.HighlightedText,'#FFFFFF')):
            palette.setColor(role,QColor(value))
        self.setPalette(palette)
        self.load_button.setIcon(icon('folder',self.theme.text));self.restart_button.setIcon(icon('restart',self.theme.text))
        self.motion.setIcon(icon('motion' if self.motion.isChecked() else 'still',self.theme.muted))
        self.hint_button.setIcon(icon('hint',self.theme.muted));self.auto_button.setIcon(icon('play','#F4EDDB'))
        self.hint_button.setIconSize(QSize(23,23));self.auto_button.setIconSize(QSize(24,24))
        self.solver.set_theme(self.theme)
        for card in self.cards.values():card.theme=self.theme;card.update()
        self.refresh_cards()

    def open_solver(self):
        self.solver.show()
        self.solver.raise_()
        self.resizeDocks([self.solver],[400],Qt.Orientation.Horizontal)

    def start_auto(self):
        if self.engine and not self.engine.solved:
            self.auto_clock.start()
            self.solver.set_running(True)

    def pause_auto(self):
        if hasattr(self,'controller'):self.controller.cancel()
        self.auto_clock.stop()
        self.solver.set_running(False)
        if hasattr(self,'controller'):self.set_busy(self.controller.busy)

    def show_hint(self):
        self.pause_auto()
        self.controller.request('hint')

    def show_hint_result(self,cell,verdict):
        if cell:
            self.select_person(cell)
            self.show_notice('Gợi ý','Các lời khai đã mở đủ để xác định trạng thái của nhân vật này.',person=cell,action='Xem nhân vật')
        else:
            self.show_notice('Gợi ý','INCONSISTENT — Các lời khai mâu thuẫn.' if verdict=='INCONSISTENT' else 'UNKNOWN — Chưa có phán quyết nào suy ra được.')

    def set_busy(self,busy):
        ready=self.state is not None
        self.hint_button.setEnabled(ready and not busy)
        self.solver.play_button.setEnabled(ready and not self.solver.complete)
        self.solver.step_button.setEnabled(ready and not busy and not self.auto_clock.isActive() and not self.solver.complete)
        for card in self.cards.values():
            for control in card.verdict_buttons.values():control.setEnabled(not busy)
        if busy:self.solver.set_message('Đang suy luận…')

    def engine_failed(self,error):
        self.pause_auto()
        message='Hết thời gian suy luận. Bạn có thể thử lại.' if isinstance(error,SolverTimeout) else str(error)
        self.solver.set_message(message,'warning')
        self.show_notice('Suy luận',message,tone='warning')

    def engine_finished(self,kind,result,view,metrics):
        self.engine=view
        if kind=='hint':
            self.show_hint_result(result['cell'],result['result'])
            self.solver.set_running(self.auto_clock.isActive())
            return
        if result['result']=='ACCEPTED':
            self.apply_verdict(result,metrics)
        else:
            self.pause_auto()
            messages={'UNKNOWN':'Chưa đủ thông tin để suy ra bước tiếp theo.',
                'INCONSISTENT':'Các dữ kiện hiện có mâu thuẫn.',
                'NOT_PROVABLE':'NOT_PROVABLE — Chưa đủ thông tin để xác định người này.',
                'CONTRADICTED':'CONTRADICTED — Thông tin hiện có chứng minh trạng thái ngược lại.',
                'ALREADY_REVEALED':'Nhân vật này đã được xác định.'}
            self.solver.set_message(messages[result['result']],'warning')
            if kind=='submit':self.show_notice('Phán quyết',messages[result['result']],tone='warning')

    def closeEvent(self,event):
        self.auto_clock.stop()
        self.controller.shutdown()
        super().closeEvent(event)

    def show_notice(self,title,message,*,tone='info',person=None,action='Đã hiểu'):
        self.pause_auto()
        if self.notice:self.notice.reject()
        self.notice_overlay=ModalScrim(self.desk);self.notice_overlay.setGeometry(self.desk.rect())
        self.notice_overlay.show();self.notice_overlay.raise_()
        subject=None
        if person:
            card=self.cards[person]
            subject=(card.character.name,person,card.expression_frames[0])
        dialog=GameNotice(self,self.theme,title,message,tone=tone,subject=subject,action=action)
        self.notice=dialog
        dialog.finished.connect(lambda result,d=dialog,c=person:self.close_notice(d,c))
        self.position_notice();dialog.open();dialog.action_button.setFocus()

    def position_notice(self):
        if self.notice:
            self.notice.move(self.desk.mapToGlobal(self.desk.rect().center())-self.notice.rect().center())

    def close_notice(self,dialog,person=None):
        if self.notice is dialog:
            self.notice=None
            if self.notice_overlay:self.notice_overlay.hide();self.notice_overlay.deleteLater();self.notice_overlay=None
            if person in self.cards:self.cards[person].setFocus()
        dialog.deleteLater()

    def submit_verdict(self, cell, verdict):
        return self.controller.request('submit',(cell,verdict))

    def apply_verdict(self,result,metrics):
        cell,verdict=result['cell'],result['verdict']
        self.state = self.engine.public_state()
        card = self.cards[cell]
        card.status = verdict
        card.clue = clue_text(self.state.clues[cell],self.state.board,self.clues,self.names)
        card.expression.set_status(verdict)
        self.select_person(cell)
        self.progress.setText(f'Tiến độ: {len(self.state.statuses)}/{len(self.state.board.cells)}')
        primary,auxiliary,clauses=metrics
        self.solver.stats.setText(f'{primary} biến chính, {auxiliary} biến phụ, {clauses} mệnh đề.')
        variables={i+1:f'{self.names[c]} ({c})' for i,c in enumerate(self.state.board.cells)}
        clue_names={spec['id']:f'{self.names[c]} ({c})' for c,spec in self.state.clues.items()}
        self.solver.append_entry(self.engine.trace[-1],self.names[cell],card.expression_frames[0],card.clue,variables,clue_names)
        if self.engine.solved:
            self.pause_auto()
            self.solver.set_complete()
            self.show_notice('Hoàn thành','Đã chứng minh được trạng thái của tất cả nhân vật.',tone='success')
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
                Path(path).write_text(json.dumps(self.engine.trace,ensure_ascii=False,indent=2),encoding='utf-8')
            except OSError as exc:
                self.show_notice('Không thể lưu',str(exc),tone='warning')


    def choose_file(self):
        self.pause_auto()
        path,_=QFileDialog.getOpenFileName(self,'Mở tệp màn chơi',str(ROOT/'puzzles'),'Màn chơi (*.json)')
        if path:self.load(Path(path))

    def restart(self):self.load(self.path)

    def load(self,path):
        try:
            engine=GameEngine(load_puzzle(path,self.clues),self.clues)
            public=engine.public_state()
            if any(c.portrait not in self.expression_bank for c in public.characters):
                raise PuzzleError("Màn chơi tham chiếu sprite không có trong bộ ảnh hiện tại.")
        except (PuzzleError,TypeError,KeyError) as exc:
            self.show_notice('Không thể mở màn chơi',str(exc),tone='warning');return False
        if self.notice:self.notice.reject()
        self.pause_auto();self.engine=self.controller.replace(engine);self.solver.reset(public.title)
        self.path=Path(path);self.state=public;self.selected_cell=None;self.active_clue=None
        self.zoom_card=None;self.zoom_slot=None
        for card in self.cards.values():card.hide();card.deleteLater()
        self.card_slots={}
        self.preview_key=None;self.pinned_key=None;self.parts={};self.solver.hide()
        while self.board_layout.count():
            item=self.board_layout.takeAt(0)
            if item.widget():item.widget().hide();item.widget().deleteLater()
        for i in range(6):self.board_layout.setColumnStretch(i,0);self.board_layout.setRowStretch(i,0)
        self.cards={};board=public.board
        self.names={c.cell:c.name for c in public.characters}
        self.title.setText(public.title);self.progress.setText(f'Tiến độ: {len(public.statuses)}/{len(board.cells)}')
        for char in public.characters:
            spec=public.clues.get(char.cell);desc=clue_text(spec,board,self.clues,self.names) if spec else None
            card=PortraitCard(char,public.statuses.get(char.cell),desc,self.portraits[char.portrait],self.theme,self.desk)
            card.expression_frames=self.expression_bank[char.portrait]
            card.props=self.profession_scenes[self.character_backgrounds[str(char.portrait)]]
            card.motion=self.motion.isChecked();card.selected.connect(self.select_person)
            card.verdict_requested.connect(self.submit_verdict)
            card.clue_text.linkHovered.connect(lambda key,c=char.cell:self.hover_part(key) if c==self.active_clue else None)
            card.clue_text.linkActivated.connect(lambda key,c=char.cell:self.pin_part(key) if c==self.active_clue else None)
            slot=QWidget(self.board_holder);slot.setMinimumSize(card.minimumSize());slot.setSizePolicy(card.sizePolicy())
            self.card_slots[char.cell]=slot
            row,col=board.position(char.cell);self.board_layout.addWidget(slot,row,col)
            slot.show()
            self.board_layout.setColumnStretch(col,1);self.board_layout.setRowStretch(row,1);self.cards[char.cell]=card
        # The user chooses a card before any clue gets colored.
        self.refresh_cards();self.set_busy(self.controller.busy);return True

    def select_person(self,cell):
        self.selected_cell=cell
        if cell in self.state.clues:self.inspect_clue(cell)
        else:self.clear_clue()

    def inspect_clue(self,cell):
        if cell not in self.state.clues:return
        self.active_clue=cell;self.preview_key=None;self.pinned_key=None
        spec=self.state.clues[cell];self.parts={p.key:p for p in clue_parts(spec,self.state.board,self.clues)}
        self.refresh_cards()
        self.pulse_regions()

    def hover_part(self,key):
        self.preview_key=key if key in self.parts else self.pinned_key
        self.refresh_cards()

    def pin_part(self,key):
        if key not in self.parts:return
        if not (self.parts[key].is_region or self.parts[key].named_cells):return
        self.pinned_key=key
        self.preview_key=key;self.refresh_cards();self.pulse_regions()

    def pulse_regions(self):
        if self.pinned_key:
            cells=self.parts[self.pinned_key].cells
        else:
            regions=[part for part in self.parts.values() if part.is_region]
            if regions:cells=set().union(*(part.cells for part in regions))
            else:cells=self.parts['result'].cells if self.parts else ()
        for cell,card in self.cards.items():
            card.feedback.pulse(self.motion.isChecked() and cell in cells)
            if cell in cells:card.raise_()
        if self.zoom_card:self.zoom_card.raise_()
        self.position_cards()

    def clear_clue(self):
        self.active_clue=None;self.parts={};self.preview_key=None;self.pinned_key=None
        for card in self.cards.values():card.feedback.pulse(False)
        self.refresh_cards()

    def clear_selection(self):
        self.selected_cell=None
        self.clear_clue()

    def sync_zoom(self):
        """All original cards use fixed grid slots, so visual motion never reflows the board."""
        self.zoom_card=self.cards.get(self.selected_cell)
        self.zoom_slot=self.card_slots.get(self.selected_cell)
        self.board_layout.activate();self.position_cards()
        if self.zoom_card:self.zoom_card.raise_()

    def position_cards(self):
        for cell,card in self.cards.items():
            slot=self.card_slots[cell];origin=slot.mapTo(self.desk,QPoint())
            factor=card.feedback.scale*(1+.04*card.feedback.pop)
            width=round(slot.width()*factor);height=round(slot.height()*factor)
            x=origin.x()-(width-slot.width())//2
            y=origin.y()-(height-slot.height())//2-round(5*card.feedback.pop)
            card.setGeometry(x,y,width,height)
            card.fade_effect.setOpacity(card.feedback.opacity)
            card.show()

    def eventFilter(self,watched,event):
        if watched is self.desk and event.type()==QEvent.Type.Resize:
            if self.notice_overlay:self.notice_overlay.setGeometry(self.desk.rect())
            if self.notice:QTimer.singleShot(0,self.position_notice)
        if watched is getattr(self,'board_holder',None) and event.type()==QEvent.Type.Resize:
            QTimer.singleShot(0,self.position_cards)
        if watched in (self.desk,getattr(self,'board_holder',None)) and event.type()==QEvent.Type.MouseButtonPress:
            if event.button()==Qt.MouseButton.LeftButton:self.clear_selection()
        return super().eventFilter(watched,event)

    def refresh_cards(self):
        focus=reference_focus(self.parts,self.active_clue,self.pinned_key,self.preview_key)
        for cell,card in self.cards.items():
            card.is_selected=cell==self.selected_cell;card.source=cell==self.active_clue
            card.active_html=clue_html(self.state.clues[cell],self.state.board,self.clues,self.paper_theme,self.names) if card.source else None
            card.counted=cell in focus.counted;card.anchor=cell in focus.anchors
            card.preview_role=focus.preview_role(cell)
            card.region_roles=focus.roles(cell)
            card.name_role=focus.named.get(cell)
            card.dimmed=bool(self.active_clue and cell not in focus.focused)
            card.feedback.emphasize(card.is_selected,card.dimmed,self.motion.isChecked())
            card.place_actions();card.update()
        self.sync_zoom()

    def toggle_motion(self,enabled):
        self.motion.setIcon(icon('motion' if enabled else 'still',self.theme.muted))
        for card in self.cards.values():
            card.motion=enabled
            if not enabled:card.feedback.finish()
            card.update()
        self.position_cards()
        if hasattr(self,'clock'):
            self.elapsed_clock.restart()
            if enabled:self.clock.start()
            else:self.clock.stop()

    def tick(self):
        self.ticks+=1
        delta=min(.1,self.elapsed_clock.restart()/1000.)
        if not self.isVisible() or self.isMinimized():return
        for card in self.cards.values():
            if card.motion:card.expression.advance(delta);card.feedback.advance(delta);card.update()
        self.position_cards()


def run():
    app=QApplication.instance() or QApplication(sys.argv);configure_app(app)
    window=Window(sys.argv[1] if len(sys.argv)>1 else None)
    if window.state and window.state.board.size==5:window.showMaximized()
    else:window.show()
    sys.exit(app.exec())

