"""Extensions exercise the public API all the way to deduction and display."""
import itertools
import re
import unittest

from griductive.engine import (
    Board, Clue, LogicAgent, PuzzleError, Region, clue_parts, clue_registry,
    region_registry,
)
from griductive.engine.models import PublicState, freeze
from griductive.engine.cnf import Encoder
from griductive.engine.sat import solve
from griductive.presentation.wording_vi import clue_html, clue_text
from griductive.ui.themes import THEMES


def extension_catalog():
    regions = region_registry()

    @regions.register('CROSS')
    class Cross(Region):
        anchor_fields = ('cell',)

        def resolve(self, spec, board, regions, depth):
            row, column = board.position(spec['cell'])
            return {cell for cell in board.cells
                    if abs(board.position(cell)[0] - row)
                    + abs(board.position(cell)[1] - column) == 1}

        def describe(self, spec, board, regions):
            return f'những người kề ngang/dọc {spec["cell"]}'

        def wording(self, spec, text, key, role):
            return (text.token(key, 'những người kề ', role, True)
                    + text.person(spec['cell'], key + '.anchor.' + spec['cell'], 'anchor'))

    clues = clue_registry(regions)

    @clues.register('ALL_INNOCENT')
    class AllInnocent(Clue):
        region_fields = ('region',)

        def evaluate(self, spec, assignment, board, clues):
            return all(not assignment[cell]
                       for cell in clues.regions.resolve(spec['region'], board))

        def expression(self, spec, encoder, clues):
            cells = clues.regions.resolve(spec['region'], encoder.board)
            return encoder.gate('AND', (-encoder.variables[cell] for cell in cells))

        def describe(self, spec, board, clues):
            return clues.regions.describe(spec['region'], board) + ' đều vô tội.'

        def wording(self, spec, text):
            return text.region(spec['region']) + ' đều vô tội.'

    return regions, clues, Cross, AllInnocent


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.board = Board(3)
        self.regions, self.clues, self.Cross, self.AllInnocent = extension_catalog()
        self.custom = {'type': 'ALL_INNOCENT',
                       'region': {'type': 'CROSS', 'cell': 'B2'}}

    def test_one_definition_supports_deduction_and_reference_metadata(self):
        state = PublicState('custom', 'custom', self.board, (), freeze({}),
                            freeze({'A1': self.custom}))
        classified = LogicAgent(self.clues).classify(state)
        cross = {'B1', 'A2', 'C2', 'B3'}
        self.assertEqual({cell for cell, result in classified.items()
                          if result == 'INNOCENT'}, cross)
        self.assertTrue(all(result == 'UNKNOWN' for cell, result in classified.items()
                            if cell not in cross))
        parts = {part.key: part for part in clue_parts(self.custom, self.board, self.clues)}
        self.assertEqual(parts['result'].cells, cross)
        self.assertEqual(parts['region'].anchors, {'B2'})
        self.assertNotIn('B2', parts['result'].cells)

    def test_nested_custom_wording_retains_links_and_escapes_names(self):
        spec = {'type': 'CONDITIONAL',
                'if': {'type': 'FACT', 'person': 'A1', 'status': 'CRIMINAL'},
                'then': self.custom}
        names = {'A1': 'Ada', 'B2': '<Eli>'}
        self.assertEqual(clue_text(spec, self.board, self.clues, names),
                         'Nếu Ada là Tội phạm thì những người kề <Eli> đều vô tội.')
        html = clue_html(spec, self.board, self.clues, THEMES['pixel'], names)
        parts = {part.key for part in clue_parts(spec, self.board, self.clues)}
        links = set(re.findall(r'href="([^"]+)"', html))
        self.assertEqual(links, {'if.person', 'then.region', 'then.region.anchor.B2'})
        self.assertTrue(links <= parts)
        self.assertIn('&lt;Eli&gt;', html)
        self.assertNotIn('<Eli>', html)

    def test_custom_clue_composes_with_conditional_semantics_and_cnf(self):
        spec = {'type': 'CONDITIONAL',
                'if': {'type': 'FACT', 'person': 'A1', 'status': 'CRIMINAL'},
                'then': self.custom}
        encoder = Encoder(self.board)
        encoder.add(spec, self.clues)
        kb = encoder.finish()
        cells = ('A1', 'B1', 'A2', 'C2', 'B3')
        for values in itertools.product((False, True), repeat=len(cells)):
            assignment = dict.fromkeys(self.board.cells, False)
            assignment.update(zip(cells, values))
            assumptions = [value if assignment[cell] else -value
                           for cell, value in kb.primary.items()]
            expected = self.clues.evaluate(spec, assignment, self.board)
            self.assertEqual(solve(kb.clauses, kb.variable_count, assumptions).status == 'SAT',
                             expected, assignment)

    def test_reference_fields_are_validated_without_custom_validator(self):
        for region in (None, {'type': 'CROSS', 'cell': 'Z9'}):
            with self.subTest(region=region), self.assertRaises(PuzzleError):
                self.clues.validate({'type': 'ALL_INNOCENT', 'region': region}, self.board)
        spec = {'type': 'CONDITIONAL', 'if': self.custom,
                'then': {'type': 'FACT', 'person': 'Z9', 'status': 'CRIMINAL'}}
        with self.assertRaises(PuzzleError):
            self.clues.validate(spec, self.board)

    def test_local_registration_is_isolated_and_duplicate_names_fail(self):
        self.assertIsInstance(self.Cross(), Region)
        self.assertIsInstance(self.AllInnocent(), Clue)
        with self.assertRaises(PuzzleError):
            region_registry().resolve({'type': 'CROSS', 'cell': 'B2'}, self.board)
        with self.assertRaises(PuzzleError):
            clue_registry(region_registry()).validate(self.custom, self.board)
        for catalog, name, rule in ((self.regions, 'CROSS', self.Cross),
                                    (self.clues, 'ALL_INNOCENT', self.AllInnocent)):
            with self.assertRaises(ValueError):
                catalog.register(name, rule)
            with self.assertRaises(TypeError):
                catalog.register('INVALID', object())
            with self.assertRaises(ValueError):
                catalog.register('', rule)

    def test_default_decorators_populate_fresh_catalogs(self):
        from griductive.engine.regions import Row
        from griductive.engine.clues import Fact
        self.assertIsInstance(region_registry().handler({'type': 'ROW'}), Row)
        self.assertIsInstance(clue_registry(region_registry()).handler({'type': 'FACT'}), Fact)
