"""Unit tests for the experiment runner, offline uniqueness statuses, and session isolation."""
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from griductive.engine import (
    GameEngine, LogicAgent, clue_registry, load_puzzle, region_registry,
)
from griductive.engine.game import check_uniqueness
from griductive.engine.sat import SolverTimeout
from griductive.experiments import main as experiments_main, run_case

ROOT = Path(__file__).resolve().parents[1]


class ExperimentRunnerTests(unittest.TestCase):
    def setUp(self):
        self.registry = clue_registry(region_registry())
        self.case_3x3 = ROOT / 'puzzles/case-3x3-01.json'

    def test_run_case_ordered_and_frequency_reach_identical_final_kb(self):
        ordered, trace_o = run_case(self.case_3x3, 'ordered')
        frequency, trace_f = run_case(self.case_3x3, 'frequency')
        for row in (ordered, frequency):
            self.assertEqual(row['status'], 'SOLVED')
            self.assertEqual(row['uniqueness'], 'UNIQUE')
            self.assertEqual(row['steps'], 7)
        for key in ('primary_variables', 'auxiliary_variables', 'clauses', 'steps'):
            self.assertEqual(ordered[key], frequency[key])
        self.assertEqual([e['cell'] for e in trace_o], [e['cell'] for e in trace_f])

    def test_run_case_records_timeout_instead_of_dropping_row(self):
        result, _ = run_case(self.case_3x3, 'ordered', timeout=0.0)
        self.assertEqual(result['puzzle'], 'case-3x3-01')
        self.assertEqual(result['status'], 'TIMEOUT')
        self.assertGreaterEqual(result['runtime'], 0.0)

    def test_run_case_records_uniqueness_timeout_gracefully(self):
        with patch('griductive.experiments.check_uniqueness', side_effect=SolverTimeout('limit')):
            result, _ = run_case(self.case_3x3, 'ordered')
        self.assertEqual(result['status'], 'SOLVED')
        self.assertEqual(result['uniqueness'], 'TIMEOUT')

    def test_run_case_preserves_unknown_terminal_state(self):
        data = json.loads(self.case_3x3.read_text(encoding='utf-8'))
        # Replace opened clues with tautological/weak clues so no next cell is forced.
        for cell in data['initially_revealed']:
            data['clues'][cell] = {
                'id': cell,
                'type': 'AT_LEAST',
                'k': 0,
                'region': {'type': 'ROW', 'row': 1},
            }
        with tempfile.TemporaryDirectory() as tmp:
            stalled_path = Path(tmp) / 'stalled.json'
            stalled_path.write_text(json.dumps(data), encoding='utf-8')
            result, trace = run_case(stalled_path, 'ordered')
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['steps'], 0)
        self.assertEqual(trace, [])

    def test_check_uniqueness_detects_multiple_solutions(self):
        data = json.loads(self.case_3x3.read_text(encoding='utf-8'))
        for cell in data['clues']:
            data['clues'][cell] = {
                'id': cell,
                'type': 'AT_LEAST',
                'k': 0,
                'region': {'type': 'CORNERS'},
            }
        with tempfile.TemporaryDirectory() as tmp:
            ambiguous = Path(tmp) / 'multiple.json'
            ambiguous.write_text(json.dumps(data), encoding='utf-8')
            puzzle = load_puzzle(ambiguous, self.registry)
        self.assertEqual(check_uniqueness(puzzle, self.registry), 'MULTIPLE')

    def test_check_uniqueness_detects_inconsistent_clue_set(self):
        puzzle = load_puzzle(self.case_3x3, self.registry)
        contradictory = dict(puzzle.clues)
        contradictory['A1'] = {'id': 'A1', 'type': 'FACT', 'person': 'B1', 'status': 'CRIMINAL'}
        contradictory['A2'] = {'id': 'A2', 'type': 'FACT', 'person': 'B1', 'status': 'INNOCENT'}
        broken = type(puzzle)(
            puzzle.puzzle_id, puzzle.title, puzzle.board,
            puzzle.characters, puzzle.solution, contradictory, puzzle.initially_revealed,
        )
        self.assertEqual(check_uniqueness(broken, self.registry), 'INCONSISTENT')

    def test_fork_isolates_tentative_session_state_and_trace(self):
        puzzle = load_puzzle(self.case_3x3, self.registry)
        original = GameEngine(puzzle, self.registry)
        forked = original.fork()
        step_res = forked.step()
        self.assertEqual(step_res['result'], 'ACCEPTED')
        self.assertEqual(len(forked.trace), 1)
        self.assertEqual(len(original.trace), 0)
        self.assertNotEqual(forked.public_state().statuses, original.public_state().statuses)

    def test_verify_rejects_invalid_verdict_label(self):
        puzzle = load_puzzle(self.case_3x3, self.registry)
        engine = GameEngine(puzzle, self.registry)
        agent = LogicAgent(self.registry)
        with self.assertRaises(ValueError):
            agent.verify(engine.public_state(), 'A1', 'MAYBE')

    def test_cli_writes_csv_json_and_trace_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / 'exp'
            with patch('griductive.experiments.ROOT', Path(tmp)):
                puzzles_dir = Path(tmp) / 'puzzles'
                puzzles_dir.mkdir()
                (puzzles_dir / 'case-3x3-01.json').write_bytes(self.case_3x3.read_bytes())
                with patch.object(sys, 'argv', ['experiments', '--output', str(out_dir), '--timeout', '15']):
                    experiments_main()
            rows = json.loads((out_dir / 'results.json').read_text(encoding='utf-8'))
            self.assertEqual(len(rows), 2)
            with (out_dir / 'results.csv').open(encoding='utf-8') as f:
                csv_rows = list(csv.DictReader(f))
            self.assertEqual(len(csv_rows), 2)
            self.assertTrue((out_dir / 'case-3x3-01-ordered-trace.json').is_file())
            self.assertTrue((out_dir / 'case-3x3-01-frequency-trace.json').is_file())
