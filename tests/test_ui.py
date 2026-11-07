import os
import json
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt,QPoint,QRect
from PySide6.QtTest import QTest
from griductive.ui import Window,configure_app,ROOT


class InteractionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])
        configure_app(cls.app)

    def setUp(self):
        self.window=Window(ROOT/'tests/fixtures/prototype-3x3.json');self.window.show();QTest.qWait(80)
        self.window.motion.setChecked(False)

    def wait_engine(self):
        import time
        deadline=time.monotonic()+10
        while self.window.controller.busy and time.monotonic()<deadline:
            QTest.qWait(5)
        self.assertFalse(self.window.controller.busy,'Background request did not finish')
        self.app.processEvents()

    def tearDown(self):self.window.close();self.window.deleteLater();self.app.processEvents()

    def test_hint_pauses_auto_and_dialog_does_not_advance_the_game(self):
        before=self.window.state
        self.window.start_auto()
        self.window.show_hint();self.wait_engine()
        self.assertFalse(self.window.auto_clock.isActive())
        self.assertTrue(self.window.notice.isVisible())
        QTest.qWait(700)
        self.assertIs(self.window.state,before)
        self.assertFalse(self.window.engine.trace)
        self.window.notice.reject()

    def test_invalid_initial_file_can_recover_by_choosing_a_valid_map(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.json';path.write_text('{}')
            window=Window(path)
            try:
                self.assertIsNone(window.state)
                self.assertFalse(window.hint_button.isEnabled())
                self.assertFalse(window.solver.step_button.isEnabled())
                self.assertFalse(window.solver.play_button.isEnabled())
                self.assertFalse(window.controller.request('hint'))
                window.start_auto();window.solve_step()
                self.assertFalse(window.auto_clock.isActive())
                self.assertTrue(window.load(ROOT/'puzzles/case-3x3-01.json'))
                self.assertTrue(window.hint_button.isEnabled())
                self.assertTrue(window.solver.step_button.isEnabled())
            finally:
                window.close();window.deleteLater();self.app.processEvents()

    def test_card_and_clue_selection_and_restart(self):
        QTest.mouseClick(self.window.cards['B1'],Qt.MouseButton.LeftButton)
        self.assertEqual(self.window.selected_cell,'B1')
        self.assertEqual(set(self.window.state.clues),{'A1','B2','C3'})
        QTest.mouseClick(self.window.cards['B2'],Qt.MouseButton.LeftButton);self.app.processEvents()
        self.assertEqual({c for c,w in self.window.cards.items() if w.counted},{'A2','C2','A3','B3','C3'})
        self.assertTrue(self.window.cards['B2'].anchor)
        QTest.mouseClick(self.window.cards['C3'],Qt.MouseButton.LeftButton);self.app.processEvents()
        self.assertEqual({c for c,w in self.window.cards.items() if w.counted},{'A1','B1','C1','A2','A3'})
        self.window.motion.setChecked(False)
        self.assertFalse(self.window.clock.isActive())
        self.window.restart();self.app.processEvents()
        self.assertIsNone(self.window.active_clue)
        self.assertEqual(len(self.window.cards),9)

    def test_only_dark_theme_preserves_selection(self):
        from griductive.ui.themes import THEMES
        self.assertEqual(set(THEMES),{'pixel'})
        self.assertFalse(hasattr(self.window,'theme_switch'))
        self.window.inspect_clue('A1');self.app.processEvents()

    def test_operand_hover_and_pin_never_change_result(self):
        self.window.inspect_clue('B2');self.app.processEvents()
        result={'A2','C2','A3','B3','C3'}
        inline=self.window.cards['B2'].clue_text
        self.assertIn('href="region.right"',inline.text())
        inline.linkHovered.emit('region.right');self.app.processEvents()
        self.assertEqual(self.window.preview_key,'region.right')
        self.assertEqual({c for c,w in self.window.cards.items() if w.preview_role=='b'},{'A1','B1','C1'})
        self.assertEqual({c for c,w in self.window.cards.items() if w.counted},result)
        inline.linkActivated.emit('region.right');self.window.hover_part('')
        self.assertEqual(self.window.preview_key,'region.right')
        self.assertEqual(self.window.pinned_key,'region.right')
        self.window.inspect_clue('A1')
        self.assertIsNone(self.window.pinned_key)
        self.assertFalse(any(w.preview_role for w in self.window.cards.values()))

    def test_selecting_clue_shows_both_regions_and_overlap_without_hover(self):
        self.window.select_person('B2');self.app.processEvents()
        cards=self.window.cards
        # DIFFERENCE(neighbors(B2), row(1)): top row belongs to A AND B,
        # but is excluded from the final counted set.
        self.assertEqual({c for c,w in cards.items() if 'a' in w.region_roles},set(self.window.state.board.cells)-{'B2'})
        self.assertEqual({c for c,w in cards.items() if 'b' in w.region_roles},{'A1','B1','C1'})
        self.assertEqual(cards['A1'].region_roles,('a','b'))
        self.assertFalse(cards['A1'].counted)
        self.assertFalse(cards['B2'].counted)
        self.assertTrue(cards['B2'].anchor)
        self.assertEqual({c for c,w in cards.items() if w.counted},{'A2','C2','A3','B3','C3'})
        self.assertFalse(any(w.dimmed for w in cards.values()))

    def test_union_shows_both_regions_and_counts_overlap_once(self):
        self.window.select_person('C3');self.app.processEvents();cards=self.window.cards
        self.assertEqual({c for c,w in cards.items() if 'a' in w.region_roles},{'A1','B1','C1'})
        self.assertEqual({c for c,w in cards.items() if 'b' in w.region_roles},{'A1','A2','A3'})
        self.assertEqual(cards['A1'].region_roles,('a','b'))
        self.assertEqual(len([w for w in cards.values() if w.counted]),5)

    def test_escape_clears_highlight_and_revealed_card_reopens_clue(self):
        QTest.keyClick(self.window.cards['B1'],Qt.Key.Key_Escape);self.app.processEvents()
        self.assertIsNone(self.window.active_clue)
        self.assertTrue(all(not w.counted and not w.anchor and not w.dimmed for w in self.window.cards.values()))
        QTest.mouseClick(self.window.cards['A1'],Qt.MouseButton.LeftButton)
        self.assertTrue(self.window.cards['A1'].clue_text.active)
        self.assertEqual(self.window.active_clue,'A1')

    def test_clue_is_inline_only_and_clicking_another_person_clears_previous(self):
        self.assertFalse(hasattr(self.window,'evidence'))
        self.assertFalse(hasattr(self.window,'source_choice'))
        self.assertFalse(hasattr(self.window,'details_button'))
        QTest.mouseClick(self.window.cards['A1'].clue_text,Qt.MouseButton.LeftButton)
        self.assertEqual(self.window.active_clue,'A1')
        self.assertIn('href=',self.window.cards['A1'].clue_text.text())
        self.assertNotIn('href=',self.window.cards['B2'].clue_text.text())
        QTest.mouseClick(self.window.cards['B1'],Qt.MouseButton.LeftButton)
        self.assertIsNone(self.window.active_clue)
        self.assertNotIn('href=',self.window.cards['A1'].clue_text.text())
        self.assertFalse(any(c.counted or c.dimmed for c in self.window.cards.values()))

    def test_all_region_colors_stay_visible_while_hovering_a_word(self):
        self.window.motion.setChecked(False);self.app.processEvents()
        before=self.window.cards['C1'].grab().toImage()
        self.window.inspect_clue('A1');self.app.processEvents()
        self.assertTrue(self.window.cards['C1'].counted)  # Metadata retained for later.
        self.assertNotEqual(before,self.window.cards['C1'].grab().toImage())
        self.window.inspect_clue('B2')
        overlap=self.window.cards['A1'].grab().toImage()
        colors={overlap.pixelColor(x,y).name().upper() for x in range(overlap.width()) for y in range(overlap.height())}
        self.assertIn(self.window.theme.operand_a.upper(),colors)
        self.assertIn(self.window.theme.operand_b.upper(),colors)
        self.window.hover_part('region.right')
        self.assertEqual(self.window.cards['A1'].grab().toImage(),overlap)
        self.window.hover_part('')
        self.assertEqual(self.window.cards['A1'].grab().toImage(),overlap)
        self.assertFalse(any(c.dimmed for c in self.window.cards.values()))
        self.assertIn('href=',self.window.cards['B2'].clue_text.text())

    def test_clues_scroll_without_resizing_any_card(self):
        self.window.resize(1050,760);QTest.qWait(80)
        before={c:w.size() for c,w in self.window.cards.items()}
        for cell in ('A1','B2','C3','B1'):
            self.window.select_person(cell);QTest.qWait(40)
            self.assertEqual({c:w.size() for c,w in self.window.cards.items() if c!=cell},
                             {c:size for c,size in before.items() if c!=cell})
            self.assertEqual(self.window.zoom_slot.size(),before[cell])
        heights=[w.height() for w in self.window.cards.values() if w is not self.window.zoom_card]+[self.window.zoom_slot.height()]
        self.assertLessEqual(max(heights)-min(heights),1)
        before={c:w.size() for c,w in self.window.cards.items()}
        card=self.window.cards['C3'];scroll=card.note_scroll
        card.clue='Lời khai dài cần đọc đầy đủ. '*30
        card.place_actions();self.app.processEvents()
        self.assertEqual({c:w.size() for c,w in self.window.cards.items()},before)
        self.assertGreater(scroll.verticalScrollBar().maximum(),0)
        scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
        self.assertGreater(scroll.verticalScrollBar().value(),0)
        self.assertLessEqual(scroll.geometry().bottom(),card.height())
        self.assertFalse(self.window.solver.isVisible())

    def test_mouse_can_hover_and_pin_a_word_inside_card(self):
        self.window.select_person('A1');QTest.qWait(30)
        inline=self.window.zoom_card.clue_text;hit=None
        # Discover a real link hit through Qt mouse events, not by emitting a signal.
        for y in range(7,min(inline.height(),60),8):
            for x in range(4,inline.width(),8):
                point=QPoint(x,y);QTest.mouseMove(inline,point);self.app.processEvents()
                if self.window.preview_key=='region':hit=point;break
            if hit is not None:break
        self.assertIsNotNone(hit,'Clue word must be mouse-accessible on the card.')
        QTest.mouseClick(inline,Qt.MouseButton.LeftButton,pos=hit);self.app.processEvents()
        self.assertEqual(self.window.pinned_key,'region')
        self.assertEqual(self.window.active_clue,'A1')

    def test_selected_card_enlarges_without_reflow_and_escape_closes_it(self):
        from griductive.ui.cards import PortraitCard
        self.assertIsNone(self.window.zoom_card)
        original=self.window.cards['A1']
        before={cell:card.geometry() for cell,card in self.window.cards.items()}
        QTest.mouseClick(self.window.cards['A1'],Qt.MouseButton.LeftButton)
        self.app.processEvents()
        zoom=self.window.zoom_card
        self.assertIs(zoom,original)
        self.assertEqual(len(self.window.findChildren(PortraitCard)),9)
        self.assertTrue(zoom.isVisible())
        self.assertAlmostEqual(zoom.width()/before['A1'].width(),1.10,places=2)
        self.assertAlmostEqual(zoom.height()/before['A1'].height(),1.10,places=2)
        self.assertEqual({cell:card.geometry() for cell,card in self.window.cards.items() if cell!='A1'},
                         {cell:rect for cell,rect in before.items() if cell!='A1'})
        QTest.mouseClick(self.window.cards['C3'],Qt.MouseButton.LeftButton)
        self.assertEqual(self.window.zoom_card.character.cell,'C3')
        self.assertEqual(original.geometry(),before['A1'])
        self.window.resize(1050,760);QTest.qWait(50)
        self.assertTrue(self.window.desk.rect().contains(self.window.zoom_card.geometry()))
        QTest.keyClick(self.window.zoom_card,Qt.Key.Key_Escape);self.app.processEvents()
        self.assertIsNone(self.window.zoom_card)
        self.assertIsNone(self.window.selected_cell)
        self.assertTrue(all(card.parentWidget() is self.window.desk for card in self.window.cards.values()))

    def test_verdict_from_enlarged_card_updates_game_and_revealed_clue(self):
        from griductive.engine.game import LogicAgent
        self.window.load(ROOT/'puzzles/case-3x3-01.json')
        cell,verdict=LogicAgent(self.window.clues).next_verdict(self.window.state)
        QTest.mouseClick(self.window.cards[cell],Qt.MouseButton.LeftButton)
        control=self.window.zoom_card.verdict_buttons[verdict.title()]
        self.assertTrue(control.isVisible())
        QTest.mouseClick(control,Qt.MouseButton.LeftButton);self.wait_engine()
        self.assertEqual(self.window.state.statuses[cell],verdict)
        self.assertEqual(self.window.zoom_card.status,verdict)
        self.assertTrue(self.window.zoom_card.clue_text.isVisible())
        self.assertFalse(self.window.zoom_card.actions.isVisible())

    def test_real_region_click_changes_spotlight_without_hover_changing_it(self):
        self.window.select_person('C3')
        before=self.window.state
        self.assertEqual({c for c,w in self.window.cards.items() if w.dimmed},{'B2','C2','B3'})
        inline=self.window.cards['C3'].clue_text;hit=None
        for y in range(5,min(inline.height(),90),6):
            for x in range(3,inline.width(),6):
                point=QPoint(x,y);QTest.mouseMove(inline,point);self.app.processEvents()
                if self.window.preview_key=='region.right':hit=point;break
            if hit is not None:break
        self.assertIsNotNone(hit)
        # Hover alone still leaves both regions visible.
        self.assertEqual({c for c,w in self.window.cards.items() if w.dimmed},{'B2','C2','B3'})
        QTest.mouseClick(inline,Qt.MouseButton.LeftButton,pos=hit)
        self.assertEqual(self.window.pinned_key,'region.right')
        self.assertEqual({c for c,w in self.window.cards.items() if not w.dimmed},{'A1','A2','A3','C3'})
        self.assertAlmostEqual(self.window.cards['B1'].fade_effect.opacity(),.28)
        self.assertEqual(self.window.cards['A1'].region_roles,('b',))
        self.assertIs(self.window.state,before)
        self.window.select_person('C3')
        self.assertIsNone(self.window.pinned_key)
        self.assertEqual(self.window.cards['A1'].region_roles,('a','b'))

    def test_one_click_on_clue_does_not_also_trigger_its_parent_card(self):
        self.window.select_person('C3')
        inline=self.window.cards['C3'].clue_text;hit=None
        for y in range(5,min(inline.height(),90),6):
            for x in range(3,inline.width(),6):
                point=QPoint(x,y);QTest.mouseMove(inline,point);self.app.processEvents()
                if self.window.preview_key=='region.left':hit=point;break
            if hit is not None:break
        self.assertIsNotNone(hit)
        with patch.object(self.window,'pulse_regions',wraps=self.window.pulse_regions) as pulse:
            QTest.mouseClick(inline,Qt.MouseButton.LeftButton,pos=hit)
            self.assertEqual(pulse.call_count,1)
            self.assertEqual(self.window.pinned_key,'region.left')
        self.window.clear_selection()
        with patch.object(self.window,'pulse_regions',wraps=self.window.pulse_regions) as pulse:
            QTest.mouseClick(inline,Qt.MouseButton.LeftButton,pos=QPoint(5,5))
            self.assertEqual(pulse.call_count,1)
            self.assertIsNone(self.window.pinned_key)

    def test_region_bounce_finishes_once_and_rapid_switch_cancels_old_group(self):
        self.window.motion.setChecked(True)
        self.window.select_person('C3')
        slots={cell:slot.geometry() for cell,slot in self.window.card_slots.items()}
        QTest.qWait(130)
        card=self.window.cards['B1'];slot=self.window.card_slots['B1']
        self.assertGreater(card.width(),slot.width())
        self.assertGreater(card.feedback.pop,0.)
        self.assertEqual({cell:s.geometry() for cell,s in self.window.card_slots.items()},slots)
        QTest.qWait(350)
        self.assertEqual(card.size(),slot.size())
        self.assertEqual(card.feedback.pop,0.)
        self.window.pin_part('region.left');QTest.qWait(80)
        self.assertGreater(card.feedback.pop,0.)
        self.window.pin_part('region.right')
        self.assertEqual(card.feedback.pop,0.)
        self.assertTrue(card.dimmed)
        QTest.qWait(230)
        self.assertAlmostEqual(card.fade_effect.opacity(),.28,places=2)
        # Clicking the same word replays its group's pulse.
        self.window.pin_part('region.right');QTest.qWait(80)
        self.assertGreater(self.window.cards['A3'].feedback.pop,0.)
        self.window.motion.setChecked(False)
        self.assertTrue(all(c.feedback.pop==0 for c in self.window.cards.values()))
        self.assertFalse(self.window.clock.isActive())
        self.window.clear_selection()
        self.assertTrue(all(c.fade_effect.opacity()==1 for c in self.window.cards.values()))

    def test_corner_zoom_keeps_its_original_center_and_fits_the_window(self):
        def rect(cell):
            card=self.window.cards[cell]
            return QRect(card.mapTo(self.window.desk,QPoint()),card.size())
        for size in (3,5):
            self.window.load(ROOT/f'puzzles/case-{size}x{size}-01.json')
            last=chr(64+size)
            for width,height in ((1500,900),(1050,760)):
                self.window.resize(width,height);QTest.qWait(40)
                for cell in ('A1',last+'1','A'+str(size),last+str(size)):
                    with self.subTest(size=size,window=(width,height),cell=cell):
                        self.window.select_person(cell);self.app.processEvents()
                        selected=rect(cell)
                        slot=self.window.card_slots[cell]
                        base=QRect(slot.mapTo(self.window.desk,QPoint()),slot.size())
                        self.assertLessEqual(abs(selected.center().x()-base.center().x()),1)
                        self.assertLessEqual(abs(selected.center().y()-base.center().y()),1)
                        self.assertTrue(self.window.desk.rect().contains(selected))

    def test_solver_panel_opens_only_on_request_without_fake_solving(self):
        before=self.window.state
        self.assertFalse(self.window.solver.isVisible())
        self.assertFalse(self.window.auto_button.isVisible())
        self.assertIn(self.window.solve_action,self.window.tools_menu.actions())
        self.window.solve_action.trigger();self.app.processEvents()
        self.assertTrue(self.window.solver.isVisible())
        self.assertIs(self.window.state,before)
        self.window.restart();self.app.processEvents()
        self.assertFalse(self.window.solver.isVisible())

    def test_load_larger_board_then_restart_original_without_stale_widgets(self):
        cells=[f'{chr(65+c)}{r+1}' for r in range(5) for c in range(5)]
        roster=json.loads((ROOT/'assets/characters/characters.json').read_text(encoding='utf-8'))
        data={'schema_version':1,'puzzle_id':'layout-fixture','title':'Kiểm tra bố cục 5×5','size':5,
            'characters':[dict(roster[i],cell=c) for i,c in enumerate(cells)],
            'solution':{c:'INNOCENT' for c in cells},'initially_revealed':['A1','E5'],
            'clues':{c:{'id':c,'type':'FACT','person':c,'status':'INNOCENT'} for i,c in enumerate(cells)}}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'layout.json';path.write_text(json.dumps(data),encoding='utf-8')
            self.assertTrue(self.window.load(path));self.app.processEvents()
            self.assertEqual(len(self.window.cards),25)
            self.assertEqual({c.character.portrait for c in self.window.cards.values()},set(range(25)))
            for card in self.window.cards.values():
                self.assertEqual(len(card.expression_frames),7)
                self.assertIs(card.expression_frames,self.window.expression_bank[card.character.portrait])
                self.assertTrue(all(frame.hasAlphaChannel() for frame in card.expression_frames))
                self.assertNotEqual(card.expression_frames[0].toImage(),card.expression_frames[1].toImage())
            self.assertEqual(len({p.toImage().cacheKey() for p in self.window.portraits}),25)
            self.assertTrue(all(p.hasAlphaChannel() for p in self.window.portraits))
            self.assertEqual(len(self.window.state.clues),2)
            self.window.resize(1900,1400);QTest.qWait(100)
            self.assertTrue(self.window.load(ROOT/'tests/fixtures/prototype-3x3.json'));self.app.processEvents()
            self.assertEqual(len(self.window.cards),9)
            self.assertIsNone(self.window.active_clue)

    def test_pixel_only_defaults(self):
        self.assertFalse(hasattr(self.window,'style_button'))
        self.assertEqual(self.window.theme_key,'pixel')
        self.assertTrue(all(c.pixel_style for c in self.window.cards.values()))

    def test_real_verdict_controls_and_step_solver(self):
        from griductive.engine.game import LogicAgent
        self.window.load(ROOT/'puzzles/case-3x3-01.json')
        before=self.window.state
        initial_count=len(before.statuses)
        cell,verdict=LogicAgent(self.window.clues).next_verdict(before)
        self.window.select_person(cell)
        control=self.window.cards[cell].verdict_buttons[verdict.title()]
        with patch.object(self.window,'show_notice'):
            QTest.mouseClick(control,Qt.MouseButton.LeftButton)
            self.wait_engine()
            self.assertEqual(self.window.state.statuses[cell],verdict)
            self.assertIn(cell,self.window.state.clues)
            while not self.window.engine.solved:
                self.window.solve_step()
                self.wait_engine()
        self.assertEqual(len(self.window.state.statuses),9)
        self.assertEqual(len(self.window.engine.trace),9-initial_count)
        self.assertFalse(self.window.auto_clock.isActive())

    def test_failed_load_retains_session(self):
        before=self.window.state
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'invalid.json';path.write_text('{}',encoding='utf-8')
            with patch.object(self.window,'show_notice') as warning:
                self.assertFalse(self.window.load(path));warning.assert_called_once()
        self.assertIs(self.window.state,before)
        self.assertEqual(len(self.window.cards),9)

    def test_hint_uses_the_game_dialog_and_closing_it_does_not_reveal_a_card(self):
        from griductive.engine.game import LogicAgent
        before=self.window.state
        cell,_=LogicAgent(self.window.clues).next_verdict(before)
        QTest.mouseClick(self.window.hint_button,Qt.MouseButton.LeftButton);self.wait_engine()
        dialog=self.window.notice
        self.assertTrue(dialog.isVisible())
        self.assertTrue(dialog.windowFlags() & Qt.WindowType.FramelessWindowHint)
        self.assertEqual(dialog.windowModality(),Qt.WindowModality.WindowModal)
        self.assertTrue(self.window.notice_overlay.isVisible())
        self.assertEqual(self.window.selected_cell,cell)
        self.assertIs(self.window.state,before)
        QTest.mouseClick(dialog.action_button,Qt.MouseButton.LeftButton);self.app.processEvents()
        self.assertIsNone(self.window.notice)
        self.assertIsNone(self.window.notice_overlay)
        self.assertIs(self.window.state,before)

    def test_notice_escape_and_loading_a_new_case_clear_the_modal(self):
        self.window.show_notice('Gợi ý','Nội dung thử nghiệm.')
        QTest.keyClick(self.window.notice,Qt.Key.Key_Escape);self.app.processEvents()
        self.assertIsNone(self.window.notice)
        self.window.show_notice('Gợi ý','Nội dung thử nghiệm.')
        self.window.restart();self.app.processEvents()
        self.assertIsNone(self.window.notice)
        self.assertIsNone(self.window.notice_overlay)

    def test_entire_5x5_fits_in_window_without_board_scrolling(self):
        self.assertTrue(self.window.load(ROOT/'puzzles/case-5x5-01.json'))
        for width,height in ((1920,1000),(1366,768),(1050,760)):
            with self.subTest(size=(width,height)):
                self.window.resize(width,height);QTest.qWait(60)
                board=self.window.board_holder
                self.assertEqual(len(self.window.cards),25)
                for cell,card in self.window.cards.items():
                    self.assertTrue(board.rect().contains(self.window.card_slots[cell].geometry()))
                    position=card.mapTo(self.window,QPoint(0,0))
                    self.assertGreaterEqual(position.x(),0);self.assertGreaterEqual(position.y(),0)
                    self.assertLessEqual(position.y()+card.height(),self.window.height())
                heights=[c.height() for c in self.window.cards.values() if c is not self.window.zoom_card]
                self.assertLessEqual(max(heights)-min(heights),1)
                self.window.select_person('A5');self.app.processEvents()
                card=self.window.cards['A5']
                self.assertLessEqual(card.note_scroll.geometry().bottom(),card.height())

    def test_portrait_motion_changes_pixels_and_can_stop(self):
        self.window.motion.setChecked(True)
        card=self.window.cards['A1']
        self.assertEqual(len(card.expression_frames),7)
        card.expression.arrival=1.;card.expression.elapsed=1.;self.app.processEvents()
        before=card.grab().toImage()
        QTest.mouseClick(card,Qt.MouseButton.LeftButton);self.app.processEvents()
        QTest.qWait(90)
        self.assertNotEqual(before,card.grab().toImage())
        self.window.motion.setChecked(False);self.app.processEvents()
        stopped=card.grab().toImage();QTest.qWait(150)
        self.assertEqual(stopped,card.grab().toImage())

    def test_blink_keeps_card_geometry_fixed(self):
        self.window.motion.setChecked(True)
        self.window.clock.stop()
        card=self.window.cards['B1'];card.expression.arrival=1.;card.expression.reaction=0.
        card.expression.elapsed=1.;before=card.grab().toImage();size=card.size()
        card.expression.elapsed=4.21;after=card.grab().toImage()
        self.assertEqual(card.expression.frame,0)
        self.assertNotEqual(before,after)
        self.assertEqual(card.size(),size)


if __name__=='__main__':unittest.main()
