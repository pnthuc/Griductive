import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel
from griductive.ui import Window, configure_app, ROOT


class JournalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        configure_app(cls.app)

    def setUp(self):
        self.window = Window()
        self.window.show()
        self.window.motion.setChecked(False)
        self.window.open_solver()
        QTest.qWait(30)
        self.journal = self.window.solver

    def wait_engine(self):
        import time
        deadline=time.monotonic()+10
        while self.window.controller.busy and time.monotonic()<deadline:
            QTest.qWait(5)
        self.assertFalse(self.window.controller.busy,'Background request did not finish')
        self.app.processEvents()

    def tearDown(self):
        self.journal.close()
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def step(self):
        with patch.object(self.window, 'show_notice'):
            QTest.mouseClick(self.journal.step_button, Qt.MouseButton.LeftButton)
            self.wait_engine()
        QTest.qWait(20)

    def test_step_records_the_real_verdict_and_details_do_not_change_the_game(self):
        before = len(self.window.state.statuses)
        self.assertTrue(self.journal.empty.isVisible())
        self.assertFalse(self.journal.export_button.isEnabled())
        self.step()
        self.assertEqual(len(self.window.state.statuses), before + 1)
        self.assertEqual(len(self.journal.entries), 1)
        row = self.journal.entries[0]
        self.assertIs(row.entry, self.window.engine.trace[0])
        self.assertFalse(row.details.isVisible())
        state = self.window.state
        QTest.mouseClick(row.details_button, Qt.MouseButton.LeftButton)
        self.assertTrue(row.details.isVisible())
        details = '\n'.join(item.text() for item in row.details.findChildren(QLabel))
        self.assertIn('Mâu thuẫn (UNSAT)', details)
        self.assertIn(self.window.cards[row.entry['cell']].clue, details)
        self.assertIn('Ben (B1)', details)
        self.assertIn('Cara (C1)', details)
        self.assertNotIn('C02', details)
        self.assertNotIn('C03', details)
        self.assertIs(self.window.state, state)

    def test_run_pause_close_and_completion_keep_controls_in_sync(self):
        before = self.window.state
        QTest.mouseClick(self.journal.play_button, Qt.MouseButton.LeftButton)
        self.assertTrue(self.window.auto_clock.isActive())
        self.assertFalse(self.journal.step_button.isEnabled())
        self.assertEqual(self.journal.play_button.text(), 'Tạm dừng')
        QTest.mouseClick(self.journal.play_button, Qt.MouseButton.LeftButton)
        self.assertFalse(self.window.auto_clock.isActive())
        self.assertTrue(self.journal.step_button.isEnabled())
        self.assertIs(self.window.state, before)
        QTest.mouseClick(self.journal.play_button, Qt.MouseButton.LeftButton)
        QTest.mouseClick(self.journal.close_button, Qt.MouseButton.LeftButton)
        self.assertFalse(self.window.auto_clock.isActive())
        self.assertFalse(self.journal.isVisible())
        self.window.open_solver()
        with patch.object(self.window, 'show_notice'):
            while not self.window.engine.solved:
                self.window.solve_step()
                self.wait_engine()
        self.assertEqual(len(self.journal.entries), len(self.window.engine.trace))
        self.assertTrue(self.journal.complete)
        self.assertFalse(self.journal.play_button.isEnabled())
        self.assertFalse(self.journal.step_button.isEnabled())
        self.window.restart()
        self.assertFalse(self.journal.entries)
        self.assertFalse(self.journal.complete)
        self.assertFalse(self.journal.isVisible())

    def test_export_preserves_the_full_machine_readable_trace(self):
        self.step()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'trace.json'
            with patch('griductive.ui.window.QFileDialog.getSaveFileName', return_value=(str(path), 'JSON (*.json)')):
                QTest.mouseClick(self.journal.export_button, Qt.MouseButton.LeftButton)
            self.assertEqual(json.loads(path.read_text(encoding='utf-8')), self.window.engine.trace)

    def test_long_details_fit_and_new_steps_preserve_a_readers_scroll_position(self):
        self.journal.setFloating(True)
        self.journal.resize(400, 580)
        for _ in range(4):
            self.step()
        row = self.journal.entries[-1]
        row.details_button.setChecked(True)
        for width in (360, 460, 400):
            self.journal.resize(width, 580)
            QTest.qWait(30)
            for text in row.details.findChildren(QLabel):
                self.assertGreaterEqual(text.height(), text.heightForWidth(text.width()))
            self.assertEqual(self.journal.scroll.horizontalScrollBar().maximum(), 0)
        bar = self.journal.scroll.verticalScrollBar()
        self.journal.scroll_to_latest()
        self.assertEqual(bar.value(), bar.maximum())
        bar.setValue(0)
        self.step()
        self.assertEqual(bar.value(), 0)
        self.assertTrue(self.journal.latest_button.isVisible())
        QTest.mouseClick(self.journal.latest_button, Qt.MouseButton.LeftButton)
        self.assertEqual(bar.value(), bar.maximum())


if __name__ == '__main__':
    unittest.main()
