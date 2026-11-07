import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import time
import unittest
from threading import Event
from unittest.mock import patch
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from griductive.ui.game_controller import GameController
from griductive.engine.game import GameEngine
from griductive.engine.models import load_puzzle
from griductive.engine.clues import clue_registry
from griductive.engine.regions import region_registry
from griductive.ui.assets import ROOT


class BackgroundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.registry=clue_registry(region_registry())
        self.engine=GameEngine(load_puzzle(ROOT/'puzzles/case-3x3-01.json',self.registry),self.registry)
        self.controller=GameController()
        self.controller.replace(self.engine)
        self.results=[]
        self.errors=[]
        self.controller.finished.connect(lambda *r:self.results.append(r))
        self.controller.failed.connect(self.errors.append)

    def tearDown(self):
        self.controller.shutdown()
        self.controller.deleteLater()
        self.app.processEvents()

    def until(self, condition):
        end=time.monotonic()+5
        while not condition() and time.monotonic()<end:QTest.qWait(5)
        self.assertTrue(condition())

    def test_requests_without_a_session_or_after_shutdown_are_rejected(self):
        controller=GameController()
        try:
            self.assertFalse(controller.request('step'))
            with self.assertRaises(ValueError):controller.request('unknown')
            controller.shutdown()
            self.assertFalse(controller.request('hint'))
            controller.shutdown()
            self.assertFalse(controller.busy)
        finally:
            controller.shutdown();controller.deleteLater()

    def test_worker_reports_setup_failure_and_can_handle_the_next_request(self):
        original=GameEngine.fork
        first=[True]
        def fail_once(engine):
            if first[0]:
                first[0]=False
                raise RuntimeError('Deliberate setup failure')
            return original(engine)
        with patch.object(GameEngine,'fork',fail_once):
            self.controller.request('step')
            self.until(lambda:not self.controller.busy)
            self.assertEqual(len(self.errors),1)
            self.assertFalse(self.controller.view.trace)
            self.controller.request('step')
            self.until(lambda:not self.controller.busy)
        self.assertEqual(len(self.results),1)
        self.assertEqual(len(self.controller.view.trace),1)

    def test_ui_events_continue_and_cancelled_commit_is_discarded(self):
        entered,release=Event(),Event()
        original=GameEngine.step
        first=[True]
        def delayed(engine,**kwargs):
            # Deliberately finish a candidate before cancellation, exercising
            # the publication race rather than just cancelling a SAT query.
            result=original(engine)
            if first[0]:
                first[0]=False
                entered.set()
                release.wait(3)
            return result
        pulses=[]
        timer=QTimer();timer.setInterval(5);timer.timeout.connect(lambda:pulses.append(True))
        timer.start()
        try:
            with patch.object(GameEngine,'step',delayed):
                self.controller.request('step')
                self.until(entered.is_set)
                QTest.qWait(40)
                self.assertGreater(len(pulses),2)
                self.controller.cancel()
                release.set()
                self.controller.request('step')
                self.until(lambda:not self.controller.busy)
            self.assertFalse(self.errors)
            self.assertEqual(len(self.results),1)
            self.assertEqual(len(self.controller.view.trace),1)
            self.assertEqual(len(self.engine.trace),0)
        finally:
            release.set();timer.stop()

    def test_replacement_drops_results_from_the_previous_game(self):
        entered,release=Event(),Event()
        original=GameEngine.hint
        def delayed(engine,**kwargs):
            entered.set();release.wait(3)
            return original(engine,**kwargs)
        try:
            with patch.object(GameEngine,'hint',delayed):
                self.controller.request('hint')
                self.until(entered.is_set)
                new=GameEngine(load_puzzle(ROOT/'puzzles/case-3x3-02.json',self.registry),self.registry)
                self.controller.replace(new)
                release.set()
            self.controller.request('hint')
            self.until(lambda:not self.controller.busy)
            self.assertEqual(len(self.results),1)
            self.assertEqual(self.controller.view.state.puzzle_id,'case-3x3-02')
            self.assertFalse(self.controller.view.trace)
            self.assertFalse(self.errors)
        finally:release.set()
