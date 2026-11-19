"""Public-only, stateless gameplay and real Dash HTTP callback coverage."""
import base64
import json
import unittest
from copy import deepcopy
from unittest.mock import patch

from griductive.engine import GameEngine, PuzzleError, SolverCancelled, SolverTimeout
from griductive.web import create_app
from griductive.web_game import ROOT, new_session, restore, transition


class WebSessionTests(unittest.TestCase):
    def test_hint_and_rejected_verdict_do_not_open_a_card(self):
        initial = new_session()
        hint, engine = transition(initial, 'hint')
        self.assertEqual(hint['selected'], 'A3')
        self.assertEqual(hint['history'], [])
        self.assertNotIn('A3', engine.public_state().clues)
        rejected, engine = transition(hint, 'verdict', 'INNOCENT')
        self.assertIn('CONTRADICTED', rejected['notice'])
        self.assertEqual(rejected['history'], [])
        self.assertNotIn('A3', engine.public_state().clues)
        self.assertEqual(initial, new_session())

    def test_public_history_survives_new_invocation_without_shared_mutable_state(self):
        state, engine = transition(new_session(), 'step')
        self.assertEqual(state['history'], [{'cell': 'A3', 'verdict': 'CRIMINAL'}])
        rebuilt = restore(json.loads(json.dumps(state)))
        self.assertEqual(rebuilt.public_state(), engine.public_state())
        self.assertEqual(len(rebuilt.trace), 1)
        self.assertNotIn('A3', restore(new_session()).public_state().statuses)
        while not engine.solved:
            state, engine = transition(state, 'step')
        self.assertEqual(len(state['history']), 7)
        self.assertEqual(len(restore(state).trace), 7)
        restarted, engine = transition(state, 'restart')
        self.assertEqual(restarted['history'], [])
        self.assertEqual(set(engine.public_state().statuses), {'B1', 'C1'})

    def test_browser_cannot_forge_proof_history_or_paths(self):
        for history in ([{'cell': 'A1', 'verdict': 'CRIMINAL'}],
                        [{'cell': 'A3', 'verdict': 'INNOCENT'}],
                        [{'cell': 'B1', 'verdict': 'CRIMINAL'}]):
            with self.subTest(history=history), self.assertRaises(PuzzleError):
                restore(dict(new_session(), history=history))
        with self.assertRaises(PuzzleError):
            restore(new_session('../../docs/team'))

    def test_upload_validation_and_timeout_preserve_original_session(self):
        raw = (ROOT / 'puzzles/case-4x4-01.json').read_bytes()
        contents = 'data:application/json;base64,' + base64.b64encode(raw).decode()
        state, engine = transition(new_session(), 'upload', contents)
        self.assertEqual(engine.public_state().board.size, 4)
        self.assertEqual(state['history'], [])
        with self.assertRaises(PuzzleError):
            transition(state, 'upload', 'invalid')
        original = deepcopy(state)
        with patch.object(GameEngine, 'step', side_effect=SolverCancelled('timeout')):
            with self.assertRaises(SolverTimeout):
                transition(state, 'step')
        self.assertEqual(state, original)


class WebHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True

    def setUp(self):
        self.client = self.app.test_client()

    def callback(self, state, trigger, puzzle='case-3x3-01'):
        dashboard = self.app.extensions['griductive_dash']
        key, callback = next(iter(dashboard.callback_map.items()))
        values = {'puzzle': puzzle, 'upload': None, 'clock': 0}
        inputs = []
        for item in callback['inputs']:
            identifier = item['id']
            value = [] if identifier.startswith('{') else values.get(identifier, 1 if identifier == trigger else 0)
            inputs.append(dict(item, value=value))
        response = self.client.post('/_dash-update-component', json={
            'output': key,
            'outputs': [{'id': output.component_id, 'property': output.component_property}
                        for output in callback['output']],
            'inputs': inputs,
            'state': [{'id': 'session', 'property': 'data', 'value': state}],
            'changedPropIds': [f'{trigger}.n_clicks'] if trigger else [],
        })
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return response.get_json()['response']

    def test_layout_assets_and_hidden_files(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        layout = self.client.get('/_dash-layout')
        self.assertEqual(layout.status_code, 200)
        self.assertNotIn('solution', layout.get_data(as_text=True))
        self.assertEqual(self.client.get('/health').json, {'status': 'ok'})
        for path in ('/puzzles/case-3x3-01.json', '/Report.pdf', '/images/secret.json'):
            with self.subTest(path=path):
                # Dash's catch-all may serve its shell, but must never return source data.
                response = self.client.get(path)
                self.assertNotIn('"solution"', response.get_data(as_text=True))
                self.assertNotEqual(response.mimetype, 'application/pdf')
        response = self.client.get('/images/pixel-desk.png')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'image/png')
        response.close()
        for svg_name in ('backdrop.svg', 'portrait-0.svg', 'silhouette-0.svg'):
            svg_res = self.client.get(f'/images/{svg_name}')
            self.assertEqual(svg_res.status_code, 200)
            self.assertEqual(svg_res.mimetype, 'image/svg+xml')
            svg_res.close()

    def test_real_dash_callback_proves_a_move_and_keeps_solution_on_server(self):
        response = self.callback(new_session(), 'step')
        state = response['session']['data']
        self.assertEqual(state['history'], [{'cell': 'A3', 'verdict': 'CRIMINAL'}])
        self.assertNotIn('solution', json.dumps(response))
        self.assertIn('3/9', response['progress']['children'])
        hinted = self.callback(new_session(), 'hint')['session']['data']
        self.assertEqual(hinted['selected'], 'A3')
        self.assertEqual(hinted['history'], [])

    def test_vector_board_renders_split_verdicts_links_and_5x5(self):
        # Selecting an unopened suspect renders the flush 50/50 split verdict bar
        sel_state = dict(new_session(), selected='B2')
        res = self.callback(sel_state, '')
        board_json = json.dumps(res['board']['children'], ensure_ascii=False)
        self.assertIn('card-verdict', board_json)
        self.assertIn('Vô tội', board_json)
        self.assertIn('Tội phạm', board_json)
        # Selecting an opened clue renders inline clickable region buttons
        clue_state = dict(new_session(), selected='B1')
        res_clue = self.callback(clue_state, '')
        self.assertIn('"kind": "region"', json.dumps(res_clue['board']['children']))
        # 5x5 board renders cleanly
        res_5x5 = self.callback(new_session('case-5x5-01'), 'puzzle', puzzle='case-5x5-01')
        self.assertIn('3/25', res_5x5['progress']['children'])
        # Menu & Journal toggles update style cleanly
        toggled = self.callback(new_session(), 'menu-toggle')
        self.assertTrue(toggled['session']['data']['menu_open'])
        j_open = self.callback(toggled['session']['data'], 'journal-toggle')
        self.assertTrue(j_open['session']['data']['journal_open'])

